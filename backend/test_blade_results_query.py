import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.config import SessionLocal
from database.weekly_tests import LeafPositionTest, LeafPositionResult

db = SessionLocal()

# Get test
test = db.query(LeafPositionTest).filter(LeafPositionTest.id == 1).first()
print(f"Test found: {test is not None}")
print(f"Test ID: {test.id if test else 'N/A'}")

# Query blade results separately
blade_results = db.query(LeafPositionResult).filter(
    LeafPositionResult.test_id == 1
).all()

print(f"\nDirect query for blade_results with test_id=1:")
print(f"  Count: {len(blade_results)}")

if blade_results:
    print(f"  First blade: pair={blade_results[0].blade_pair}, field_size={blade_results[0].field_size_mm}")

# Also try using the relationship
if test:
    print(f"\nUsing relationship test.blade_results:")
    print(f"  Type: {type(test.blade_results)}")
    print(f"  Count: {len(test.blade_results)}")
    if test.blade_results:
        print(f"  First blade: pair={test.blade_results[0].blade_pair}")

db.close()
