from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
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
import database
import database as db  # Keep legacy alias for compatibility
import database_helpers
import mv_center_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_field_name(field_name: str) -> str:
    """
    Convert field names from frontend format to database column format
    Examples:
        'D10 Moyenne' -> 'd10_moyenne'
        'Ratio D20/D10' -> 'ratio_d20_d10'
        'helium_level' -> 'helium_level' (unchanged)
    """
    import re
    # Remove special characters and replace spaces with underscores
    sanitized = re.sub(r'[^\w\s]', '', field_name)  # Remove special chars except letters, numbers, spaces
    sanitized = sanitized.replace(' ', '_')  # Replace spaces with underscores
    sanitized = sanitized.lower()  # Convert to lowercase
    return sanitized


def extract_extra_fields(data: dict, standard_fields: set) -> dict:
    """Extract test-specific fields from request data, excluding standard fields"""
    extra = {}
    for k, v in data.items():
        if k not in standard_fields and v is not None:
            # Sanitize field name for database compatibility
            sanitized_key = sanitize_field_name(k)
            extra[sanitized_key] = v
    return extra


def parse_test_date(date_str):
    """Helper function to parse test date from string or return current datetime"""
    if date_str:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    return datetime.now()

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

# Import routers
from routers.daily_tests import router as daily_router
from routers.weekly_tests import router as weekly_router
from routers.monthly_tests import router as monthly_router
from routers.mlc_routes import router as mlc_router
from routers.mvic_routes import router as mvic_router
from routers.test_execution import router as test_execution_router
from routers.result_display_router import router as result_display_router
from routers.config_routes import router as config_router

# Include routers by frequency
app.include_router(daily_router, tags=["Daily Tests"])
app.include_router(weekly_router, tags=["Weekly Tests"])
app.include_router(monthly_router, tags=["Monthly Tests"])
app.include_router(mlc_router, tags=["MLC Analysis"])
app.include_router(mvic_router, tags=["MVIC Analysis"])
app.include_router(test_execution_router, tags=["Test Execution"])
app.include_router(result_display_router, tags=["Result Display"])
app.include_router(config_router, tags=["Configuration"])
logger.info("Registered all routers (Daily/Weekly/Monthly + MLC/MVIC + Test Execution + Result Display + Config)")

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


@app.get("/config/mv-center")
async def get_mv_center_config():
    """Get MV isocenter (u, v) coordinates from database"""
    try:
        u, v = mv_center_utils.get_mv_center()
        logger.info(f"[CONFIG] Retrieved MV center: u={u}, v={v}")
        return {"u": u, "v": v}
    except Exception as e:
        logger.error(f"[CONFIG] Error getting MV center: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/mv-center")
async def update_mv_center_config(data: dict):
    """Update MV isocenter (u, v) coordinates in database"""
    try:
        u = float(data.get('u'))
        v = float(data.get('v'))
        
        success = mv_center_utils.update_mv_center(u, v)
        if success:
            logger.info(f"[CONFIG] Updated MV center: u={u}, v={v}")
            return {"success": True, "message": f"MV center updated to u={u}, v={v}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update MV center")
    except ValueError as e:
        logger.error(f"[CONFIG] Invalid values: {e}")
        raise HTTPException(status_code=400, detail="Invalid u or v values")
    except Exception as e:
        logger.error(f"[CONFIG] Error updating MV center: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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


# ===== PDF REPORT GENERATION ENDPOINTS =====

@app.get("/reports/test/{test_id}")
async def generate_test_report(test_id: int):
    """
    Generate PDF report for a single test
    """
    logger.info(f"[REPORT] Generating report for test {test_id}")
    try:
        from report_generator import generate_test_report
        
        pdf_data = generate_test_report(test_id)
        
        # Return PDF as downloadable file
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=test_report_{test_id}.pdf"
            }
        )
    except ValueError as e:
        logger.error(f"[REPORT] Test not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[REPORT] Error generating report: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/trend/{test_type}")
async def generate_trend_report_endpoint(
    test_type: str,
    start_date: str = None,
    end_date: str = None
):
    """
    Generate PDF trend report for a test type
    
    Query parameters:
        test_type: Test type identifier (e.g., "mlc_leaf_jaw")
        start_date: Start date (YYYY-MM-DD) - optional
        end_date: End date (YYYY-MM-DD) - optional
    """
    logger.info(f"[REPORT] Generating trend report for {test_type}")
    try:
        from report_generator import generate_trend_report
        
        pdf_data = generate_trend_report(test_type, start_date, end_date)
        
        # Return PDF as downloadable file
        filename = f"trend_report_{test_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        logger.error(f"[REPORT] Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[REPORT] Error generating trend report: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generic-tests")
async def get_generic_tests(
    test_type: str = None,
    limit: int = 100,
    offset: int = 0,
    start_date: str = None,
    end_date: str = None
):
    """
    Get all generic tests with optional filtering
    """
    logger.info(f"[GENERIC-TESTS] Getting tests (type={test_type}, limit={limit})")
    try:
        tests = db.get_all_generic_tests(
            test_type=test_type,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"[GENERIC-TESTS] Retrieved {len(tests)} tests")
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[GENERIC-TESTS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generic-tests/{test_id}")
async def get_generic_test(test_id: int):
    """
    Get a specific generic test by ID
    """
    logger.info(f"[GENERIC-TEST] Getting test ID: {test_id}")
    try:
        test = db.get_generic_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        logger.info(f"[GENERIC-TEST] Retrieved test: {test['test_name']}")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GENERIC-TEST] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/generic-tests/{test_id}")
async def delete_generic_test(test_id: int):
    """
    Delete a specific generic test
    """
    logger.info(f"[DELETE-GENERIC] Deleting test ID: {test_id}")
    try:
        success = db.delete_generic_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        logger.info(f"[DELETE-GENERIC] Successfully deleted test {test_id}")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE-GENERIC] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTE: MLC and MVIC endpoints moved to routers/mlc_routes.py and routers/mvic_routes.py
# Legacy endpoints below for backward compatibility - consider deprecating
# ============================================================================

@app.get("/mlc-trend/{parameter}")
async def get_mlc_trend(parameter: str, limit: int = 50):
    """
    Get trend data for a specific MLC parameter
    
    Parameters: center_u, center_v, jaw_x1_mm, jaw_x2_mm, 
                blade_top_average, blade_top_std_dev, 
                blade_bottom_average, blade_bottom_std_dev, 
                blade_average_angle
    """
    logger.info(f"[MLC-TREND] Getting trend for parameter: {parameter}")
    try:
        trend_data = db.get_mlc_trend_data(parameter, limit)
        logger.info(f"[MLC-TREND] Retrieved {len(trend_data)} data points")
        return JSONResponse({
            'parameter': parameter,
            'data': trend_data,
            'count': len(trend_data)
        })
    except Exception as e:
        logger.error(f"[MLC-TREND] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mlc-reports/trend")
async def generate_mlc_trend_report(start_date: str = None, end_date: str = None):
    """
    Generate PDF report for MLC test sessions with trend analysis
    """
    logger.info(f"[MLC-REPORT] Generating trend report from {start_date} to {end_date}")
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        from datetime import datetime
        
        # Get MLC test sessions
        tests = db.get_all_mlc_test_sessions(limit=1000, start_date=start_date, end_date=end_date)
        
        if not tests:
            raise HTTPException(status_code=404, detail="No MLC test sessions found for the given date range")
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("MLC Leaf and Jaw Test Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report info
        info_style = styles['Normal']
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"<b>Number of Tests:</b> {len(tests)}", info_style))
        if start_date:
            story.append(Paragraph(f"<b>Start Date:</b> {start_date}", info_style))
        if end_date:
            story.append(Paragraph(f"<b>End Date:</b> {end_date}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Create table data
        table_data = [['Test ID', 'Date', 'Operator', 'Center (U,V)', 'Jaw (X1,X2)', 'Top Blade Avg', 'Bottom Blade Avg', 'Angle', 'Result']]
        
        for test in tests:
            test_date = datetime.fromisoformat(test['test_date']).strftime('%Y-%m-%d')
            center = f"{test['test1_center']['center_u'] or '-'}, {test['test1_center']['center_v'] or '-'}"
            jaw = f"{test['test2_jaw']['jaw_x1_mm'] or '-'}, {test['test2_jaw']['jaw_x2_mm'] or '-'}"
            top_avg = str(test['test3_blade_top']['average'] or '-')
            bottom_avg = str(test['test4_blade_bottom']['average'] or '-')
            angle = str(test['test5_angle']['average_angle'] or '-')
            result = test['overall_result'] or 'N/A'
            
            table_data.append([
                str(test['id']),
                test_date,
                test['operator'][:10],  # Truncate operator name
                center[:15],  # Truncate
                jaw[:15],
                top_avg[:8],
                bottom_avg[:8],
                angle[:8],
                result
            ])
        
        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"[MLC-REPORT] Successfully generated report with {len(tests)} tests")
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=mlc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MLC-REPORT] Error generating report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===== MVIC TEST SESSION ENDPOINTS =====

@app.post("/mvic-test-sessions")
async def save_mvic_test_session(data: dict):
    """
    Save MVIC test session with all 5 images
    
    Expected data structure:
    {
        "test_date": "2025-11-26T10:30:00",  // ISO format or will use current date
        "operator": "Dr. Smith",
        "image1": {"width_mm": 150.2, "height_mm": 85.1, "avg_angle": 90.1, "angle_std_dev": 0.5},
        "image2": {"width_mm": 85.3, "height_mm": 85.2, "avg_angle": 89.9, "angle_std_dev": 0.6},
        "image3": {"width_mm": 50.1, "height_mm": 50.0, "avg_angle": 90.2, "angle_std_dev": 0.4},
        "image4": {"width_mm": 150.0, "height_mm": 85.0, "avg_angle": 90.0, "angle_std_dev": 0.5},
        "image5": {"width_mm": 85.0, "height_mm": 85.1, "avg_angle": 89.8, "angle_std_dev": 0.7},
        "notes": "Optional notes",
        "overall_result": "PASS"
    }
    """
    logger.info("[MVIC-SESSION] Saving MVIC test session")
    try:
        # Parse test date
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except:
                test_date = datetime.now()
        else:
            test_date = datetime.now()
        
        # Validate operator
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        # Extract image data
        image1 = data.get('image1', {})
        image2 = data.get('image2', {})
        image3 = data.get('image3', {})
        image4 = data.get('image4', {})
        image5 = data.get('image5', {})
        
        # Prepare results for database
        from database_helpers import save_mvic_to_database
        
        results = []
        for i in range(1, 6):
            img_data = data.get(f'image{i}', {})
            # Extract corner angles if provided, otherwise calculate avg
            avg_angle = img_data.get('avg_angle', 90.0)
            results.append({
                'top_left_angle': img_data.get('top_left_angle', avg_angle),
                'top_right_angle': img_data.get('top_right_angle', avg_angle),
                'bottom_left_angle': img_data.get('bottom_left_angle', avg_angle),
                'bottom_right_angle': img_data.get('bottom_right_angle', avg_angle),
                'height': img_data.get('height_mm', 0),
                'width': img_data.get('width_mm', 0)
            })
        
        # Save to database
        test_id = save_mvic_to_database(
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            results=results,
            notes=data.get('notes'),
            filenames=data.get('filenames')
        )
        
        logger.info(f"[MVIC-SESSION] Saved test session with ID: {test_id}")
        
        return JSONResponse({
            'success': True,
            'test_id': test_id,
            'message': 'MVIC test session saved successfully'
        })
        
    except ValueError as e:
        logger.error(f"[MVIC-SESSION] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[MVIC-SESSION] Error saving test: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mvic-test-sessions")
async def get_mvic_test_sessions(
    limit: int = 100,
    offset: int = 0,
    start_date: str = None,
    end_date: str = None
):
    """
    Get all MVIC test sessions with optional date filtering
    """
    logger.info(f"[MVIC-SESSIONS] Getting tests (limit={limit}, start_date={start_date}, end_date={end_date})")
    try:
        from database import SessionLocal, MVICTest, MVICResult
        db_session = SessionLocal()
        
        query = db_session.query(MVICTest).order_by(MVICTest.test_date.desc())
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(MVICTest.test_date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(MVICTest.test_date <= datetime.fromisoformat(end_date))
        
        # Apply pagination
        tests = query.offset(offset).limit(limit).all()
        
        # Convert to dict
        result_tests = []
        for test in tests:
            test_dict = {
                'id': test.id,
                'test_date': test.test_date.isoformat(),
                'operator': test.operator,
                'overall_result': test.overall_result,
                'notes': test.notes,
                'filenames': test.filenames
            }
            result_tests.append(test_dict)
        
        db_session.close()
        logger.info(f"[MVIC-SESSIONS] Retrieved {len(result_tests)} tests")
        return JSONResponse({'tests': result_tests, 'count': len(result_tests)})
    except Exception as e:
        logger.error(f"[MVIC-SESSIONS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mvic-test-sessions/{test_id}")
async def get_mvic_test_session(test_id: int):
    """
    Get a specific MVIC test session by ID
    """
    logger.info(f"[MVIC-SESSION] Getting test ID: {test_id}")
    try:
        from database import SessionLocal, MVICTest, MVICResult
        db_session = SessionLocal()
        
        test = db_session.query(MVICTest).filter(MVICTest.id == test_id).first()
        
        if not test:
            db_session.close()
            raise HTTPException(status_code=404, detail="Test session not found")
        
        # Get results
        results = db_session.query(MVICResult).filter(MVICResult.test_id == test_id).all()
        
        test_dict = {
            'id': test.id,
            'test_date': test.test_date.isoformat(),
            'operator': test.operator,
            'overall_result': test.overall_result,
            'notes': test.notes,
            'filenames': test.filenames,
            'results': [{
                'image_number': r.image_number,
                'filename': r.filename,
                'top_left_angle': r.top_left_angle,
                'top_right_angle': r.top_right_angle,
                'bottom_left_angle': r.bottom_left_angle,
                'bottom_right_angle': r.bottom_right_angle,
                'height': r.height,
                'width': r.width
            } for r in results]
        }
        
        db_session.close()
        logger.info(f"[MVIC-SESSION] Retrieved test session")
        return JSONResponse(test_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MVIC-SESSION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/mvic-test-sessions/{test_id}")
async def delete_mvic_test_session(test_id: int):
    """
    Delete a specific MVIC test session
    """
    logger.info(f"[MVIC-SESSION] Deleting test ID: {test_id}")
    try:
        from database import SessionLocal, MVICTest, MVICResult
        db_session = SessionLocal()
        
        test = db_session.query(MVICTest).filter(MVICTest.id == test_id).first()
        
        if not test:
            db_session.close()
            raise HTTPException(status_code=404, detail="Test session not found")
        
        # Delete results first (foreign key constraint)
        db_session.query(MVICResult).filter(MVICResult.test_id == test_id).delete()
        
        # Delete test
        db_session.delete(test)
        db_session.commit()
        db_session.close()
        
        logger.info(f"[MVIC-SESSION] Successfully deleted test {test_id}")
        return JSONResponse({'message': 'MVIC test session deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MVIC-SESSION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTE: POST endpoints for test types moved to frequency-based routers:
# - daily_tests.py: Safety Systems
# - weekly_tests.py: Niveau Helium, MVIC Fente V2, PIQT
# - monthly_tests.py: Position Table, Alignement Laser, Quasar, Indice Quality
# - mlc_routes.py: MLC Leaf and Jaw
# - mvic_routes.py: MVIC (handled separately below)
# ============================================================================

@app.get("/mvic-trend/{parameter}")
async def get_mvic_trend(parameter: str, limit: int = 50):
    """
    Get trend data for a specific MVIC parameter
    
    Parameters: image1_width_mm, image1_height_mm, image1_avg_angle, image1_angle_std_dev,
                (same pattern for image2_ through image5_)
    """
    logger.info(f"[MVIC-TREND] Getting trend for parameter: {parameter}")
    try:
        trend_data = db.get_mvic_trend_data(parameter, limit)
        logger.info(f"[MVIC-TREND] Retrieved {len(trend_data)} data points")
        return JSONResponse({
            'parameter': parameter,
            'data': trend_data,
            'count': len(trend_data)
        })
    except Exception as e:
        logger.error(f"[MVIC-TREND] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTE: Test execution endpoints moved to routers/test_execution.py
# ============================================================================
# ============================================================================
