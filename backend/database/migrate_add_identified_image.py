"""
Migration: Add identified_image_number to LeafPositionResult table
"""
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'qc_tests.db')
    
    print(f"Connecting to database: {db_path}")
    
    if not os.path.exists(db_path):
        print("Error: Database file not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check columns in weekly_leaf_position_results
        cursor.execute("PRAGMA table_info(weekly_leaf_position_results)")
        results_columns = [row[1] for row in cursor.fetchall()]
        print(f"Results table columns: {results_columns}")
        
        # Add identified_image_number column
        if 'identified_image_number' not in results_columns:
            print("\nAdding identified_image_number to results table...")
            cursor.execute("""
                ALTER TABLE weekly_leaf_position_results 
                ADD COLUMN identified_image_number INTEGER
            """)
            print("✓ Added identified_image_number column to results table")
        else:
            print("✓ identified_image_number already exists in results table")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify column was added
        cursor.execute("PRAGMA table_info(weekly_leaf_position_results)")
        results_columns = [row[1] for row in cursor.fetchall()]
        print(f"\nUpdated results table columns: {results_columns}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add identified_image_number to LeafPositionResult")
    print("=" * 60)
    migrate()
