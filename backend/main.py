from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import os
import shutil
from pathlib import Path
import sys
import traceback
import logging
import pydicom
from datetime import datetime
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

services_dir = os.path.join(os.path.dirname(__file__), 'services')
sys.path.insert(0, services_dir)
logger.info(f"Added services directory to path: {services_dir}")

try:
    from leaf_pos import MLCBladeAnalyzer
    logger.info("Successfully imported MLCBladeAnalyzer from leaf_pos")
except ImportError as e:
    logger.error(f"Failed to import MLCBladeAnalyzer: {e}")
    logger.error(traceback.format_exc())
    raise

# Import basic tests (depricated)
try:
    from basic_tests import (
        get_available_tests,
        create_test_instance,
        execute_test
    )
    logger.info("Successfully imported basic tests")
except ImportError as e:
    logger.error(f"Failed to import basic tests: {e}")
    logger.error(traceback.format_exc())

app = FastAPI(title="DICOM MLC Blade Analyzer")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files (frontend)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    logger.info(f"Mounted frontend directory: {FRONTEND_DIR}")


@app.get("/")
async def root():
    """Serve the main frontend page"""
    if FRONTEND_DIR.exists():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    logger.info("Root endpoint called - returning API info")
    return {"message": "DICOM MLC Blade Analyzer API", "version": "1.0", "status": "running"}

@app.post("/analyze-batch")
async def analyze_batch(files: List[UploadFile] = File(...)):
    """
    Upload and analyze multiple DICOM files using leaf_pos.py
    All files must be from the same day
    """
    logger.info(f"[ANALYZE-BATCH] Received {len(files)} files")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate all files are DICOM
    for file in files:
        if not file.filename.endswith('.dcm'):
            raise HTTPException(status_code=400, detail=f"Only DICOM (.dcm) files are supported: {file.filename}")
    
    temp_dir = None
    try:
        # Create temporary directory for this batch
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="mlc_analysis_"))
        logger.info(f"[ANALYZE-BATCH] Created temp directory: {temp_dir}")
        
        # Save all files
        saved_files = []
        for file in files:
            file_path = temp_dir / file.filename
            logger.info(f"[ANALYZE-BATCH] Saving file: {file.filename}")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append(file_path)
            logger.info(f"[ANALYZE-BATCH] Saved: {file.filename}, size: {os.path.getsize(file_path)} bytes")
        
        # Create analyzer instance
        logger.info("[ANALYZE-BATCH] Creating MLCBladeAnalyzer instance")
        analyzer = MLCBladeAnalyzer(testing_folder=str(temp_dir), gui_mode=False)
        
        # Run analysis (will process files in chronological order)
        logger.info(f"[ANALYZE-BATCH] Running analysis on {len(saved_files)} files")
        results = analyzer.run()
        
        if results is None or len(results) == 0:
            logger.error("[ANALYZE-BATCH] No results returned")
            raise HTTPException(status_code=500, detail="Failed to process DICOM images - no results returned")
        
        logger.info(f"[ANALYZE-BATCH] Processing complete, got {len(results)} blade results")
        
        # Group results by file (extract from visualization filenames)
        # Find all generated visualization files
        visualization_files = list(Path().glob("blade_detection_*.png"))
        logger.info(f"[ANALYZE-BATCH] Found {len(visualization_files)} visualization files")
        
        # Format results for JSON response
        formatted_results = []
        for r in results:
            formatted_results.append({
                'blade_pair': r[0],
                'distance_sup_mm': round(r[1], 3) if r[1] is not None else None,
                'distance_inf_mm': round(r[2], 3) if r[2] is not None else None,
                'field_size_mm': round(r[3], 3) if r[3] is not None else None,
                'status': r[4]
            })
        
        # Calculate summary statistics
        total_blades = len(formatted_results)
        closed_blades = sum(1 for r in formatted_results if r['status'] == 'CLOSED')
        out_of_tolerance = sum(1 for r in formatted_results if r['status'] and 'OUT_OF_TOLERANCE' in r['status'])
        ok_blades = sum(1 for r in formatted_results if r['status'] == 'OK')
        
        logger.info(f"[ANALYZE-BATCH] Summary - Total: {total_blades}, OK: {ok_blades}, Out of tolerance: {out_of_tolerance}, Closed: {closed_blades}")
        
        # Save to database (one test with all blades)
        # Get the file creation date from the first file
        first_file_date = None
        try:
            first_dcm = pydicom.dcmread(saved_files[0])
            first_file_date = analyzer.get_dicom_datetime(first_dcm)
            logger.info(f"[ANALYZE-BATCH] Test date: {first_file_date}")
        except Exception as e:
            logger.warning(f"[ANALYZE-BATCH] Could not extract date: {e}")
        
        try:
            summary_dict = {
                'total_blades': total_blades,
                'ok_blades': ok_blades,
                'out_of_tolerance': out_of_tolerance,
                'closed_blades': closed_blades
            }
            
            # Create a combined filename
            batch_filename = f"Batch_{len(files)}_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            test_id = db.save_analysis_result(
                filename=batch_filename,
                file_creation_date=first_file_date,
                results=formatted_results,
                summary=summary_dict,
                visualization=None  # Will update with visualization files
            )
            logger.info(f"[ANALYZE-BATCH] Saved to database with test_id: {test_id}")
            
            # Move visualization files to permanent location and associate with test
            viz_files = []
            for viz_file in visualization_files:
                new_name = f"test_{test_id}_{viz_file.name}"
                new_path = UPLOAD_DIR / new_name
                shutil.move(str(viz_file), str(new_path))
                viz_files.append(new_name)
                logger.info(f"[ANALYZE-BATCH] Moved visualization: {viz_file.name} -> {new_name}")
            
            # Update test record with visualization files
            if viz_files:
                db.update_test_visualizations(test_id, viz_files)
            
        except Exception as e:
            logger.error(f"[ANALYZE-BATCH] Failed to save to database: {e}")
            logger.error(traceback.format_exc())
        
        response_data = {
            'test_id': test_id,
            'files_processed': len(files),
            'results': formatted_results,
            'summary': {
                'total_blades': total_blades,
                'ok_blades': ok_blades,
                'out_of_tolerance': out_of_tolerance,
                'closed_blades': closed_blades
            },
            'visualizations': viz_files
        }
        
        logger.info(f"[ANALYZE-BATCH] Returning successful response")
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYZE-BATCH] Error processing files: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")
    finally:
        # Cleanup temp directory
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"[ANALYZE-BATCH] Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"[ANALYZE-BATCH] Could not clean up temp dir: {e}")
        
        # Close all file handles
        for file in files:
            try:
                file.file.close()
            except:
                pass


@app.post("/analyze")
async def analyze_dicom(file: UploadFile = File(...)):
    """
    Upload and analyze a DICOM file for MLC blade positions
    """
    logger.info(f"[ANALYZE] Received file: {file.filename} (content-type: {file.content_type})")
    
    if not file.filename.endswith('.dcm'):
        logger.warning(f"[ANALYZE] Rejected non-DICOM file: {file.filename}")
        raise HTTPException(status_code=400, detail="Only DICOM (.dcm) files are supported")
    
    file_path = None
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        logger.info(f"[ANALYZE] Saving file to: {file_path}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"[ANALYZE] File saved successfully, size: {os.path.getsize(file_path)} bytes")
        
        # Extract DICOM file creation date
        file_creation_date = None
        try:
            dcm = pydicom.dcmread(file_path)
            if hasattr(dcm, 'InstanceCreationDate') and hasattr(dcm, 'InstanceCreationTime'):
                date_str = dcm.InstanceCreationDate
                time_str = dcm.InstanceCreationTime if dcm.InstanceCreationTime else "000000"
                file_creation_date = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S.%f") if '.' in time_str else datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                logger.info(f"[ANALYZE] DICOM file creation date: {file_creation_date}")
            elif hasattr(dcm, 'InstanceCreationDate'):
                date_str = dcm.InstanceCreationDate
                file_creation_date = datetime.strptime(date_str, "%Y%m%d")
                logger.info(f"[ANALYZE] DICOM file creation date (date only): {file_creation_date}")
        except Exception as e:
            logger.warning(f"[ANALYZE] Could not extract file creation date: {e}")
        
        # Create analyzer instance
        logger.info("[ANALYZE] Creating MLCBladeAnalyzer instance")
        analyzer = MLCBladeAnalyzer(testing_folder=str(UPLOAD_DIR))
        
        # Process the image
        logger.info(f"[ANALYZE] Processing image: {file_path}")
        results = analyzer.process_image(str(file_path))
        
        if results is None:
            logger.error("[ANALYZE] Process returned None")
            raise HTTPException(status_code=500, detail="Failed to process DICOM image - no results returned")
        
        logger.info(f"[ANALYZE] Processing complete, got {len(results)} blade results")
        
        # Format results for JSON response
        formatted_results = []
        for r in results:
            formatted_results.append({
                'blade_pair': r[0],
                'distance_sup_mm': round(r[1], 3) if r[1] is not None else None,
                'distance_inf_mm': round(r[2], 3) if r[2] is not None else None,
                'field_size_mm': round(r[3], 3) if r[3] is not None else None,
                'status': r[4]
            })
        
        # Calculate summary statistics
        total_blades = len(formatted_results)
        closed_blades = sum(1 for r in formatted_results if r['status'] == 'CLOSED')
        out_of_tolerance = sum(1 for r in formatted_results if r['status'] and 'OUT_OF_TOLERANCE' in r['status'])
        ok_blades = sum(1 for r in formatted_results if r['status'] == 'OK')
        
        logger.info(f"[ANALYZE] Summary - Total: {total_blades}, OK: {ok_blades}, Out of tolerance: {out_of_tolerance}, Closed: {closed_blades}")
        
        # Find the generated visualization image
        visualization_file = f"blade_detection_{os.path.splitext(file.filename)[0]}.png"
        visualization_path = Path(visualization_file)
        
        visualization_exists = visualization_path.exists()
        logger.info(f"[ANALYZE] Visualization file: {visualization_file}, exists: {visualization_exists}")
        
        # Save to database
        try:
            summary_dict = {
                'total_blades': total_blades,
                'ok_blades': ok_blades,
                'out_of_tolerance': out_of_tolerance,
                'closed_blades': closed_blades
            }
            test_id = db.save_analysis_result(
                filename=file.filename,
                file_creation_date=file_creation_date,
                results=formatted_results,
                summary=summary_dict,
                visualization=visualization_file if visualization_exists else None
            )
            logger.info(f"[ANALYZE] Saved to database with test_id: {test_id}")
        except Exception as e:
            logger.error(f"[ANALYZE] Failed to save to database: {e}")
            # Continue anyway, don't fail the request
        
        response_data = {
            'filename': file.filename,
            'results': formatted_results,
            'summary': {
                'total_blades': total_blades,
                'ok_blades': ok_blades,
                'out_of_tolerance': out_of_tolerance,
                'closed_blades': closed_blades
            },
            'visualization': visualization_file if visualization_exists else None
        }
        
        logger.info(f"[ANALYZE] Returning successful response")
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYZE] Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}\n{traceback.format_exc()}")
    finally:
        # Close the file
        try:
            file.file.close()
            logger.info("[ANALYZE] File handle closed")
        except:
            pass

@app.get("/visualization/{filename}")
async def get_visualization(filename: str):
    """
    Retrieve the generated visualization image
    """
    logger.info(f"[VISUALIZATION] Requested file: {filename}")
    
    # Check in uploads directory first
    file_path = UPLOAD_DIR / filename
    logger.info(f"[VISUALIZATION] Looking for file at: {file_path.absolute()}")
    
    # Fallback to current directory if not in uploads
    if not file_path.exists():
        file_path = Path(filename)
        logger.info(f"[VISUALIZATION] Trying alternate location: {file_path.absolute()}")
    
    if not file_path.exists():
        logger.warning(f"[VISUALIZATION] File not found: {filename}")
        raise HTTPException(status_code=404, detail=f"Visualization not found: {filename}")
    
    logger.info(f"[VISUALIZATION] Returning file: {filename}")
    return FileResponse(file_path, media_type="image/png")


@app.get("/tests")
async def get_tests(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """
    Get list of all tests (sorted by file creation date, oldest first)
    Optional date range filtering
    """
    logger.info(f"[TESTS] Getting tests (limit={limit}, offset={offset}, start_date={start_date}, end_date={end_date})")
    try:
        tests = db.get_all_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        logger.info(f"[TESTS] Retrieved {len(tests)} tests")
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[TESTS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tests/{test_id}")
async def get_test(test_id: int):
    """
    Get a specific test with all blade results
    """
    logger.info(f"[TEST] Getting test ID: {test_id}")
    try:
        test = db.get_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        logger.info(f"[TEST] Retrieved test: {test['filename']}")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TEST] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/blade-trend/{blade_pair}")
async def get_blade_trend_data(blade_pair: str, limit: int = 50):
    """
    Get historical trend data for a specific blade pair
    """
    logger.info(f"[TREND] Getting trend for blade: {blade_pair} (limit={limit})")
    try:
        trend = db.get_blade_trend(blade_pair=blade_pair, limit=limit)
        logger.info(f"[TREND] Retrieved {len(trend)} data points")
        return JSONResponse({'blade_pair': blade_pair, 'data': trend, 'count': len(trend)})
    except Exception as e:
        logger.error(f"[TREND] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tests/{test_id}")
async def delete_test(test_id: int):
    """
    Delete a specific test
    """
    logger.info(f"[DELETE] Deleting test ID: {test_id}")
    try:
        success = db.delete_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        logger.info(f"[DELETE] Successfully deleted test {test_id}")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/database/stats")
async def get_db_stats():
    """
    Get database statistics
    """
    logger.info("[STATS] Getting database stats")
    try:
        stats = db.get_database_stats()
        logger.info(f"[STATS] Total tests: {stats['total_tests']}")
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"[STATS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== BASIC TESTS ENDPOINTS =====

@app.get("/basic-tests")
async def get_basic_tests():
    """
    Get list of available basic quality control tests
    """
    logger.info("[BASIC-TESTS] Getting available tests")
    try:
        tests = get_available_tests()
        return JSONResponse({
            'available_tests': tests,
            'count': len(tests)
        })
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error getting tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/basic-tests/{test_id}/form")
async def get_test_form(test_id: str):
    """
    Get form structure for a specific basic test
    """
    logger.info(f"[BASIC-TESTS] Getting form for test: {test_id}")
    try:
        test_instance = create_test_instance(test_id)
        form_data = test_instance.get_form_data()
        return JSONResponse(form_data)
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Test not found: {test_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error getting form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/niveau-helium")
async def execute_niveau_helium(data: dict):
    """
    Execute niveau d'hélium test
    Expected data: {"helium_level": float, "operator": str, "test_date": str (optional)}
    """
    logger.info("[BASIC-TESTS] Executing niveau hélium test")
    try:
        # Validate required fields
        if 'helium_level' not in data:
            raise HTTPException(status_code=400, detail="helium_level is required")
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'niveau_helium',
            helium_level=float(data['helium_level']),
            operator=data['operator'],
            test_date=test_date
        )
        
        logger.info(f"[BASIC-TESTS] Niveau hélium test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/position-table-v2")
async def execute_position_table_v2(data: dict):
    """
    Execute position table V2 test
    Expected data: {"position_175": float, "position_215": float, "operator": str, "test_date": str (optional)}
    """
    logger.info("[BASIC-TESTS] Executing position table V2 test")
    try:
        # Validate required fields
        required_fields = ['position_175', 'position_215', 'operator']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'position_table_v2',
            position_175=float(data['position_175']),
            position_215=float(data['position_215']),
            operator=data['operator'],
            test_date=test_date
        )
        
        logger.info(f"[BASIC-TESTS] Position table V2 test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/alignement-laser")
async def execute_alignement_laser(data: dict):
    """
    Execute alignement laser test
    Expected data: {"ecart_proximal": float, "ecart_central": float, "ecart_distal": float, "operator": str, "test_date": str (optional)}
    """
    logger.info("[BASIC-TESTS] Executing alignement laser test")
    try:
        # Validate required fields
        required_fields = ['ecart_proximal', 'ecart_central', 'ecart_distal', 'operator']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'alignement_laser',
            ecart_proximal=float(data['ecart_proximal']),
            ecart_central=float(data['ecart_central']),
            ecart_distal=float(data['ecart_distal']),
            operator=data['operator'],
            test_date=test_date
        )
        
        logger.info(f"[BASIC-TESTS] Alignement laser test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/quasar")
async def execute_quasar_test(data: dict):
    """
    Execute QUASAR test (Latence du gating et Précision)
    Expected data: {
        "operator": str,
        "latence_status": "PASS"/"FAIL"/"SKIP",
        "latence_reason": str (optional, required if SKIP),
        "coord_correction": float (optional),
        "x_value": float (optional),
        "y_value": float (optional),
        "z_value": float (optional),
        "test_date": str (optional),
        "notes": str (optional)
    }
    """
    logger.info("[BASIC-TESTS] Executing QUASAR test")
    try:
        # Validate required fields
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        if 'latence_status' not in data:
            raise HTTPException(status_code=400, detail="latence_status is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'quasar',
            operator=data['operator'],
            latence_status=data['latence_status'],
            latence_reason=data.get('latence_reason'),
            coord_correction=float(data['coord_correction']) if data.get('coord_correction') else None,
            x_value=float(data['x_value']) if data.get('x_value') else None,
            y_value=float(data['y_value']) if data.get('y_value') else None,
            z_value=float(data['z_value']) if data.get('z_value') else None,
            test_date=test_date,
            notes=data.get('notes')
        )
        
        logger.info(f"[BASIC-TESTS] QUASAR test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/indice-quality")
async def execute_indice_quality_test(data: dict):
    """
    Execute Indice de Qualité test (D10/D20 et D5/D15)
    Expected data: {
        "operator": str,
        "d10_m1": float, "d10_m2": float, "d10_m3": float,
        "d20_m1": float, "d20_m2": float, "d20_m3": float,
        "d5_m1": float (optional, default 0), "d5_m2": float (optional), "d5_m3": float (optional),
        "d15_m1": float (optional, default 0), "d15_m2": float (optional), "d15_m3": float (optional),
        "test_date": str (optional),
        "notes": str (optional)
    }
    """
    logger.info("[BASIC-TESTS] Executing Indice de Qualité test")
    try:
        # Validate required fields
        required_fields = ['operator', 'd10_m1', 'd10_m2', 'd10_m3', 'd20_m1', 'd20_m2', 'd20_m3']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'indice_quality',
            operator=data['operator'],
            d10_m1=float(data['d10_m1']),
            d10_m2=float(data['d10_m2']),
            d10_m3=float(data['d10_m3']),
            d20_m1=float(data['d20_m1']),
            d20_m2=float(data['d20_m2']),
            d20_m3=float(data['d20_m3']),
            d5_m1=float(data.get('d5_m1', 0)),
            d5_m2=float(data.get('d5_m2', 0)),
            d5_m3=float(data.get('d5_m3', 0)),
            d15_m1=float(data.get('d15_m1', 0)),
            d15_m2=float(data.get('d15_m2', 0)),
            d15_m3=float(data.get('d15_m3', 0)),
            test_date=test_date,
            notes=data.get('notes')
        )
        
        logger.info(f"[BASIC-TESTS] Indice de Qualité test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/piqt")
async def execute_piqt_test(request: Request):
    """
    Execute PIQT test (Philips Image Quality Test)
    Expects multipart form with:
        - operator: str
        - html_file: uploaded HTML file
        - test_date: str (optional)
        - notes: str (optional)
    """
    logger.info("[BASIC-TESTS] Executing PIQT test")
    
    try:
        # Parse form data
        form = await request.form()
        logger.info(f"[BASIC-TESTS] Form keys: {list(form.keys())}")
        
        # Debug: log all form data
        for key in form.keys():
            value = form[key]
            logger.info(f"[BASIC-TESTS] PIQT form field '{key}': type={type(value)}, hasattr(filename)={hasattr(value, 'filename')}")
            if hasattr(value, 'filename'):
                logger.info(f"[BASIC-TESTS]   -> filename: {value.filename}")
        
        # Extract operator
        operator = form.get("operator")
        if not operator:
            logger.error("[BASIC-TESTS] operator field is missing")
            raise HTTPException(status_code=400, detail="operator is required")
        
        logger.info(f"[BASIC-TESTS] Operator: {operator}")
        
        # Extract HTML file
        html_file = form.get("html_file")
        if not html_file or not hasattr(html_file, 'filename'):
            logger.error(f"[BASIC-TESTS] html_file is missing or invalid. html_file={html_file}, hasattr={hasattr(html_file, 'filename') if html_file else 'N/A'}")
            raise HTTPException(status_code=400, detail="html_file is required")
        
        if not html_file.filename.lower().endswith(('.html', '.htm')):
            raise HTTPException(status_code=400, detail=f"File {html_file.filename} is not an HTML file")
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, html_file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(html_file.file, buffer)
        
        logger.info(f"[BASIC-TESTS] Saved HTML file: {html_file.filename}")
        
        # Extract test date
        test_date = None
        test_date_str = form.get("test_date")
        if test_date_str:
            try:
                test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"[BASIC-TESTS] Invalid date format: {test_date_str}")
        
        # Execute test
        result = execute_test(
            'piqt',
            operator=operator,
            html_file_path=file_path,
            test_date=test_date,
            notes=form.get('notes')
        )
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        logger.info(f"[BASIC-TESTS] PIQT test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing PIQT test: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/safety-systems")
async def execute_safety_systems(data: dict):
    """
    Execute daily safety systems verification test
    Expected data: {
        "operator": str,
        "accelerator_warmup": "PASS"/"FAIL"/"SKIP",
        "audio_indicator": "PASS"/"FAIL"/"SKIP",
        "visual_indicators_console": "PASS"/"FAIL"/"SKIP",
        "visual_indicator_room": "PASS"/"FAIL"/"SKIP",
        "beam_interruption": "PASS"/"FAIL"/"SKIP",
        "door_interlocks": "PASS"/"FAIL"/"SKIP",
        "camera_monitoring": "PASS"/"FAIL"/"SKIP",
        "patient_communication": "PASS"/"FAIL"/"SKIP",
        "table_emergency_stop": "PASS"/"FAIL"/"SKIP",
        "test_date": str (optional),
        "notes": str (optional)
    }
    """
    logger.info("[BASIC-TESTS] Executing safety systems test")
    try:
        # Extract data
        operator = data.get('operator')
        accelerator_warmup = data.get('accelerator_warmup')
        audio_indicator = data.get('audio_indicator')
        visual_indicators_console = data.get('visual_indicators_console')
        visual_indicator_room = data.get('visual_indicator_room')
        beam_interruption = data.get('beam_interruption')
        door_interlocks = data.get('door_interlocks')
        camera_monitoring = data.get('camera_monitoring')
        patient_communication = data.get('patient_communication')
        table_emergency_stop = data.get('table_emergency_stop')
        
        test_date_str = data.get('test_date')
        notes = data.get('notes')
        
        # Validate required fields
        if not operator:
            raise ValueError("operator is required")
        
        required_checks = {
            'accelerator_warmup': accelerator_warmup,
            'audio_indicator': audio_indicator,
            'visual_indicators_console': visual_indicators_console,
            'visual_indicator_room': visual_indicator_room,
            'beam_interruption': beam_interruption,
            'door_interlocks': door_interlocks,
            'camera_monitoring': camera_monitoring,
            'patient_communication': patient_communication,
            'table_emergency_stop': table_emergency_stop
        }
        
        for field_name, field_value in required_checks.items():
            if not field_value:
                raise ValueError(f"{field_name} is required")
        
        # Parse date if provided
        test_date = None
        if test_date_str:
            from datetime import datetime
            test_date = datetime.fromisoformat(test_date_str)
        
        # Import and execute test
        from services.daily.safety_systems import SafetySystemsTest
        test = SafetySystemsTest()
        
        result = test.execute(
            operator=operator,
            accelerator_warmup=accelerator_warmup,
            audio_indicator=audio_indicator,
            visual_indicators_console=visual_indicators_console,
            visual_indicator_room=visual_indicator_room,
            beam_interruption=beam_interruption,
            door_interlocks=door_interlocks,
            camera_monitoring=camera_monitoring,
            patient_communication=patient_communication,
            table_emergency_stop=table_emergency_stop,
            test_date=test_date,
            notes=notes
        )
        
        logger.info(f"[BASIC-TESTS] Safety systems test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/mlc-leaf-jaw-debug")
async def debug_mlc_upload(request: Request):
    """
    Debug endpoint to see what's being sent
    """
    logger.info("[DEBUG] Raw request received")
    
    # Get form data
    form = await request.form()
    logger.info(f"[DEBUG] Form keys: {list(form.keys())}")
    
    for key in form.keys():
        value = form[key]
        logger.info(f"[DEBUG] {key}: {type(value)} = {value}")
    
    return {"received_keys": list(form.keys())}


@app.post("/basic-tests/mlc-leaf-jaw")
async def execute_mlc_leaf_jaw(
    request: Request
):
    """
    Execute MLC leaf and jaw test with DICOM file uploads
    """
    logger.info("[BASIC-TESTS] Executing MLC leaf and jaw test")
    
    file_paths = []  # Initialize at the start to avoid UnboundLocalError
    
    try:
        # Parse form data manually to handle flexible input
        form = await request.form()
        logger.info(f"[BASIC-TESTS] Form keys: {list(form.keys())}")
        
        # Debug: log all form data
        for key in form.keys():
            value = form[key]
            logger.info(f"[BASIC-TESTS] {key}: {type(value)} = {value}")
        
        # Extract operator - handle both single value and list
        operator_field = form.get("operator")
        if isinstance(operator_field, list):
            operator = operator_field[0] if operator_field else None
        else:
            operator = operator_field
            
        if not operator:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Extract test_date (optional) - handle both single value and list
        test_date_field = form.get("test_date") 
        if isinstance(test_date_field, list):
            test_date = test_date_field[0] if test_date_field else None
        else:
            test_date = test_date_field
        
        # Extract files - more robust approach
        dicom_files = []
        
        # Try to get files from different possible field names
        possible_file_fields = ['dicom_files', 'files']
        for field_name in possible_file_fields:
            try:
                # Try getlist first
                if hasattr(form, 'getlist'):
                    file_list = form.getlist(field_name)
                    for file_field in file_list:
                        if hasattr(file_field, 'filename') and file_field.filename:
                            dicom_files.append(file_field)
                
                # Also try direct access
                file_field = form.get(field_name)
                if file_field and hasattr(file_field, 'filename') and file_field.filename:
                    if file_field not in dicom_files:  # Avoid duplicates
                        dicom_files.append(file_field)
                        
            except Exception as e:
                logger.warning(f"[BASIC-TESTS] Error accessing field {field_name}: {e}")
                continue
        
        if not dicom_files:
            raise HTTPException(status_code=400, detail="At least one DICOM file is required")
        
        logger.info(f"[BASIC-TESTS] Operator: {operator}")
        logger.info(f"[BASIC-TESTS] Test date: {test_date}")
        logger.info(f"[BASIC-TESTS] Number of files: {len(dicom_files)}")
        
        # Create upload directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded files
        file_paths = []
        for file in dicom_files:
            if not file.filename.lower().endswith('.dcm'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a DICOM file (.dcm)")
            
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
        
        logger.info(f"[BASIC-TESTS] Saved {len(file_paths)} DICOM files")
        
        # Parse test date if provided
        parsed_test_date = None
        if test_date:
            try:
                parsed_test_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    parsed_test_date = datetime.strptime(test_date, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"[BASIC-TESTS] Invalid date format: {test_date}")
        
        # Create test instance and execute
        # Use the generic test execution function
        result = execute_test(
            'mlc_leaf_jaw',
            files=file_paths,
            operator=operator,
            test_date=parsed_test_date
        )
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.info(f"[BASIC-TESTS] MLC leaf and jaw test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except Exception as e:
        # Clean up files on error
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"[BASIC-TESTS] Error executing MLC test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/mvic")
async def execute_mvic(request: Request):
    """
    Execute MVIC (MV Imaging Check) test with 5 DICOM files upload
    Validates field size and shape with automatic detection
    """
    logger.info("[BASIC-TESTS] Executing MVIC test")
    
    file_paths = []
    
    try:
        # Log request details
        logger.info(f"[BASIC-TESTS] Request method: {request.method}")
        logger.info(f"[BASIC-TESTS] Request headers: {dict(request.headers)}")
        logger.info(f"[BASIC-TESTS] Content-Type: {request.headers.get('content-type')}")
        
        # Parse form data manually to handle flexible input
        form = await request.form()
        logger.info(f"[BASIC-TESTS] Form keys: {list(form.keys())}")
        
        # Debug: log all form data
        for key in form.keys():
            value = form[key]
            logger.info(f"[BASIC-TESTS] {key}: {type(value)} = {value if not hasattr(value, 'filename') else f'File: {value.filename}'}")
        
        # Extract operator - handle both single value and list
        operator_field = form.get("operator")
        if isinstance(operator_field, list):
            operator = operator_field[0] if operator_field else None
        else:
            operator = operator_field
            
        if not operator:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Extract test_date (optional) - handle both single value and list
        test_date_field = form.get("test_date") 
        if isinstance(test_date_field, list):
            test_date = test_date_field[0] if test_date_field else None
        else:
            test_date = test_date_field
        
        # Extract notes (optional) - handle both single value and list
        notes_field = form.get("notes")
        if isinstance(notes_field, list):
            notes = notes_field[0] if notes_field else None
        else:
            notes = notes_field
        
        # Extract files - more robust approach
        dicom_files = []
        
        # Try to get files from different possible field names
        possible_file_fields = ['dicom_files', 'files']
        for field_name in possible_file_fields:
            try:
                # Try getlist first
                if hasattr(form, 'getlist'):
                    file_list = form.getlist(field_name)
                    for file_field in file_list:
                        if hasattr(file_field, 'filename') and file_field.filename:
                            dicom_files.append(file_field)
                
                # Also try direct access
                file_field = form.get(field_name)
                if file_field and hasattr(file_field, 'filename') and file_field.filename:
                    if file_field not in dicom_files:  # Avoid duplicates
                        dicom_files.append(file_field)
                        
            except Exception as e:
                logger.warning(f"[BASIC-TESTS] Error accessing field {field_name}: {e}")
                continue
        
        if not dicom_files:
            raise HTTPException(status_code=400, detail="5 DICOM files are required")
        
        if len(dicom_files) != 5:
            raise HTTPException(status_code=400, detail=f"Exactly 5 DICOM files required, got {len(dicom_files)}")
        
        logger.info(f"[BASIC-TESTS] Operator: {operator}")
        logger.info(f"[BASIC-TESTS] Test date: {test_date}")
        logger.info(f"[BASIC-TESTS] Number of files: {len(dicom_files)}")
        
        # Create upload directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save all uploaded files
        file_paths = []
        for i, file in enumerate(dicom_files, 1):
            if not file.filename.lower().endswith('.dcm'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be a DICOM file (.dcm)")
            
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_paths.append(file_path)
            logger.info(f"[BASIC-TESTS] Saved file {i}: {file.filename}")
        
        logger.info(f"[BASIC-TESTS] Saved {len(file_paths)} DICOM files")
        
        # Parse test date if provided
        parsed_test_date = None
        if test_date:
            try:
                parsed_test_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    parsed_test_date = datetime.strptime(test_date, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"[BASIC-TESTS] Invalid date format: {test_date}")
        
        # Execute test
        from services.weekly.MVIC import MVICTest
        test = MVICTest()
        result = test.execute(
            files=file_paths,
            operator=operator,
            test_date=parsed_test_date,
            notes=notes
        )
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.info(f"[BASIC-TESTS] MVIC test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except Exception as e:
        # Clean up files on error
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"[BASIC-TESTS] Error executing MVIC test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/basic-tests/{test_id}")
async def execute_basic_test_generic(test_id: str, data: dict):
    """
    Execute any basic test by ID with generic data
    This is a flexible endpoint for frontend integration
    """
    logger.info(f"[BASIC-TESTS] Executing test: {test_id}")
    try:
        # Validate operator is provided
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Prepare parameters
        params = dict(data)
        if test_date:
            params['test_date'] = test_date
        
        # Execute test
        result = execute_test(test_id, **params)
        
        logger.info(f"[BASIC-TESTS] Test {test_id} result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        if "not found" in str(e):
            logger.warning(f"[BASIC-TESTS] Test not found: {test_id}")
            raise HTTPException(status_code=404, detail=str(e))
        else:
            logger.warning(f"[BASIC-TESTS] Invalid data: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[BASIC-TESTS] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))