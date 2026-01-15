"""
Migration: Create weekly_leaf_position_images table and populate from existing data
"""
import sqlite3
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

DB_PATH = backend_path / "data" / "qc_tests.db"


def migrate():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create new table
        print("\n1. Creating weekly_leaf_position_images table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_leaf_position_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                image_number INTEGER NOT NULL,
                identified_image_number INTEGER,
                filename TEXT,
                top_average REAL,
                bottom_average REAL,
                FOREIGN KEY (test_id) REFERENCES weekly_leaf_position (id)
            )
        """)
        print("✓ Table created")
        
        # Populate from existing blade results
        # For each test and image_number, calculate averages from blade results
        print("\n2. Populating from existing blade results...")
        cursor.execute("""
            INSERT INTO weekly_leaf_position_images 
                (test_id, image_number, identified_image_number, top_average, bottom_average)
            SELECT 
                test_id,
                image_number,
                identified_image_number,
                AVG(distance_sup_mm) as top_average,
                AVG(distance_inf_mm) as bottom_average
            FROM weekly_leaf_position_results
            GROUP BY test_id, image_number
            ORDER BY test_id, image_number
        """)
        rows_inserted = cursor.rowcount
        print(f"✓ Inserted {rows_inserted} image records")
        
        # Show sample data
        print("\n3. Sample data from new table:")
        cursor.execute("""
            SELECT test_id, image_number, top_average, bottom_average
            FROM weekly_leaf_position_images
            ORDER BY test_id, image_number
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  Test {row[0]}, Image {row[1]}: Top={row[2]:.2f}mm, Bottom={row[3]:.2f}mm")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
