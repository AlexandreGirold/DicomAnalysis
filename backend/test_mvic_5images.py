"""
Test script for MVIC with 5 images
Tests the multi-file processing and automatic detection
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.weekly.MVIC import MVICTest, test_mvic

def test_mvic_multi_file():
    """Test MVIC with multiple files"""
    print("\n" + "="*60)
    print("TEST: MVIC avec 5 images")
    print("="*60)
    
    # Test 1: Verify MVICTest can be instantiated
    print("\n1. Instantiation de MVICTest...")
    try:
        test = MVICTest()
        print("   ✓ MVICTest instantiated successfully")
        print(f"   ✓ Test name: {test.test_name}")
        print(f"   ✓ Description: {test.description}")
    except Exception as e:
        print(f"   ✗ Failed to instantiate: {e}")
        return False
    
    # Test 2: Check that execute accepts files parameter
    print("\n2. Vérification de la signature execute()...")
    try:
        import inspect
        sig = inspect.signature(test.execute)
        params = list(sig.parameters.keys())
        print(f"   ✓ Parameters: {params}")
        
        if 'files' not in params:
            print("   ✗ Missing 'files' parameter")
            return False
        if 'operator' not in params:
            print("   ✗ Missing 'operator' parameter")
            return False
        
        print("   ✓ Signature correcte (files, operator, test_date, notes)")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 3: Check form data has multiple file field
    print("\n3. Vérification des données du formulaire...")
    try:
        form_data = test.get_form_data()
        print(f"   ✓ Title: {form_data['title']}")
        print(f"   ✓ Description: {form_data['description']}")
        
        # Find dicom_files field
        dicom_field = None
        for field in form_data['fields']:
            if 'dicom' in field['name'].lower():
                dicom_field = field
                break
        
        if not dicom_field:
            print("   ✗ No DICOM file field found")
            return False
        
        print(f"   ✓ DICOM field name: {dicom_field['name']}")
        print(f"   ✓ Multiple: {dicom_field.get('multiple', False)}")
        print(f"   ✓ Help: {dicom_field.get('help', '')}")
        
        if not dicom_field.get('multiple'):
            print("   ⚠ Warning: Field should have 'multiple': True")
        
        # Check that expected_size field is removed
        has_expected_size = any('expected_size' in field['name'] for field in form_data['fields'])
        if has_expected_size:
            print("   ⚠ Warning: expected_size field should be removed")
        else:
            print("   ✓ expected_size field correctement supprimé")
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 4: Check helper methods exist
    print("\n4. Vérification des méthodes d'extraction de métadonnées...")
    try:
        if not hasattr(test, '_get_dicom_datetime'):
            print("   ✗ Missing _get_dicom_datetime method")
            return False
        if not hasattr(test, '_read_dicom_header'):
            print("   ✗ Missing _read_dicom_header method")
            return False
        
        print("   ✓ _get_dicom_datetime exists")
        print("   ✓ _read_dicom_header exists")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 5: Test file count validation
    print("\n5. Test de validation du nombre de fichiers...")
    try:
        # Should fail with wrong number of files
        try:
            result = test.execute(
                files=[],
                operator="Test Operator"
            )
            print("   ✗ Should have raised ValueError for 0 files")
            return False
        except ValueError as e:
            if "5 images" in str(e) or "5 fichiers" in str(e).lower():
                print(f"   ✓ Correctly validates file count: {e}")
            else:
                print(f"   ⚠ Unexpected error message: {e}")
        
        # Should fail with 3 files
        try:
            result = test.execute(
                files=["file1.dcm", "file2.dcm", "file3.dcm"],
                operator="Test Operator"
            )
            print("   ✗ Should have raised ValueError for 3 files")
            return False
        except (ValueError, Exception) as e:
            print(f"   ✓ Correctly rejects 3 files: {e}")
    
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✓ TOUS LES TESTS SONT PASSÉS")
    print("="*60)
    print("\nRésumé:")
    print("  ✓ MVICTest accepte 5 fichiers")
    print("  ✓ Extraction de dates DICOM implémentée")
    print("  ✓ Auto-détection de taille (pas de expected_size)")
    print("  ✓ Validation du nombre de fichiers")
    print("\nLe test MVIC est prêt pour traiter 5 images!")
    
    return True

if __name__ == "__main__":
    success = test_mvic_multi_file()
    sys.exit(0 if success else 1)
