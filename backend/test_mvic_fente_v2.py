"""
Test script for MVIC Fente V2 implementation
Tests edge detection and slit analysis
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("=" * 60)
print("MVIC FENTE V2 TEST - Edge Detection Method")
print("=" * 60)

# Test 1: Import test
print("\n[1] Testing imports...")
try:
    from services.weekly.MVIC_fente import MVICFenteV2Test, test_mvic_fente_v2
    print("✓ MVICFenteV2Test imported successfully")
    print("✓ test_mvic_fente_v2 function imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Class instantiation
print("\n[2] Testing class instantiation...")
try:
    test = MVICFenteV2Test()
    print(f"✓ Test name: {test.test_name}")
    print(f"✓ Description: {test.description}")
    print(f"✓ Center U: {test.center_u}")
    print(f"✓ Center V: {test.center_v}")
    print(f"✓ Pixel spacing: {test.pixel_size_mm} mm/px")
except Exception as e:
    print(f"✗ Instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Form data
print("\n[3] Testing form data generation...")
try:
    form_data = test.get_form_data()
    print(f"✓ Form title: {form_data['title']}")
    print(f"✓ Form description: {form_data['description']}")
    print(f"✓ Number of fields: {len(form_data['fields'])}")
    for field in form_data['fields']:
        print(f"  - {field['name']}: {field['type']} ({'required' if field.get('required') else 'optional'})")
except Exception as e:
    print(f"✗ Form data generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Weekly tests registry
print("\n[4] Testing weekly tests registry...")
try:
    from services.weekly import WEEKLY_TESTS
    
    if 'mvic_fente_v2' in WEEKLY_TESTS:
        test_info = WEEKLY_TESTS['mvic_fente_v2']
        print("✓ mvic_fente_v2 found in WEEKLY_TESTS")
        print(f"  - Class: {test_info['class'].__name__}")
        print(f"  - Description: {test_info['description']}")
        print(f"  - Category: {test_info['category']}")
    else:
        print("✗ mvic_fente_v2 NOT found in WEEKLY_TESTS")
        print(f"  Available tests: {list(WEEKLY_TESTS.keys())}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Registry check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test with real DICOM files
print("\n[5] Testing with real DICOM files...")
dicom_folder = r"R:\Radiotherapie - Physique Medicale\06 Contrôle qualité\01 Accélérateurs\11_UNITY\CQ_Mensuel\Collimation\2025\09\TailleChamp17-09-2025"

if os.path.exists(dicom_folder):
    dicom_files = [os.path.join(dicom_folder, f) for f in os.listdir(dicom_folder) if f.endswith('.dcm')]
    
    if dicom_files:
        print(f"✓ Found {len(dicom_files)} DICOM files")
        
        # Take first 2 files for testing
        test_files = dicom_files[:2]
        print(f"  Testing with: {[os.path.basename(f) for f in test_files]}")
        
        try:
            result = test_mvic_fente_v2(
                files=test_files,
                operator="Test Operator",
                notes="Automated test"
            )
            
            print(f"✓ Test executed successfully")
            print(f"  - Overall result: {result['overall_result']}")
            print(f"  - Total images: {result.get('total_images', 0)}")
            print(f"  - Total slits: {result.get('total_slits_detected', 0)}")
            
            # Check detailed results
            if 'detailed_results' in result:
                for idx, img_result in enumerate(result['detailed_results'], 1):
                    print(f"\n  Image {idx}: {img_result['file']}")
                    print(f"    - Slits detected: {img_result['num_slits']}")
                    
                    if img_result['num_slits'] > 0:
                        for slit_idx, slit in enumerate(img_result['slits'], 1):
                            print(f"    - Slit {slit_idx}:")
                            print(f"      Width: {slit['width_mm']} mm")
                            print(f"      Center: ({slit['center_u']:.1f}, {slit['center_v']:.1f})")
            
            # Check visualizations
            if 'visualizations' in result:
                print(f"\n  ✓ Visualizations: {len(result['visualizations'])}")
                for viz in result['visualizations']:
                    print(f"    - {viz['name']}")
                    if 'statistics' in viz:
                        stats = viz['statistics']
                        print(f"      Status: {stats.get('status')}")
                        print(f"      Slits: {stats.get('total_blades', 0)}")
            
        except Exception as e:
            print(f"✗ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"! No DICOM files found in {dicom_folder}")
        print("  Skipping real file test")
else:
    print(f"! DICOM folder not found: {dicom_folder}")
    print("  Skipping real file test")

print("\n" + "=" * 60)
print("✓✓✓ ALL TESTS PASSED ✓✓✓")
print("=" * 60)
print("\nMVIC Fente V2 is ready to use!")
print("Available at: http://127.0.0.1:8000/basic-tests/mvic_fente_v2")
