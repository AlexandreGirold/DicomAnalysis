"""
Monthly Tests Router
Endpoints for monthly QC tests
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
# POSITION TABLE (MONTHLY)
# ============================================================================

@router.post("/position-table-sessions")
async def save_position_table_session(data: dict):
    """Save Position Table V2 test session"""
    logger.info("[POSITION-TABLE] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        standard_fields = {'test_date', 'operator', 'overall_result', 'notes', 'filenames'}
        extra_fields = extract_extra_fields(data, standard_fields)
        
        test_id = database_helpers.save_generic_test_to_database(
            test_class=db.PositionTableV2Test,
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            **extra_fields
        )
        
        logger.info(f"[POSITION-TABLE] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'Position Table test saved successfully'})
    except Exception as e:
        logger.error(f"[POSITION-TABLE] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position-table-sessions")
async def get_position_table_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all Position Table test sessions"""
    try:
        tests = db.get_all_position_table_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[POSITION-TABLE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position-table-sessions/{test_id}")
async def get_position_table_session(test_id: int):
    """Get a specific Position Table test session"""
    try:
        test = db.get_position_table_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/position-table-sessions/{test_id}")
async def delete_position_table_session(test_id: int):
    """Delete a Position Table test session"""
    try:
        success = db.delete_position_table_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ALIGNEMENT LASER (MONTHLY)
# ============================================================================

@router.post("/alignement-laser-sessions")
async def save_alignement_laser_session(data: dict):
    """Save Alignement Laser test session"""
    logger.info("[ALIGNEMENT-LASER] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        standard_fields = {'test_date', 'operator', 'overall_result', 'notes', 'filenames'}
        extra_fields = extract_extra_fields(data, standard_fields)
        
        test_id = database_helpers.save_generic_test_to_database(
            test_class=db.AlignementLaserTest,
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            **extra_fields
        )
        
        logger.info(f"[ALIGNEMENT-LASER] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'Alignement Laser test saved successfully'})
    except Exception as e:
        logger.error(f"[ALIGNEMENT-LASER] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alignement-laser-sessions")
async def get_alignement_laser_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all Alignement Laser test sessions"""
    try:
        tests = db.get_all_alignement_laser_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[ALIGNEMENT-LASER] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alignement-laser-sessions/{test_id}")
async def get_alignement_laser_session(test_id: int):
    """Get a specific Alignement Laser test session"""
    try:
        test = db.get_alignement_laser_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alignement-laser-sessions/{test_id}")
async def delete_alignement_laser_session(test_id: int):
    """Delete an Alignement Laser test session"""
    try:
        success = db.delete_alignement_laser_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUASAR (MONTHLY)
# ============================================================================

@router.post("/quasar-sessions")
async def save_quasar_session(data: dict):
    """Save Quasar test session"""
    logger.info("[QUASAR] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        standard_fields = {'test_date', 'operator', 'overall_result', 'notes', 'filenames'}
        extra_fields = extract_extra_fields(data, standard_fields)
        
        test_id = database_helpers.save_generic_test_to_database(
            test_class=db.QuasarTest,
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            **extra_fields
        )
        
        logger.info(f"[QUASAR] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'Quasar test saved successfully'})
    except Exception as e:
        logger.error(f"[QUASAR] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quasar-sessions")
async def get_quasar_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all Quasar test sessions"""
    try:
        tests = db.get_all_quasar_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[QUASAR] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quasar-sessions/{test_id}")
async def get_quasar_session(test_id: int):
    """Get a specific Quasar test session"""
    try:
        test = db.get_quasar_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/quasar-sessions/{test_id}")
async def delete_quasar_session(test_id: int):
    """Delete a Quasar test session"""
    try:
        success = db.delete_quasar_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INDICE QUALITY (MONTHLY)
# ============================================================================

@router.post("/indice-quality-sessions")
async def save_indice_quality_session(data: dict):
    """Save Indice Quality test session"""
    logger.info("[INDICE-QUALITY] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        standard_fields = {'test_date', 'operator', 'overall_result', 'notes', 'filenames'}
        extra_fields = extract_extra_fields(data, standard_fields)
        
        test_id = database_helpers.save_generic_test_to_database(
            test_class=db.IndiceQualityTest,
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            **extra_fields
        )
        
        logger.info(f"[INDICE-QUALITY] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'Indice Quality test saved successfully'})
    except Exception as e:
        logger.error(f"[INDICE-QUALITY] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indice-quality-sessions")
async def get_indice_quality_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all Indice Quality test sessions"""
    try:
        tests = db.get_all_indice_quality_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[INDICE-QUALITY] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indice-quality-sessions/{test_id}")
async def get_indice_quality_session(test_id: int):
    """Get a specific Indice Quality test session"""
    try:
        test = db.get_indice_quality_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/indice-quality-sessions/{test_id}")
async def delete_indice_quality_session(test_id: int):
    """Delete an Indice Quality test session"""
    try:
        success = db.delete_indice_quality_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
