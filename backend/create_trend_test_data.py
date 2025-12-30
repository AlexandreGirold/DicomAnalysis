"""
Create multiple test entries to demonstrate trend graphs
Using realistic MLC blade numbering (27-54)
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from database_helpers import save_leaf_position_to_database

print("=" * 60)
print("Creating Multiple Tests for Trend Analysis")
print("Using MLC blade numbers 27-54")
print("=" * 60)

# MLC blades are numbered 27 to 54 (28 blades total)
# Different blade sizes: 20mm, 30mm, 40mm
blade_configs = [
    # 20mm blades (27-32)
    (27, 20.0), (28, 20.0), (29, 20.0), (30, 20.0), (31, 20.0), (32, 20.0),
    # 30mm blades (33-42)
    (33, 30.0), (34, 30.0), (35, 30.0), (36, 30.0), (37, 30.0),
    (38, 30.0), (39, 30.0), (40, 30.0), (41, 30.0), (42, 30.0),
    # 40mm blades (43-54)
    (43, 40.0), (44, 40.0), (45, 40.0), (46, 40.0), (47, 40.0), (48, 40.0),
    (49, 40.0), (50, 40.0), (51, 40.0), (52, 40.0), (53, 40.0), (54, 40.0)
]

# Create 5 tests over 5 days with varying measurements
for day in range(5):
    test_date = datetime.now() - timedelta(days=4-day)
    
    # Build blade data for all 28 blades
    blades_list = []
    ok_count = 0
    out_of_tolerance_count = 0
    
    for blade_num, target_size in blade_configs:
        # Add small variations and drift over time
        size_variation = (day * 0.05) if blade_num % 7 == 0 else 0  # Some blades drift
        measured_size = target_size + size_variation
        
        # Determine if within tolerance (±1.0mm)
        tolerance = 1.0
        is_within_tolerance = abs(measured_size - target_size) <= tolerance
        
        if is_within_tolerance:
            is_valid = 'OK'
            ok_count += 1
        else:
            is_valid = 'OUT_OF_TOLERANCE'
            out_of_tolerance_count += 1
        
        # Simulate pixel coordinates (realistic values)
        v_sup_px = 100 + (blade_num - 27) * 20
        v_inf_px = v_sup_px + int(measured_size * 2)  # Rough conversion
        
        blades_list.append({
            'pair': str(blade_num),
            'position_u_px': 512,
            'v_sup_px': v_sup_px,
            'v_inf_px': v_inf_px,
            'distance_sup_mm': 10.0 + (blade_num - 27) * 0.5,
            'distance_inf_mm': 10.0 + (blade_num - 27) * 0.5,
            'length_mm': measured_size,
            'field_size_mm': measured_size,
            'is_valid': is_valid,
            'status_message': f'Blade {blade_num}: {measured_size:.2f}mm (target {target_size}mm)'
        })
    
    blade_data = [{'blades': blades_list}]
    
    filenames = [f'mlc_test_day_{day+1}.dcm']
    file_results = [{
        'file': f'mlc_test_day_{day+1}.dcm',
        'total_blades': len(blades_list),
        'ok': ok_count,
        'out_of_tolerance': out_of_tolerance_count,
        'closed': 0,
        'detected_field_size_mm': 30,
        'average_length_mm': sum(b['field_size_mm'] for b in blades_list) / len(blades_list)
    }]
    
    test_id = save_leaf_position_to_database(
        operator="Test Operator",
        test_date=test_date,
        overall_result="PASS" if out_of_tolerance_count == 0 else "FAIL",
        results=blade_data,
        notes=f"Test day {day+1} - MLC blades 27-54",
        filenames=filenames,
        file_results=file_results,
        visualization_paths=None
    )
    
    print(f"✓ Test {day+1}/5 saved (ID: {test_id}, Date: {test_date.strftime('%Y-%m-%d')}, Blades: {len(blades_list)}, OK: {ok_count}, OOT: {out_of_tolerance_count})")

print("\n" + "=" * 60)
print("✓ Created 5 tests with realistic MLC blade data (27-54)")
print("\nTest IDs will be 10-14 (or higher if database already had tests)")
print("=" * 60)
