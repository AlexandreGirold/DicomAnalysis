"""
Test Sessions Router
GET/DELETE endpoints for all test types
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import database as db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# SAFETY SYSTEMS (DAILY)
# ============================================================================

@router.get("/safety-systems-sessions")
async def get_safety_systems_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all Safety Systems test sessions"""
    try:
        tests = db.get_all_safety_systems_tests(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[SAFETY-SYSTEMS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-systems-sessions/{test_id}")
async def get_safety_systems_session(test_id: int):
    """Get a specific Safety Systems test session"""
    try:
        test = db.get_safety_systems_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/safety-systems-sessions/{test_id}")
async def delete_safety_systems_session(test_id: int):
    """Delete a Safety Systems test session"""
    try:
        success = db.delete_safety_systems_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return JSONResponse({'message': 'Test deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NIVEAU HELIUM (WEEKLY)
# ============================================================================

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


# ============================================================================
# POSITION TABLE (MONTHLY)
# ============================================================================

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
