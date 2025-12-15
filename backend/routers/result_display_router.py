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
    from result_displays.mlc_display import display_mlc_result
    from result_displays.mvic_display import display_mvic_result
    from result_displays.mvic_fente_v2_display import display_mvic_fente_v2_result
    from result_displays.niveau_helium_display import display_niveau_helium_result
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


# ========== MLC Leaf & Jaw Test Display ==========

@router.get("/display/mlc/{test_id}")
async def get_mlc_display(test_id: int):
    """Get formatted MLC test result for display"""
    try:
        logger.info(f"[DISPLAY-ROUTER] Retrieving MLC test {test_id}")
        result = display_mlc_result(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"MLC test {test_id} not found")
        
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error retrieving MLC test {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/display/mlc")
async def list_mlc_tests(limit: int = 10, offset: int = 0):
    """List available MLC tests"""
    try:
        import database as db
        tests = db.get_all_mlc_tests(limit=limit, offset=offset)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error listing MLC tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== MVIC-Champ Test Display ==========

@router.get("/display/mvic/{test_id}")
async def get_mvic_display(test_id: int):
    """Get formatted MVIC-Champ test result for display"""
    try:
        logger.info(f"[DISPLAY-ROUTER] Retrieving MVIC-Champ test {test_id}")
        result = display_mvic_result(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"MVIC-Champ test {test_id} not found")
        
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error retrieving MVIC-Champ test {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/display/mvic")
async def list_mvic_tests(limit: int = 10, offset: int = 0):
    """List available MVIC-Champ tests"""
    try:
        import database as db
        tests = db.get_all_mvic_tests(limit=limit, offset=offset)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error listing MVIC-Champ tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== MVIC Fente Test Display ==========

@router.get("/display/mvic-fente-v2/{test_id}")
async def get_mvic_fente_v2_display(test_id: int):
    """Get formatted MVIC Fente test result for display"""
    try:
        logger.info(f"[DISPLAY-ROUTER] Retrieving MVIC Fente test {test_id}")
        result = display_mvic_fente_v2_result(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"MVIC Fente test {test_id} not found")
        
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error retrieving MVIC Fente test {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/display/mvic-fente-v2")
async def list_mvic_fente_v2_tests(limit: int = 10, offset: int = 0):
    """List available MVIC Fente tests"""
    try:
        import database as db
        tests = db.get_all_mvic_fente_v2_tests(limit=limit, offset=offset)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error listing MVIC Fente tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Niveau Helium Test Display ==========

@router.get("/display/niveau-helium/{test_id}")
async def get_niveau_helium_display(test_id: int):
    """Get formatted Niveau Helium test result for display"""
    try:
        logger.info(f"[DISPLAY-ROUTER] Retrieving Niveau Helium test {test_id}")
        result = display_niveau_helium_result(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Niveau Helium test {test_id} not found")
        
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error retrieving Niveau Helium test {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/display/niveau-helium")
async def list_niveau_helium_tests(limit: int = 10, offset: int = 0):
    """List available Niveau Helium tests"""
    try:
        import database as db
        tests = db.get_all_niveau_helium_tests(limit=limit, offset=offset)
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[DISPLAY-ROUTER] Error listing Niveau Helium tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

