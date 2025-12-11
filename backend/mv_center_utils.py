"""
Centralized MV Center utilities
Provides easy access to MV isocenter (u,v) coordinates from database
"""
from database import SessionLocal, MVCenterConfig
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def get_mv_center() -> Tuple[float, float]:
    """
    Get MV center coordinates from database
    
    Returns:
        Tuple[float, float]: (u, v) center coordinates in pixels
        Default: (511.03, 652.75) if not configured
    """
    db = SessionLocal()
    try:
        config = db.query(MVCenterConfig).first()
        if config:
            logger.debug(f"MV center from DB: u={config.u}, v={config.v}")
            return config.u, config.v
        else:
            # Create default config if not exists
            logger.warning("No MV center config found, creating default (511.03, 652.75)")
            default_config = MVCenterConfig(u=511.03, v=652.75)
            db.add(default_config)
            db.commit()
            return default_config.u, default_config.v
    except Exception as e:
        logger.error(f"Error reading MV center config: {e}")
        return 511.03, 652.75  # Fallback
    finally:
        db.close()


def update_mv_center(u: float, v: float) -> bool:
    """
    Update MV center coordinates in database
    
    Args:
        u: U coordinate (horizontal) in pixels
        v: V coordinate (vertical) in pixels
    
    Returns:
        bool: True if successful
    """
    db = SessionLocal()
    try:
        config = db.query(MVCenterConfig).first()
        if config:
            config.u = u
            config.v = v
            logger.info(f"Updated MV center: u={u}, v={v}")
        else:
            config = MVCenterConfig(u=u, v=v)
            db.add(config)
            logger.info(f"Created MV center config: u={u}, v={v}")
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating MV center config: {e}")
        return False
    finally:
        db.close()
