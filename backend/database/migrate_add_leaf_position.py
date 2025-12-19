"""
Database Migration: Add Leaf Position Test Tables
Creates weekly_leaf_position and weekly_leaf_position_results tables
"""

from .config import Base, engine
from .weekly_tests import LeafPositionTest, LeafPositionResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Create the Leaf Position test tables"""
    try:
        logger.info("Creating Leaf Position test tables...")
        
        # Create tables
        LeafPositionTest.__table__.create(engine, checkfirst=True)
        LeafPositionResult.__table__.create(engine, checkfirst=True)
        
        logger.info("✓ Successfully created weekly_leaf_position table")
        logger.info("✓ Successfully created weekly_leaf_position_results table")
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate()
