"""
Check all recent LeafPosition tests for visualization_paths
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.queries import get_all_leaf_position_tests
import json

tests = get_all_leaf_position_tests(limit=20)

print(f"Found {len(tests)} recent tests\n")
print("=" * 80)

for test in tests:
    test_id = test.get('id')
    viz_paths = test.get('visualization_paths')
    
    status = "✅" if viz_paths else "❌"
    
    print(f"{status} Test ID {test_id}: {test.get('operator')} - {test.get('test_date')}")
    
    if viz_paths:
        try:
            paths = json.loads(viz_paths) if isinstance(viz_paths, str) else viz_paths
            print(f"   {len(paths)} visualization(s)")
        except Exception as e:
            print(f"   Error: {e}")
    else:
        print(f"   NO visualization_paths")
    
    # Check actual files on disk
    viz_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'visualizations', 'leaf_position')
    if os.path.exists(viz_dir):
        test_files = [f for f in os.listdir(viz_dir) if f.startswith(f'test_{test_id}_')]
        if test_files:
            print(f"   📁 {len(test_files)} file(s) on disk")
            if not viz_paths:
                print(f"   ⚠️  MISMATCH: Files exist but not in DB!")
    
    print()
