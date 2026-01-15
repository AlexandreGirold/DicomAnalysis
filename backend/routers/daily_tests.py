"""
Daily Tests Router
Endpoints for daily QC tests
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
# SAFETY SYSTEMS (DAILY)
# ============================================================================

@router.post("/safety-systems-sessions")
async def save_safety_systems_session(data: dict):
    """Save Safety Systems test session"""
    logger.info("[SAFETY-SYSTEMS] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        # Extract standard fields
        standard_fields = {'test_date', 'operator', 'overall_result', 'notes', 'filenames'}
        extra_fields = extract_extra_fields(data, standard_fields)
        
        test_id = database_helpers.save_generic_test_to_database(
            test_class=db.SafetySystemsTest,
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', []),
            **extra_fields
        )
        
        logger.info(f"[SAFETY-SYSTEMS] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'Safety Systems test saved successfully'})
    except Exception as e:
        logger.error(f"[SAFETY-SYSTEMS] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
