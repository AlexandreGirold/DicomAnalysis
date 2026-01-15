"""
Check test ID 4 (working) visualization paths
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.queries import get_leaf_position_test_by_id
import json

test_id = 4
test = get_leaf_position_test_by_id(test_id)

if test:
    print(f"Test ID {test_id} found")
    print(f"Operator: {test.get('operator')}")
    print(f"Test Date: {test.get('test_date')}")
    print(f"Overall Result: {test.get('overall_result')}")
    
    viz_paths = test.get('visualization_paths')
    print(f"\nVisualization Paths (raw): {viz_paths}")
    print(f"Type: {type(viz_paths)}")
    
    if viz_paths:
        try:
            paths = json.loads(viz_paths) if isinstance(viz_paths, str) else viz_paths
            print(f"\n✅ Parsed paths ({len(paths)} items):")
            for i, path in enumerate(paths):
                print(f"  {i+1}. {path}")
        except Exception as e:
            print(f"Error parsing paths: {e}")
    else:
        print("\n⚠️ NO VISUALIZATION PATHS FOUND!")
else:
    print(f"Test ID {test_id} not found")
