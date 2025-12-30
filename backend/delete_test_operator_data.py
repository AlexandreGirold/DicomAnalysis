import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database import SessionLocal, LeafPositionTest, LeafPositionResult

# Find all tests by "Test Operator"
session = SessionLocal()

try:
    # Get all test IDs with operator "Test Operator"
    tests = session.query(LeafPositionTest).filter(
        LeafPositionTest.operator == "Test Operator"
    ).all()
    
    print(f"Found {len(tests)} tests by 'Test Operator':")
    
    for test in tests:
        # Count blade results for this test
        blade_count = session.query(LeafPositionResult).filter(
            LeafPositionResult.test_id == test.id
        ).count()
        
        print(f"  Test ID {test.id}: Date={test.test_date.strftime('%Y-%m-%d')}, Blades={blade_count}")
    
    # Confirm deletion
    if tests:
        print(f"\nDeleting {len(tests)} tests and their blade results...")
        
        for test in tests:
            # Delete blade results first
            session.query(LeafPositionResult).filter(
                LeafPositionResult.test_id == test.id
            ).delete()
            
            # Delete test
            session.delete(test)
        
        session.commit()
        print("✓ All test data deleted successfully!")
    else:
        print("\nNo tests found to delete.")
        
finally:
    session.close()
