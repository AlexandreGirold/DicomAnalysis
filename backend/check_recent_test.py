from database import SessionLocal, LeafPositionTest, LeafPositionResult
from database.queries import get_leaf_position_test_by_id

session = SessionLocal()

# Get the most recent test
tests = session.query(LeafPositionTest).order_by(LeafPositionTest.id.desc()).limit(3).all()

print(f"Most recent tests:")
for test in tests:
    blade_count = session.query(LeafPositionResult).filter(
        LeafPositionResult.test_id == test.id
    ).count()
    print(f"\nTest ID {test.id}:")
    print(f"  Operator: {test.operator}")
    print(f"  Date: {test.test_date}")
    print(f"  Overall Result: {test.overall_result}")
    print(f"  Blade Results Count: {blade_count}")
    
    # Get detailed data
    test_data = get_leaf_position_test_by_id(test.id)
    if test_data:
        print(f"  blade_results field: {len(test_data.get('blade_results', []))} items")
        if test_data.get('blade_results'):
            print(f"  First blade: {test_data['blade_results'][0]}")

session.close()
