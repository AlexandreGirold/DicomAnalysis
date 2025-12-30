from database import SessionLocal, LeafPositionTest, LeafPositionResult

session = SessionLocal()

try:
    # Get all leaf position tests
    all_tests = session.query(LeafPositionTest).all()
    
    print(f"Found {len(all_tests)} leaf position tests")
    
    if all_tests:
        print("\nDeleting all tests:")
        for test in all_tests:
            blade_count = session.query(LeafPositionResult).filter(
                LeafPositionResult.test_id == test.id
            ).count()
            print(f"  Test ID {test.id}: operator={test.operator}, date={test.test_date.strftime('%Y-%m-%d')}, blades={blade_count}")
        
        # Delete all blade results first
        total_blades = session.query(LeafPositionResult).count()
        session.query(LeafPositionResult).delete()
        print(f"\n✓ Deleted {total_blades} blade results")
        
        # Delete all tests
        session.query(LeafPositionTest).delete()
        print(f"✓ Deleted {len(all_tests)} tests")
        
        session.commit()
        print("\n✓ All leaf position data deleted successfully!")
    else:
        print("No tests found to delete.")
        
finally:
    session.close()
