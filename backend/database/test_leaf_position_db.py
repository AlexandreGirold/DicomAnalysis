"""
Test script to verify Leaf Position database setup
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import (
    SessionLocal, 
    LeafPositionTest, 
    LeafPositionResult,
    get_all_leaf_position_tests
)
from datetime import datetime

def test_database_setup():
    """Test that tables were created and can be accessed"""
    print("Testing Leaf Position database setup...")
    
    db = SessionLocal()
    try:
        # Test 1: Check if tables exist by querying
        print("\n1. Testing table existence...")
        count = db.query(LeafPositionTest).count()
        print(f"   ✓ LeafPositionTest table exists (count: {count})")
        
        count = db.query(LeafPositionResult).count()
        print(f"   ✓ LeafPositionResult table exists (count: {count})")
        
        # Test 2: Check query functions
        print("\n2. Testing query functions...")
        tests = get_all_leaf_position_tests(limit=10)
        print(f"   ✓ get_all_leaf_position_tests() works (found {len(tests)} tests)")
        
        # Test 3: Check table structure
        print("\n3. Checking table columns...")
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        
        print("\n   LeafPositionTest columns:")
        for column in inspector.get_columns('weekly_leaf_position'):
            print(f"     - {column['name']}: {column['type']}")
        
        print("\n   LeafPositionResult columns:")
        for column in inspector.get_columns('weekly_leaf_position_results'):
            print(f"     - {column['name']}: {column['type']}")
        
        print("\n✅ All database setup tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
