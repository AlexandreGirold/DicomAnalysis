import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.config import SessionLocal
from database.weekly_tests import LeafPositionTest
import json

db = SessionLocal()

# Get the most recent test
latest_test = db.query(LeafPositionTest).order_by(LeafPositionTest.id.desc()).first()

if not latest_test:
    print("No tests found in database")
    exit(1)

print(f"=== Latest Test (ID {latest_test.id}) ===")
print(f"Operator: {latest_test.operator}")
print(f"Date: {latest_test.test_date}")
print(f"Overall Result: {latest_test.overall_result}")
print(f"Filenames: {latest_test.filenames}")
print(f"\n=== Blade Results ===")
print(f"Number of blade_results: {len(latest_test.blade_results)}")

if latest_test.blade_results:
    print("\nFirst 5 blade results:")
    for br in latest_test.blade_results[:5]:
        print(f"  Blade {br.blade_pair}: field_size={br.field_size_mm}mm, is_valid={br.is_valid}")
    print(f"... total {len(latest_test.blade_results)} blades")
else:
    print("❌ NO BLADE RESULTS - The bug is still there!")
    print("\nChecking file_results to see if test was executed:")
    if latest_test.file_results:
        file_results = json.loads(latest_test.file_results)
        print(json.dumps(file_results, indent=2))

db.close()
