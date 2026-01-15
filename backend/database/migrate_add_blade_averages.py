"""
Migration: Add blade_top_average and blade_bottom_average to LeafPositionTest table
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
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(weekly_leaf_position)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Existing columns: {columns}")
        
        # Add blade_top_average column if not exists
        if 'blade_top_average' not in columns:
            print("Adding blade_top_average column...")
            cursor.execute("""
                ALTER TABLE weekly_leaf_position 
                ADD COLUMN blade_top_average REAL
            """)
            print("✓ Added blade_top_average column")
        else:
            print("✓ blade_top_average column already exists")
        
        # Add blade_bottom_average column if not exists
        if 'blade_bottom_average' not in columns:
            print("Adding blade_bottom_average column...")
            cursor.execute("""
                ALTER TABLE weekly_leaf_position 
                ADD COLUMN blade_bottom_average REAL
            """)
            print("✓ Added blade_bottom_average column")
        else:
            print("✓ blade_bottom_average column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(weekly_leaf_position)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"\nUpdated columns: {columns}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add blade averages to LeafPositionTest")
    print("=" * 60)
    migrate()
