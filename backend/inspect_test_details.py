import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.queries import get_leaf_position_test_by_id
import json

# Get test ID 1
test = get_leaf_position_test_by_id(1)

if not test:
    print("Test ID 1 not found")
    exit(1)

print("=== Test ID 1 Details ===")
print(f"Test type: {type(test)}")
print(f"Test keys: {list(test.keys()) if isinstance(test, dict) else 'N/A'}")

# Handle both dict and object
if isinstance(test, dict):
    operator = test.get('operator')
    test_date = test.get('test_date')
    overall_result = test.get('overall_result')
    filenames = test.get('filenames')
    blade_results = test.get('blade_results', [])
    file_results = test.get('file_results')
    notes = test.get('notes')
else:
    operator = test.operator
    test_date = test.test_date
    overall_result = test.overall_result
    filenames = test.filenames
    blade_results = test.blade_results
    file_results = test.file_results
    notes = test.notes

print(f"Operator: {operator}")
print(f"Date: {test_date}")
print(f"Overall Result: {overall_result}")
print(f"Filenames: {filenames}")
print(f"\n=== Blade Results ===")
print(f"Number of blade_results records: {len(blade_results)}")

if blade_results:
    print("\nFirst 5 blade results:")
    for br in blade_results[:5]:
        if isinstance(br, dict):
            pair = br.get('blade_pair')
            field_size = br.get('field_size_mm')
            is_valid = br.get('is_valid')
        else:
            pair = br.blade_pair
            field_size = br.field_size_mm
            is_valid = br.is_valid
        print(f"  Blade {pair}: field_size={field_size}mm, is_valid={is_valid}")
else:
    print("NO BLADE RESULTS FOUND!")

print(f"\n=== File Results (JSON) ===")
if file_results:
    if isinstance(file_results, str):
        file_results_data = json.loads(file_results)
    else:
        file_results_data = file_results
    print(json.dumps(file_results_data, indent=2))
else:
    print("No file_results")

print(f"\n=== Notes ===")
print(notes or "No notes")
