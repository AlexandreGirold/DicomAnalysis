"""
Test MVIC API endpoint with simulated file uploads
"""
import requests
import os

def test_mvic_api():
    """Test the MVIC API endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/basic-tests/mvic"
    
    # Test data
    operator = "Test Operator"
    test_date = "2024-11-21"
    
    # Check if we have a test DICOM file
    test_file = r"c:\Users\agirold\Desktop\DicomAnalysis\1.3.46.423632.420000.1735982979.14.dcm"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"✓ Found test file: {test_file}")
    
    # Prepare form data with 5 files (using same file 5 times for testing)
    files = []
    form_data = {
        'operator': operator,
        'test_date': test_date,
        'notes': 'Test via Python script'
    }
    
    print("\nPreparing form data:")
    print(f"  operator: {operator}")
    print(f"  test_date: {test_date}")
    print(f"  files: 5 copies of test file")
    
    # Open file 5 times with different names
    try:
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        # Create 5 file tuples
        for i in range(1, 6):
            files.append(('dicom_files', (f'test_image_{i}.dcm', file_content, 'application/dicom')))
        
        print("\n📤 Sending POST request to:", url)
        response = requests.post(url, data=form_data, files=files)
        
        print(f"\n📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            result = response.json()
            print("\nResult:")
            print(f"  Test: {result.get('test_name')}")
            print(f"  Status: {result.get('overall_result')}")
            print(f"  Operator: {result.get('operator')}")
            
            # Show per-image results
            if 'results' in result:
                print("\n  Per-image results:")
                for key, value in result['results'].items():
                    if 'image_' in key and 'fichier' in key:
                        print(f"    {key}: {value.get('value')} - {value.get('details')}")
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("Testing MVIC API Endpoint")
    print("="*60)
    print("\nNOTE: Make sure the backend server is running!")
    print("Start it with: cd backend && python main.py\n")
    
    input("Press Enter to continue...")
    
    success = test_mvic_api()
    
    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("="*60)
