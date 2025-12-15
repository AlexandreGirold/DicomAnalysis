"""
Configuration Router
API endpoints for application configuration management
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from mv_center_utils import get_mv_center, update_mv_center

logger = logging.getLogger(__name__)
router = APIRouter()


class MVCenterUpdate(BaseModel):
    """Model for MV center coordinate update"""
    u: float
    v: float


@router.get("/config/mv-center")
async def get_mv_center_config():
    """
    Get current MV center (u, v) coordinates
    """
    try:
        u, v = get_mv_center()
        return JSONResponse({
            'u': u,
            'v': v,
            'success': True
        })
    except Exception as e:
        logger.error(f"[CONFIG] Error getting MV center: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/mv-center")
async def update_mv_center_config(data: MVCenterUpdate):
    """
    Update MV center (u, v) coordinates
    
    Request body:
        {
            "u": float,  // U coordinate (horizontal) in pixels
            "v": float   // V coordinate (vertical) in pixels
        }
    """
    try:
        success = update_mv_center(data.u, data.v)
        
        if success:
            logger.info(f"[CONFIG] MV center updated: u={data.u}, v={data.v}")
            return JSONResponse({
                'success': True,
                'message': f'MV center updated to u={data.u}, v={data.v}',
                'u': data.u,
                'v': data.v
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to update MV center")
    
    except Exception as e:
        logger.error(f"[CONFIG] Error updating MV center: {e}")
        raise HTTPException(status_code=500, detail=str(e))
