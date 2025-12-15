"""
Database Migration: Add visualization_paths column
Adds visualization_paths TEXT column to MLC, MVIC, and MVIC Fente V2 tables
"""
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_add_visualization_paths():
    """Add visualization_paths column to test tables"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'qc_tests.db')
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables_to_update = [
            'weekly_mlc_leaf_jaw',
            'weekly_mvic',
            'weekly_mvic_fente_v2'
        ]
        
        for table in tables_to_update:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                logger.warning(f"Table {table} does not exist, skipping")
                continue
            
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'visualization_paths' in columns:
                logger.info(f"Column visualization_paths already exists in {table}")
                continue
            
            # Add column
            logger.info(f"Adding visualization_paths column to {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN visualization_paths TEXT")
            logger.info(f"✓ Added visualization_paths to {table}")
        
        # Also add file_results to mvic_fente_v2 if it doesn't exist
        cursor.execute("PRAGMA table_info(weekly_mvic_fente_v2)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'file_results' not in columns:
            logger.info("Adding file_results column to weekly_mvic_fente_v2")
            cursor.execute("ALTER TABLE weekly_mvic_fente_v2 ADD COLUMN file_results TEXT")
            logger.info("✓ Added file_results to weekly_mvic_fente_v2")
        
        conn.commit()
        conn.close()
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting database migration: add visualization_paths column")
    success = migrate_add_visualization_paths()
    if success:
        logger.info("✓ Migration successful!")
    else:
        logger.error("✗ Migration failed!")
