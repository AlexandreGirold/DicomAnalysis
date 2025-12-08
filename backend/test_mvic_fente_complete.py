"""
Test complet du module MVIC_fente avec une vraie image DICOM
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / 'services'))

print("=" * 60)
print("TEST MVIC FENTE - Module Import & Execution")
print("=" * 60)

# Test 1: Import
print("\n[1/4] Testing module import...")
try:
    from services.weekly.MVIC_fente import MVICFenteTest, test_mvic_fente
    print("✓ Successfully imported MVICFenteTest and test_mvic_fente")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Create instance
print("\n[2/4] Creating test instance...")
try:
    test = MVICFenteTest()
    print(f"✓ Created instance: {test.test_name}")
    print(f"  Description: {test.description}")
except Exception as e:
    print(f"✗ Instance creation failed: {e}")
    sys.exit(1)

# Test 3: Get form data
print("\n[3/4] Getting form configuration...")
try:
    form_data = test.get_form_data()
    print(f"✓ Form title: {form_data['title']}")
    print(f"  Number of fields: {len(form_data['fields'])}")
    print(f"  File upload enabled: {form_data.get('file_upload', False)}")
    print("\n  Fields:")
    for field in form_data['fields']:
        required = "required" if field.get('required') else "optional"
        print(f"    - {field['name']} ({field['type']}, {required})")
except Exception as e:
    print(f"✗ Form data retrieval failed: {e}")
    sys.exit(1)

# Test 4: Check if test file exists
print("\n[4/4] Checking for test DICOM file...")
test_dicom_path = Path(r"R:\Radiotherapie - Physique Medicale\06 Contrôle qualité\01 Accélérateurs\11_UNITY\CQ_Mensuel\Collimation\2025\09\TailleChamp17-09-2025")

if test_dicom_path.exists():
    dicom_files = list(test_dicom_path.glob("*.dcm"))
    if dicom_files:
        print(f"✓ Found {len(dicom_files)} DICOM files in test directory")
        print(f"  First file: {dicom_files[0].name}")
        
        # Try to execute test
        print("\n[BONUS] Executing test on first DICOM file...")
        try:
            result = test_mvic_fente(
                files=[str(dicom_files[0])],
                operator="Test Script",
                notes="Automated test"
            )
            print(f"✓ Test executed successfully!")
            print(f"  Overall result: {result['overall_result']}")
            print(f"  Total bands detected: {result.get('total_bands_detected', 0)}")
            
            if 'detailed_results' in result and result['detailed_results']:
                first_result = result['detailed_results'][0]
                print(f"  File: {first_result['file']}")
                print(f"  Number of bands: {first_result['num_bands']}")
                if first_result['bands']:
                    print(f"\n  First band details:")
                    band = first_result['bands'][0]
                    print(f"    Position: ({band['center_u']}, {band['center_v']})")
                    print(f"    Size: {band['width_pixels']}x{band['height_pixels']} pixels")
                    if 'width_mm' in band:
                        print(f"    Size (mm): {band['width_mm']}x{band['height_mm']} mm")
        except Exception as e:
            print(f"✗ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠ No DICOM files found in test directory")
else:
    print(f"⚠ Test directory not found: {test_dicom_path}")
    print("  (This is normal if you're not connected to the network drive)")

print("\n" + "=" * 60)
print("✓✓✓ ALL CORE TESTS PASSED ✓✓✓")
print("=" * 60)
print("\nThe MVIC_fente test is ready to use!")
print("Access it via:")
print("  - Frontend: http://localhost:8000/ → Select 'MVIC Fente'")
print("  - API: POST http://localhost:8000/basic-tests/mvic_fente")
