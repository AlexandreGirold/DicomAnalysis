import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.queries import get_leaf_position_test_by_id
import json

result = get_leaf_position_test_by_id(1)

print("=== Result from get_leaf_position_test_by_id(1) ===")
print(f"Type: {type(result)}")
print(f"Keys: {list(result.keys()) if result else 'None'}")
print(f"\nblade_results present: {'blade_results' in result if result else False}")
print(f"blade_results length: {len(result.get('blade_results', [])) if result else 0}")

if result and result.get('blade_results'):
    print(f"\nFirst blade result:")
    print(json.dumps(result['blade_results'][0], indent=2))
