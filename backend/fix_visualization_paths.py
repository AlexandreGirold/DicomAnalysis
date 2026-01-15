"""
Fix visualization_paths for tests 8, 9, 10 that have PNG files but NULL paths in DB
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database_helpers import update_visualization_paths
import json

# Check which tests need fixing
viz_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'visualizations', 'leaf_position')

tests_to_fix = [8, 9, 10]

for test_id in tests_to_fix:
    # Find all PNG files for this test
    test_files = []
    if os.path.exists(viz_dir):
        all_files = os.listdir(viz_dir)
        test_files = sorted([f for f in all_files if f.startswith(f'test_{test_id}_')])
    
    if test_files:
        # Convert to relative paths matching the storage format
        viz_paths = [f"visualizations/leaf_position/{f}" for f in test_files]
        
        print(f"\nFixing Test ID {test_id}:")
        print(f"  Found {len(test_files)} file(s):")
        for f in test_files:
            print(f"    - {f}")
        
        # Update database
        success = update_visualization_paths(
            test_id=test_id,
            test_type='leaf_position',
            paths=viz_paths
        )
        
        if success:
            print(f"  ✅ Updated database with {len(viz_paths)} path(s)")
        else:
            print(f"  ❌ Failed to update database")
    else:
        print(f"\nTest ID {test_id}: No files found on disk")

print("\n" + "=" * 60)
print("Fix complete! Tests should now display visualizations.")
