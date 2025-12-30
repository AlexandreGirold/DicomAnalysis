import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.config import SessionLocal
from database.weekly_tests import LeafPositionTest

db = SessionLocal()

tests = db.query(LeafPositionTest).order_by(LeafPositionTest.id).all()

print("=== All Leaf Position Tests ===")
for test in tests:
    print(f"ID {test.id}: {test.operator} - {test.test_date} - Blades: {len(test.blade_results)}")

db.close()
