"""
Test the leaf position image identification logic
"""
import sys
sys.path.insert(0, '.')

from services.leaf_position_identifier import (
    identify_image_position, 
    identify_all_images, 
    validate_identification,
    REFERENCE_PROFILES
)

print("=" * 60)
print("Testing Leaf Position Image Identification")
print("=" * 60)

# Display reference profiles
print("\nReference Profiles:")
for pos, profile in sorted(REFERENCE_PROFILES.items()):
    print(f"  Position {pos}: top={profile['top']:+6.1f}mm, bottom={profile['bottom']:+6.1f}mm")

# Test individual identification
print("\n" + "=" * 60)
print("Test 1: Individual Image Identification")
print("=" * 60)

test_cases = [
    (40.1, 20.2, 1),   # Should match position 1
    (30.0, 10.0, 2),   # Should match position 2
    (19.8, -0.1, 3),   # Should match position 3
    (0.2, -19.9, 4),   # Should match position 4
    (-9.8, -30.1, 5),  # Should match position 5
    (-20.1, -39.9, 6), # Should match position 6
]

for top, bottom, expected in test_cases:
    result = identify_image_position(top, bottom)
    status = "✓" if result == expected else "✗"
    print(f"{status} (top={top:+6.1f}, bottom={bottom:+6.1f}) → Position {result} (expected {expected})")

# Test full set identification
print("\n" + "=" * 60)
print("Test 2: Full Set Identification (Correct Order)")
print("=" * 60)

correct_order = [
    {'upload_order': 1, 'top_average': 40.0, 'bottom_average': 20.0, 'filename': 'img1.dcm'},
    {'upload_order': 2, 'top_average': 30.0, 'bottom_average': 10.0, 'filename': 'img2.dcm'},
    {'upload_order': 3, 'top_average': 20.0, 'bottom_average': 0.0, 'filename': 'img3.dcm'},
    {'upload_order': 4, 'top_average': 0.0, 'bottom_average': -20.0, 'filename': 'img4.dcm'},
    {'upload_order': 5, 'top_average': -10.0, 'bottom_average': -30.0, 'filename': 'img5.dcm'},
    {'upload_order': 6, 'top_average': -20.0, 'bottom_average': -40.0, 'filename': 'img6.dcm'},
]

identified = identify_all_images(correct_order.copy())
is_valid, errors = validate_identification(identified)

print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
if errors:
    for error in errors:
        print(f"  ✗ {error}")

# Test scrambled order
print("\n" + "=" * 60)
print("Test 3: Full Set Identification (Scrambled Order)")
print("=" * 60)

scrambled_order = [
    {'upload_order': 1, 'top_average': -10.0, 'bottom_average': -30.0, 'filename': 'imgA.dcm'},  # Actually pos 5
    {'upload_order': 2, 'top_average': 40.0, 'bottom_average': 20.0, 'filename': 'imgB.dcm'},    # Actually pos 1
    {'upload_order': 3, 'top_average': 0.0, 'bottom_average': -20.0, 'filename': 'imgC.dcm'},    # Actually pos 4
    {'upload_order': 4, 'top_average': -20.0, 'bottom_average': -40.0, 'filename': 'imgD.dcm'},  # Actually pos 6
    {'upload_order': 5, 'top_average': 20.0, 'bottom_average': 0.0, 'filename': 'imgE.dcm'},     # Actually pos 3
    {'upload_order': 6, 'top_average': 30.0, 'bottom_average': 10.0, 'filename': 'imgF.dcm'},    # Actually pos 2
]

identified = identify_all_images(scrambled_order.copy())
is_valid, errors = validate_identification(identified)

print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
if errors:
    for error in errors:
        print(f"  ✗ {error}")

print("\nMapping (Upload Order → Identified Position):")
for img in sorted(identified, key=lambda x: x['upload_order']):
    print(f"  Upload {img['upload_order']} ({img['filename']}) → Position {img.get('identified_position')}")

# Test with real data from earlier test
print("\n" + "=" * 60)
print("Test 4: Real Data from Previous Test")
print("=" * 60)

real_data = [
    {'upload_order': 1, 'top_average': 39.91, 'bottom_average': 20.90, 'filename': 'test1.dcm'},
    {'upload_order': 2, 'top_average': 29.95, 'bottom_average': 10.01, 'filename': 'test2.dcm'},
    {'upload_order': 3, 'top_average': 19.85, 'bottom_average': 0.08, 'filename': 'test3.dcm'},
    {'upload_order': 4, 'top_average': 0.05, 'bottom_average': -19.74, 'filename': 'test4.dcm'},
    {'upload_order': 5, 'top_average': -10.09, 'bottom_average': -29.83, 'filename': 'test5.dcm'},
    {'upload_order': 6, 'top_average': -20.16, 'bottom_average': -39.81, 'filename': 'test6.dcm'},
]

identified = identify_all_images(real_data.copy())
is_valid, errors = validate_identification(identified)

print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
if errors:
    for error in errors:
        print(f"  ✗ {error}")

print("\n" + "=" * 60)
print("All Tests Complete")
print("=" * 60)
