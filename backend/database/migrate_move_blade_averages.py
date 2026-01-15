"""
Migration: Move blade averages from LeafPositionTest to LeafPositionResult table
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
        # Check columns in weekly_leaf_position
        cursor.execute("PRAGMA table_info(weekly_leaf_position)")
        main_columns = [row[1] for row in cursor.fetchall()]
        print(f"Main table columns: {main_columns}")
        
        # Check columns in weekly_leaf_position_results
        cursor.execute("PRAGMA table_info(weekly_leaf_position_results)")
        results_columns = [row[1] for row in cursor.fetchall()]
        print(f"Results table columns: {results_columns}")
        
        # Remove columns from main table if they exist
        if 'blade_top_average' in main_columns or 'blade_bottom_average' in main_columns:
            print("\n⚠️  Cannot drop columns in SQLite, they will remain but won't be used")
            print("The new columns in results table will be used instead")
        
        # Add columns to results table
        if 'blade_top_average' not in results_columns:
            print("\nAdding blade_top_average to results table...")
            cursor.execute("""
                ALTER TABLE weekly_leaf_position_results 
                ADD COLUMN blade_top_average REAL
            """)
            print("✓ Added blade_top_average column to results table")
        else:
            print("✓ blade_top_average already exists in results table")
        
        if 'blade_bottom_average' not in results_columns:
            print("Adding blade_bottom_average to results table...")
            cursor.execute("""
                ALTER TABLE weekly_leaf_position_results 
                ADD COLUMN blade_bottom_average REAL
            """)
            print("✓ Added blade_bottom_average column to results table")
        else:
            print("✓ blade_bottom_average already exists in results table")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify columns were added
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
    print("Migration: Move blade averages to LeafPositionResult")
    print("=" * 60)
    migrate()
