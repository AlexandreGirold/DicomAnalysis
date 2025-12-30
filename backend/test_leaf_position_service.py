import sys
import os
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

# Find a DICOM file to test with
import glob

# Look for DICOM files in uploads or data directory
dicom_files = glob.glob('uploads/*.dcm') + glob.glob('data/*.dcm')

if not dicom_files:
    print("No DICOM files found in uploads/ or data/ directories")
    print("Please specify a DICOM file path manually")
    exit(1)

print(f"Found {len(dicom_files)} DICOM files")
print(f"Using: {dicom_files[0]}")

# Test the leaf position service
from services.weekly.leaf_position import LeafPositionTest
from datetime import datetime

test = LeafPositionTest()
result = test.execute(
    files=[dicom_files[0]],
    operator="Diagnostic Test",
    test_date=datetime.now(),
    notes="Testing blade_results generation"
)

print("\n=== RESULT STRUCTURE ===")
print(f"Keys: {list(result.keys())}")
print(f"\nblade_results type: {type(result.get('blade_results'))}")
print(f"blade_results length: {len(result.get('blade_results', []))}")

if result.get('blade_results'):
    print(f"\nFirst blade_results item type: {type(result['blade_results'][0])}")
    print(f"First blade_results item keys: {list(result['blade_results'][0].keys()) if isinstance(result['blade_results'][0], dict) else 'NOT A DICT'}")
    
    if isinstance(result['blade_results'][0], dict) and 'blades' in result['blade_results'][0]:
        blades = result['blade_results'][0]['blades']
        print(f"\nNumber of blades in first image: {len(blades)}")
        if blades:
            print(f"First blade: {blades[0]}")
else:
    print("\nNo blade_results generated!")
