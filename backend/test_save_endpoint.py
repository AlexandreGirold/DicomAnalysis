"""
Check if the updated save_piqt_session code is loaded in the running server
"""
import requests
import json

# Test data with results array
test_data = {
    "operator": "test_user",
    "test_date": "2025-12-11",
    "overall_result": "PASS",
    "notes": "Test to verify results extraction",
    "results": [
        {"name": "SNR Value", "value": 123.45, "status": "PASS", "unit": "", "tolerance": "N/A"},
        {"name": "Uniformity", "value": 95.5, "status": "PASS", "unit": "%", "tolerance": "N/A"},
        {"name": "Ghosting", "value": 2.1, "status": "PASS", "unit": "%", "tolerance": "N/A"}
    ]
}

print("Testing save endpoint with results array...")
print(f"Data: {json.dumps(test_data, indent=2)}")

response = requests.post(
    "http://localhost:8000/piqt-sessions",
    json=test_data
)

print(f"\nResponse status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    test_id = response.json().get('test_id')
    print(f"\nSaved as test ID: {test_id}")
    
    # Check what was actually saved
    from database.config import SessionLocal
    from database.weekly_tests import PIQTTest
    
    db = SessionLocal()
    test = db.query(PIQTTest).filter(PIQTTest.id == test_id).first()
    
    if test:
        print(f"\nVerifying saved data:")
        print(f"  SNR: {test.snr_value}")
        print(f"  Uniformity: {test.uniformity_value}")
        print(f"  Ghosting: {test.ghosting_value}")
        print(f"  Results JSON length: {len(test.results_json) if test.results_json else 0}")
        
        if test.results_json:
            print(f"  Results JSON preview: {test.results_json[:200]}")
    
    db.close()
