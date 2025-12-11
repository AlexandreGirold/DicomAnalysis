"""
Database Migration Script
Adds 'filenames' column to all test tables and creates new MVIC Fente V2 tables

Run this script once to update your existing database:
    python migrate_database.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "qc_tests.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    
    # Add filenames column to existing tables
    tables_to_update = [
        'daily_safety_systems',
        'weekly_niveau_helium',
        'weekly_mlc_leaf_jaw',
        'weekly_mvic',
        'weekly_piqt',
        'monthly_position_table_v2',
        'monthly_alignement_laser',
        'monthly_quasar',
        'monthly_indice_quality'
    ]
    
    for table in tables_to_update:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN filenames TEXT")
            print(f"✓ Added 'filenames' column to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  - Column already exists in {table}")
            else:
                print(f"✗ Error updating {table}: {e}")
    
    # Recreate weekly_mvic_results with all columns
    try:
        # Check if table needs restructuring
        cursor.execute("PRAGMA table_info(weekly_mvic_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'image_number' not in columns:
            print("Recreating weekly_mvic_results with new schema...")
            
            # Create new table with correct structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weekly_mvic_results_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id INTEGER NOT NULL,
                    image_number INTEGER NOT NULL,
                    filename TEXT,
                    top_left_angle REAL NOT NULL,
                    top_right_angle REAL NOT NULL,
                    bottom_left_angle REAL NOT NULL,
                    bottom_right_angle REAL NOT NULL,
                    height REAL NOT NULL,
                    width REAL NOT NULL,
                    FOREIGN KEY (test_id) REFERENCES weekly_mvic(id)
                )
            """)
            
            # Copy existing data if any
            cursor.execute("SELECT COUNT(*) FROM weekly_mvic_results")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"  Warning: Found {count} existing records - they will be lost")
                print("  Please export data manually if needed before proceeding")
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE IF EXISTS weekly_mvic_results")
            cursor.execute("ALTER TABLE weekly_mvic_results_new RENAME TO weekly_mvic_results")
            print("✓ Recreated weekly_mvic_results with new schema")
        else:
            print("  - weekly_mvic_results already has correct schema")
            
    except sqlite3.Error as e:
        print(f"✗ Error updating weekly_mvic_results: {e}")
    
    # Create new MVIC Fente V2 tables
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_mvic_fente_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_date DATETIME NOT NULL,
                operator TEXT NOT NULL,
                upload_date DATETIME NOT NULL,
                overall_result TEXT NOT NULL,
                notes TEXT,
                filenames TEXT
            )
        """)
        print("✓ Created weekly_mvic_fente_v2 table")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mvic_fente_v2_date ON weekly_mvic_fente_v2(test_date)")
        
    except sqlite3.Error as e:
        print(f"✗ Error creating weekly_mvic_fente_v2: {e}")
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_mvic_fente_v2_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                image_number INTEGER NOT NULL,
                filename TEXT,
                slit_number INTEGER NOT NULL,
                width_mm REAL NOT NULL,
                height_pixels REAL NOT NULL,
                center_u REAL,
                center_v REAL,
                FOREIGN KEY (test_id) REFERENCES weekly_mvic_fente_v2(id)
            )
        """)
        print("✓ Created weekly_mvic_fente_v2_results table")
        
    except sqlite3.Error as e:
        print(f"✗ Error creating weekly_mvic_fente_v2_results: {e}")
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Save MVIC tests with filenames")
    print("  2. Save MVIC Fente V2 slit analysis")
    print("  3. Track source files for all tests")

if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"✗ Database not found at: {DB_PATH}")
        print("  The database will be created automatically on first use.")
    else:
        print(f"Migrating database at: {DB_PATH}")
        migrate()
