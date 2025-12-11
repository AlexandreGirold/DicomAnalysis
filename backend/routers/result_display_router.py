"""
Result Display Router
Endpoints for retrieving and displaying saved test results
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Import display functions
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from result_displays.piqt_display import display_piqt_result
    logger.info("Successfully imported result display functions")
except ImportError as e:
    logger.error(f"Failed to import result display functions: {e}")


@router.get("/display/piqt/{test_id}")
async def get_piqt_display(test_id: int):
    """
    Get formatted PIQT test result for display
    
    Args:
        test_id: Database ID of the PIQT test
        
    Returns:
        JSON response with formatted test data including:
        - Test metadata (date, operator, result)
        - Summary values (SNR, uniformity, ghosting)
        - Detailed measurements organized by category
        - Results list matching original test output format
    """
    try:
        logger.info(f"[DISPLAY-ROUTER] Retrieving PIQT test {test_id}")
        result = display_piqt_result(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"PIQT test {test_id} not found")
        
        logger.info(f"[DISPLAY-ROUTER] Successfully retrieved PIQT test {test_id}")
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error retrieving PIQT test {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/display/piqt")
async def list_piqt_tests(limit: int = 10, offset: int = 0):
    """
    List available PIQT tests
    
    Args:
        limit: Maximum number of tests to return
        offset: Number of tests to skip
        
    Returns:
        JSON response with list of available tests
    """
    try:
        import database as db
        tests = db.get_all_piqt_tests(limit=limit, offset=offset)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error listing PIQT tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))
