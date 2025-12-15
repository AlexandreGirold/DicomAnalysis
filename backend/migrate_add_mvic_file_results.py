"""
Migration script to add file_results column to MVICTest table
Run this once to update the database schema
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "data" / "qc_tests.db"

def migrate():
    """Add file_results column to weekly_mvic table"""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(weekly_mvic)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'file_results' in columns:
            print("✓ file_results column already exists in weekly_mvic table")
        else:
            print("Adding file_results column to weekly_mvic table...")
            cursor.execute("""
                ALTER TABLE weekly_mvic 
                ADD COLUMN file_results TEXT
            """)
            conn.commit()
            print("✓ Successfully added file_results column to weekly_mvic table")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MVIC Test Database Migration - Add file_results Column")
    print("=" * 60)
    migrate()
    print("\n✓ Migration complete!")
