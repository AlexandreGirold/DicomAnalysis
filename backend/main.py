from fastapi import FastAPI, File, UploadFile, HTTPException
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add services directory to path
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