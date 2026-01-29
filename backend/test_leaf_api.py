"""Test script to check if Exactitude du MLC (leaf position) API query works"""
import sys
sys.path.insert(0, '.')

from database.queries import get_all_leaf_position_tests
import json

print("Testing get_all_leaf_position_tests()...")
tests = get_all_leaf_position_tests(limit=100)
print(f"Found {len(tests)} tests")

for test in tests:
    print(f"\nTest ID: {test['id']}")
    print(f"  Operator: {test['operator']}")
    print(f"  Test Date: {test['test_date']}")
    print(f"  Overall Result: {test.get('overall_result', 'N/A')}")
    print(f"  Blade Results Count: {len(test.get('blade_results', []))}")
    
print("\n\nFull JSON output:")
print(json.dumps(tests, indent=2, default=str))
