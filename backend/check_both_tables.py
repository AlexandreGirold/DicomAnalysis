import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.config import SessionLocal
from database.weekly_tests import MLCLeafJawTest, LeafPositionTest

db = SessionLocal()

# Check MLCLeafJawTest
mlc_test = db.query(MLCLeafJawTest).filter(MLCLeafJawTest.id == 1).first()
print(f"MLCLeafJawTest ID 1 exists: {mlc_test is not None}")
if mlc_test:
    print(f"  Operator: {mlc_test.operator}")
    print(f"  Date: {mlc_test.test_date}")

# Check LeafPositionTest
leaf_test = db.query(LeafPositionTest).filter(LeafPositionTest.id == 1).first()
print(f"\nLeafPositionTest ID 1 exists: {leaf_test is not None}")
if leaf_test:
    print(f"  Operator: {leaf_test.operator}")
    print(f"  Date: {leaf_test.test_date}")
    print(f"  Blade results: {len(leaf_test.blade_results)}")

db.close()
