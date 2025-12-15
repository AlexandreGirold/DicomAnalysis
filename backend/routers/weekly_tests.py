"""
Weekly Tests Router
Endpoints for weekly QC tests
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import database as db
import database_helpers
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def parse_test_date(date_str):
    """Helper function to parse test date from string or return current datetime"""
    if date_str:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    return datetime.now()


def extract_extra_fields(data: dict, standard_fields: set) -> dict:
    """Extract test-specific fields from request data, excluding standard fields"""
    extra = {}
    for k, v in data.items():
        if k not in standard_fields and v is not None:
            # Sanitize field name for database compatibility
            sanitized = re.sub(r'[^\w\s]', '', k)
            sanitized = sanitized.replace(' ', '_')
            sanitized = sanitized.lower()
            extra[sanitized] = v
    return extra


# ============================================================================
# NIVEAU HELIUM (WEEKLY)
# ============================================================================

@router.post("/niveau-helium-sessions")
async def save_niveau_helium_session(data: dict):
    """Save Niveau Helium test session"""
    logger.info("[NIVEAU-HELIUM] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        if 'helium_level' not in data:
            raise ValueError("helium_level is required")
        
        test_id = database_helpers.save_niveau_helium_to_database(
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            helium_level=float(data['helium_level']),
            notes=data.get('notes'),
            filenames=data.get('filenames', [])
        )
        
        logger.info(f"[NIVEAU-HELIUM] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'Niveau Helium test saved successfully'})
    except ValueError as e:
        logger.error(f"[NIVEAU-HELIUM] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[NIVEAU-HELIUM] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/niveau-helium-sessions")
async def get_niveau_helium_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all Niveau Helium test sessions"""
    try:
        tests = db.get_all_niveau_helium_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[NIVEAU-HELIUM] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/niveau-helium-sessions/{test_id}")
async def get_niveau_helium_session(test_id: int):
    """Get a specific Niveau Helium test session"""
    try:
        test = db.get_niveau_helium_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/niveau-helium-sessions/{test_id}")
async def delete_niveau_helium_session(test_id: int):
    """Delete a Niveau Helium test session"""
    try:
        success = db.delete_niveau_helium_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MVIC FENTE V2 (WEEKLY)
# ============================================================================

@router.post("/mvic-fente-v2-sessions")
async def save_mvic_fente_v2_session(data: dict):
    """Save MVIC Fente V2 test session (slit analysis)"""
    logger.info("[MVIC-FENTE-V2] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        # Save the test first to get an ID
        test_id = database_helpers.save_mvic_fente_v2_to_database(
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            results=data.get('results', []),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            file_results=data.get('file_results')  # Pass file_results
        )
        
        # Save visualizations if present
        visualizations = data.get('visualizations', [])
        if visualizations:
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
                from visualization_storage import save_multiple_visualizations
                
                saved_viz = save_multiple_visualizations(
                    visualizations=visualizations,
                    test_type='mvic_fente_v2',
                    test_id=test_id
                )
                
                # Update test with visualization paths
                if saved_viz:
                    viz_paths = [v.get('file_path') for v in saved_viz if v.get('file_path')]
                    database_helpers.update_visualization_paths(test_id, 'mvic_fente_v2', viz_paths)
                    logger.info(f"[MVIC-FENTE-V2] Saved {len(viz_paths)} visualizations")
            except Exception as viz_error:
                logger.error(f"[MVIC-FENTE-V2] Error saving visualizations: {viz_error}")
                # Continue even if visualization save fails
        
        logger.info(f"[MVIC-FENTE-V2] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'MVIC Fente V2 test saved successfully'})
    except ValueError as e:
        logger.error(f"[MVIC-FENTE-V2] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[MVIC-FENTE-V2] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mvic-fente-v2-sessions")
async def get_mvic_fente_v2_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all MVIC Fente V2 test sessions"""
    try:
        tests = db.get_all_mvic_fente_v2_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[MVIC-FENTE-V2] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mvic-fente-v2-sessions/{test_id}")
async def get_mvic_fente_v2_session(test_id: int):
    """Get a specific MVIC Fente V2 test session"""
    try:
        test = db.get_mvic_fente_v2_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mvic-fente-v2-sessions/{test_id}")
async def delete_mvic_fente_v2_session(test_id: int):
    """Delete a MVIC Fente V2 test session"""
    try:
        success = db.delete_mvic_fente_v2_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PIQT (WEEKLY)
# ============================================================================

@router.post("/piqt-sessions")
async def save_piqt_session(data: dict):
    """Save PIQT test session"""
    logger.info("[PIQT] Saving test session")
    logger.info(f"[PIQT] Received data keys: {list(data.keys())}")
    logger.info(f"[PIQT] Has 'results' key: {'results' in data}")
    if 'results' in data:
        logger.info(f"[PIQT] Results type: {type(data['results'])}, length: {len(data['results']) if isinstance(data['results'], (list, dict)) else 'N/A'}")
        if isinstance(data['results'], list) and len(data['results']) > 0:
            logger.info(f"[PIQT] First result sample: {data['results'][0]}")
    
    try:
        import json
        
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        # Extract standard fields
        standard_fields = {'test_date', 'operator', 'overall_result', 'notes', 'filenames', 'results'}
        extra_fields = extract_extra_fields(data, standard_fields)
        
        # Convert results to JSON if present
        if 'results' in data and data['results']:
            results_data = data['results']
            
            # Convert dict to array format if needed (BaseTest returns dict, not array)
            results_array = []
            if isinstance(results_data, dict):
                logger.info(f"[PIQT] Converting results dict with {len(results_data)} items to array")
                for result_name, result_info in results_data.items():
                    results_array.append({
                        'name': result_name,
                        'value': result_info.get('value'),
                        'status': result_info.get('status'),
                        'unit': result_info.get('unit', ''),
                        'tolerance': result_info.get('tolerance', 'N/A')
                    })
            elif isinstance(results_data, list):
                logger.info(f"[PIQT] Results already in array format with {len(results_data)} items")
                results_array = results_data
            
            if results_array:
                extra_fields['results_json'] = json.dumps(results_array)
                logger.info(f"[PIQT] Stored {len(results_array)} results in JSON")
        
        test_id = database_helpers.save_generic_test_to_database(
            test_class=db.PIQTTest,
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            **extra_fields
        )
        
        logger.info(f"[PIQT] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'PIQT test saved successfully'})
    except Exception as e:
        logger.error(f"[PIQT] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/piqt-sessions")
async def get_piqt_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all PIQT test sessions"""
    try:
        tests = db.get_all_piqt_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[PIQT] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/piqt-sessions/{test_id}")
async def get_piqt_session(test_id: int):
    """Get a specific PIQT test session"""
    try:
        test = db.get_piqt_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/piqt-sessions/{test_id}")
async def delete_piqt_session(test_id: int):
    """Delete a PIQT test session"""
    try:
        success = db.delete_piqt_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
