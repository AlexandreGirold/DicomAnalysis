"""
Test script for API endpoints
Tests the new basic tests endpoints without starting the full server
"""
import sys
import os
import json
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all imports work correctly"""
    print("=== Testing Imports ===")
    try:
        from services.basic_tests import (
            get_available_tests,
            create_test_instance,
            execute_test
        )
        print("✅ Basic tests imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_api_logic():
    """Test the API endpoint logic without FastAPI"""
    print("\n=== Testing API Logic ===")
    
    try:
        # Import the basic tests
        from services.basic_tests import get_available_tests, execute_test
        
        # Test 1: Get available tests
        print("1. Testing get_available_tests...")
        tests = get_available_tests()
        print(f"   Available tests: {list(tests.keys())}")
        
        # Test 2: Execute niveau helium test
        print("2. Testing niveau helium execution...")
        result = execute_test(
            'niveau_helium',
            helium_level=75.5,
            operator="Test Operator",
            test_date=datetime.now()
        )
        print(f"   Result: {result['overall_result']} (Level: {result['inputs']['helium_level']['value']}%)")
        
        # Test 3: Execute position table test
        print("3. Testing position table V2 execution...")
        result = execute_test(
            'position_table_v2',
            position_175=17.5,
            position_215=21.5,
            operator="Test Operator"
        )
        print(f"   Result: {result['overall_result']} (Ecart: {result['results']['ecart_mm']['value']}mm)")
        
        # Test 4: Execute alignement laser test
        print("4. Testing alignement laser execution...")
        result = execute_test(
            'alignement_laser',
            ecart_proximal=1.2,
            ecart_central=0.8,
            ecart_distal=1.5,
            operator="Test Operator"
        )
        print(f"   Result: {result['overall_result']}")
        
        return True
    except Exception as e:
        print(f"❌ API Logic error: {e}")
        return False

def test_data_validation():
    """Test data validation scenarios"""
    print("\n=== Testing Data Validation ===")
    
    try:
        from services.basic_tests import execute_test
        
        # Test invalid helium level
        print("1. Testing invalid helium level...")
        try:
            execute_test('niveau_helium', helium_level=150, operator="Test")
            print("   ❌ Should have failed with invalid level")
        except ValueError:
            print("   ✅ Correctly rejected invalid helium level")
        
        # Test missing operator
        print("2. Testing missing parameters...")
        try:
            execute_test('niveau_helium', helium_level=70)  # Missing operator
            print("   ❌ Should have failed with missing operator")
        except TypeError:
            print("   ✅ Correctly rejected missing operator")
        
        return True
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        return False

def simulate_api_requests():
    """Simulate the API request/response flow"""
    print("\n=== Simulating API Requests ===")
    
    try:
        from services.basic_tests import get_available_tests, create_test_instance, execute_test
        
        # Simulate GET /basic-tests
        print("GET /basic-tests")
        tests = get_available_tests()
        response = {
            'available_tests': tests,
            'count': len(tests)
        }
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        # Simulate GET /basic-tests/niveau_helium/form
        print("\nGET /basic-tests/niveau_helium/form")
        test_instance = create_test_instance('niveau_helium')
        form_data = test_instance.get_form_data()
        print(f"   Form fields: {len(form_data['fields'])} fields")
        
        # Simulate POST /basic-tests/niveau-helium
        print("\nPOST /basic-tests/niveau-helium")
        data = {
            "helium_level": 75.5,
            "operator": "Dr. Dupont",
            "test_date": "2025-11-10"
        }
        
        # Parse date like in API
        test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        result = execute_test(
            'niveau_helium',
            helium_level=float(data['helium_level']),
            operator=data['operator'],
            test_date=test_date
        )
        print(f"   Test result: {result['overall_result']}")
        
        return True
    except Exception as e:
        print(f"❌ API simulation error: {e}")
        return False

def main():
    """Run all tests"""
    print("API Endpoints Test Suite")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_api_logic()
    success &= test_data_validation()
    success &= simulate_api_requests()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed'}")
    return success

if __name__ == "__main__":
    main()