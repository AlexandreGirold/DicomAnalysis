"""
Debug what's in test 5
"""
from database.config import SessionLocal
from database.weekly_tests import PIQTTest
import json

db = SessionLocal()
test = db.query(PIQTTest).filter(PIQTTest.id == 5).first()

if test:
    print("Test 5 found:")
    print(f"  ID: {test.id}")
    print(f"  Operator: {test.operator}")
    print(f"  Date: {test.test_date}")
    print(f"  Result: {test.overall_result}")
    print(f"  Notes: {test.notes}")
    print(f"  SNR: {test.snr_value}")
    print(f"  Uniformity: {test.uniformity_value}")
    print(f"  Ghosting: {test.ghosting_value}")
    print(f"  Results JSON: {test.results_json}")
    
    # Check all attributes
    print("\nAll attributes:")
    for attr in dir(test):
        if not attr.startswith('_') and not attr in ['metadata', 'registry']:
            value = getattr(test, attr, None)
            if not callable(value) and not hasattr(value, '__table__'):
                print(f"  {attr}: {value}")
else:
    print("Test 5 not found!")

db.close()
