"""
Test script to verify all test save endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, data, test_name):
    """Test a single save endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Test saved')}")
            print(f"   Test ID: {result.get('test_id')}")
            return result.get('test_id')
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def main():
    """Run tests for all endpoints"""
    
    print("\n" + "="*60)
    print("TESTING ALL DATABASE SAVE ENDPOINTS")
    print("="*60)
    
    test_date = datetime.now().isoformat()
    operator = "Test Operator"
    
    # Test 1: MVIC Test
    mvic_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "results": [
            {
                "top_left_angle": 90.0,
                "top_right_angle": 90.1,
                "bottom_left_angle": 89.9,
                "bottom_right_angle": 90.2,
                "height": 150.5,
                "width": 150.3
            },
            {
                "top_left_angle": 90.1,
                "top_right_angle": 90.0,
                "bottom_left_angle": 90.0,
                "bottom_right_angle": 89.9,
                "height": 150.4,
                "width": 150.2
            },
            {
                "top_left_angle": 89.9,
                "top_right_angle": 90.2,
                "bottom_left_angle": 90.1,
                "bottom_right_angle": 90.0,
                "height": 150.6,
                "width": 150.4
            },
            {
                "top_left_angle": 90.2,
                "top_right_angle": 89.8,
                "bottom_left_angle": 90.0,
                "bottom_right_angle": 90.1,
                "height": 150.3,
                "width": 150.5
            },
            {
                "top_left_angle": 90.0,
                "top_right_angle": 90.0,
                "bottom_left_angle": 90.0,
                "bottom_right_angle": 90.0,
                "height": 150.4,
                "width": 150.4
            }
        ],
        "notes": "Test MVIC save",
        "filenames": ["test1.dcm", "test2.dcm", "test3.dcm", "test4.dcm", "test5.dcm"]
    }
    test_endpoint("/mvic-test-sessions", mvic_data, "MVIC Test (5 images)")
    
    # Test 2: MLC Leaf Jaw Test
    mlc_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test MLC Leaf Jaw save",
        "filenames": ["mlc_test.dcm"]
    }
    test_endpoint("/mlc-leaf-jaw-sessions", mlc_data, "MLC Leaf Jaw Test")
    
    # Test 3: MVIC Fente V2 Test
    mvic_fente_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "results": [
            {
                "slits": [
                    {"width_mm": 5.0, "height_pixels": 100, "center_u": 512, "center_v": 384},
                    {"width_mm": 10.0, "height_pixels": 200, "center_u": 512, "center_v": 484}
                ]
            }
        ],
        "notes": "Test MVIC Fente V2 save",
        "filenames": ["fente_test.dcm"]
    }
    test_endpoint("/mvic-fente-v2-sessions", mvic_fente_data, "MVIC Fente V2 Test")
    
    # Test 4: Niveau Helium Test
    helium_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "helium_level": 95.5,
        "notes": "Test Helium save",
        "filenames": ["helium_test.dcm"]
    }
    test_endpoint("/niveau-helium-sessions", helium_data, "Niveau Helium Test")
    
    # Test 5: PIQT Test
    piqt_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test PIQT save",
        "filenames": ["piqt_test.dcm"]
    }
    test_endpoint("/piqt-sessions", piqt_data, "PIQT Test")
    
    # Test 6: Safety Systems Test
    safety_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test Safety Systems save",
        "filenames": []
    }
    test_endpoint("/safety-systems-sessions", safety_data, "Safety Systems Test")
    
    # Test 7: Position Table Test
    position_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test Position Table save",
        "filenames": ["position_test.dcm"]
    }
    test_endpoint("/position-table-sessions", position_data, "Position Table V2 Test")
    
    # Test 8: Alignement Laser Test
    laser_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test Alignement Laser save",
        "filenames": ["laser_test.dcm"]
    }
    test_endpoint("/alignement-laser-sessions", laser_data, "Alignement Laser Test")
    
    # Test 9: Quasar Test
    quasar_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test Quasar save",
        "filenames": ["quasar_test.dcm"]
    }
    test_endpoint("/quasar-sessions", quasar_data, "Quasar Test")
    
    # Test 10: Indice Quality Test
    indice_data = {
        "test_date": test_date,
        "operator": operator,
        "overall_result": "PASS",
        "notes": "Test Indice Quality save",
        "filenames": ["indice_test.dcm"]
    }
    test_endpoint("/indice-quality-sessions", indice_data, "Indice Quality Test")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
