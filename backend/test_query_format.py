import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.queries import get_leaf_position_test_by_id
import json

# Get test ID 1
test = get_leaf_position_test_by_id(1)

if not test:
    print("Test not found")
    exit(1)

print("=== Test Data Structure ===")
print(f"Keys: {list(test.keys())}")
print(f"\nblade_results present: {'blade_results' in test}")
print(f"blade_results type: {type(test.get('blade_results'))}")
print(f"blade_results length: {len(test.get('blade_results', []))}")

if test.get('blade_results'):
    print(f"\nFirst blade result:")
    print(json.dumps(test['blade_results'][0], indent=2))
    
    print(f"\nBlade pairs in results:")
    blade_pairs = [br.get('blade_pair') for br in test['blade_results']]
    print(f"  Unique blade_pair values: {sorted(set(blade_pairs))}")
    print(f"  Count: {len(blade_pairs)}")
    
    # Check field sizes
    field_sizes = [br.get('field_size_mm') for br in test['blade_results'] if br.get('field_size_mm')]
    print(f"\n  Field sizes: min={min(field_sizes):.2f}, max={max(field_sizes):.2f}")
    
    # Check is_valid status
    statuses = [br.get('is_valid') for br in test['blade_results']]
    print(f"  Statuses: {set(statuses)}")
