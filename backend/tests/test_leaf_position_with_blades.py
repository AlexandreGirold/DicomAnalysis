"""
Test script to verify leaf position blade data is saved correctly
"""
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from database_helpers import save_leaf_position_to_database
from database.queries import get_leaf_position_test_by_id

# Sample blade data matching the expected format
blade_data = [
    {
        'blades': [
            {
                'pair': 'A1-B1',
                'position_u_px': 512,
                'v_sup_px': 100,
                'v_inf_px': 120,
                'distance_sup_mm': 10.5,
                'distance_inf_mm': 10.3,
                'length_mm': 20.1,
                'field_size_mm': 20.1,
                'is_valid': 'OK',
                'status_message': 'Blade within tolerance'
            },
            {
                'pair': 'A2-B2',
                'position_u_px': 512,
                'v_sup_px': 200,
                'v_inf_px': 230,
                'distance_sup_mm': 15.2,
                'distance_inf_mm': 14.8,
                'length_mm': 30.0,
                'field_size_mm': 30.0,
                'is_valid': 'OK',
                'status_message': 'Blade within tolerance'
            },
            {
                'pair': 'A3-B3',
                'position_u_px': 512,
                'v_sup_px': 300,
                'v_inf_px': 342,
                'distance_sup_mm': 19.5,
                'distance_inf_mm': 21.5,
                'length_mm': 42.0,
                'field_size_mm': 42.0,
                'is_valid': 'OUT_OF_TOLERANCE',
                'status_message': 'Blade exceeds 40mm tolerance'
            }
        ]
    }
]

# File metadata
filenames = ['test_blade_20mm.dcm']
file_results = [
    {
        'file': 'test_blade_20mm.dcm',
        'total_blades': 3,
        'ok': 2,
        'out_of_tolerance': 1,
        'closed': 0,
        'detected_field_size_mm': 30,
        'average_length_mm': 30.7
    }
]

print("=" * 60)
print("Testing Leaf Position Blade Data Save")
print("=" * 60)

# Save test to database
test_id = save_leaf_position_to_database(
    operator="Test Operator",
    test_date=datetime.now(),
    overall_result="FAIL",
    results=blade_data,
    notes="Test with complete blade data",
    filenames=filenames,
    file_results=file_results,
    visualization_paths=None
)

print(f"\n✓ Test saved with ID: {test_id}")

# Retrieve test to verify
test_data = get_leaf_position_test_by_id(test_id)

if test_data:
    print(f"\n✓ Test retrieved successfully")
    print(f"  - Test ID: {test_data.get('id')}")
    print(f"  - Operator: {test_data.get('operator')}")
    print(f"  - Overall Result: {test_data.get('overall_result')}")
    
    blade_results = test_data.get('blade_results', [])
    print(f"\n✓ Blade results count: {len(blade_results)}")
    
    if blade_results:
        print("\nFirst blade details:")
        first_blade = blade_results[0]
        for key, value in first_blade.items():
            print(f"  - {key}: {value}")
        
        print(f"\n✓ SUCCESS: Blade data is being saved and retrieved correctly!")
        print(f"\nBlade summary:")
        for idx, blade in enumerate(blade_results, 1):
            print(f"  {idx}. Pair: {blade['blade_pair']}, Size: {blade['field_size_mm']}mm, Status: {blade['is_valid']}")
    else:
        print("\n✗ ERROR: No blade results found!")
else:
    print(f"\n✗ ERROR: Could not retrieve test {test_id}")

print("\n" + "=" * 60)
