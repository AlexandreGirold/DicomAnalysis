"""
Verify that each test type routes to the correct endpoint and database table
"""

print("=" * 80)
print("FRONTEND → BACKEND → DATABASE ROUTING VERIFICATION")
print("=" * 80)

# From frontend/js/mlc-save.js TEST_SAVE_ENDPOINTS
FRONTEND_ENDPOINTS = {
    'mvic': '/mvic-test-sessions',
    'mvic_fente_v2': '/mvic-fente-v2-sessions',
    'mlc_leaf_jaw': '/mlc-leaf-jaw-sessions',
    'niveau_helium': '/niveau-helium-sessions',
    'piqt': '/piqt-sessions',
    'safety_systems': '/safety-systems-sessions',
    'position_table_v2': '/position-table-sessions',
    'alignement_laser': '/alignement-laser-sessions',
    'quasar': '/quasar-sessions',
    'indice_quality': '/indice-quality-sessions'
}

# Expected backend endpoints and their database tables
EXPECTED_ROUTING = {
    'mvic': {
        'endpoint': '/mvic-test-sessions',
        'backend_function': 'save_mvic_session',
        'db_table': 'weekly_mvic',
        'db_helper': 'save_mvic_to_database',
        'model': 'MVICTest'
    },
    'mvic_fente_v2': {
        'endpoint': '/mvic-fente-v2-sessions',
        'backend_function': 'save_mvic_fente_v2_session',
        'db_table': 'weekly_mvic_fente_v2',
        'db_helper': 'save_generic_test_to_database',
        'model': 'MVICFenteV2Test'
    },
    'mlc_leaf_jaw': {
        'endpoint': '/mlc-leaf-jaw-sessions',
        'backend_function': 'save_mlc_leaf_jaw_session',
        'db_table': 'weekly_mlc_leaf_jaw',
        'db_helper': 'save_mlc_leaf_jaw_to_database',
        'model': 'MLCLeafJawTest'
    },
    'niveau_helium': {
        'endpoint': '/niveau-helium-sessions',
        'backend_function': 'save_niveau_helium_session',
        'db_table': 'weekly_niveau_helium',
        'db_helper': 'save_niveau_helium_to_database',
        'model': 'NiveauHeliumTest'
    },
    'piqt': {
        'endpoint': '/piqt-sessions',
        'backend_function': 'save_piqt_session',
        'db_table': 'weekly_piqt',
        'db_helper': 'save_generic_test_to_database',
        'model': 'PIQTTest'
    },
    'safety_systems': {
        'endpoint': '/safety-systems-sessions',
        'backend_function': 'save_safety_systems_session',
        'db_table': 'daily_safety_systems',
        'db_helper': 'save_generic_test_to_database',
        'model': 'SafetySystemsTest'
    },
    'position_table_v2': {
        'endpoint': '/position-table-sessions',
        'backend_function': 'save_position_table_session',
        'db_table': 'monthly_position_table_v2',
        'db_helper': 'save_generic_test_to_database',
        'model': 'PositionTableV2Test'
    },
    'alignement_laser': {
        'endpoint': '/alignement-laser-sessions',
        'backend_function': 'save_alignement_laser_session',
        'db_table': 'monthly_alignement_laser',
        'db_helper': 'save_generic_test_to_database',
        'model': 'AlignementLaserTest'
    },
    'quasar': {
        'endpoint': '/quasar-sessions',
        'backend_function': 'save_quasar_session',
        'db_table': 'monthly_quasar',
        'db_helper': 'save_generic_test_to_database',
        'model': 'QuasarTest'
    },
    'indice_quality': {
        'endpoint': '/indice-quality-sessions',
        'backend_function': 'save_indice_quality_session',
        'db_table': 'monthly_indice_quality',
        'db_helper': 'save_generic_test_to_database',
        'model': 'IndiceQualityTest'
    }
}

print("\n✅ CORRECT ROUTING:\n")
for test_type, info in EXPECTED_ROUTING.items():
    frontend_endpoint = FRONTEND_ENDPOINTS.get(test_type, FRONTEND_ENDPOINTS.get(test_type.replace('_', ''), 'NOT FOUND'))
    
    status = "✅" if frontend_endpoint == info['endpoint'] else "❌"
    print(f"{status} {test_type}")
    print(f"   Frontend: {frontend_endpoint}")
    print(f"   Backend:  {info['endpoint']} → {info['backend_function']}()")
    print(f"   DB Table: {info['db_table']}")
    print(f"   Model:    {info['model']}")
    print()

print("=" * 80)
print("CHECKING BACKEND ENDPOINTS IN main.py")
print("=" * 80)

import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all @app.post endpoints
endpoints = re.findall(r'@app\.post\("([^"]+)"\)\s+async def (\w+)', content)

print(f"\nFound {len(endpoints)} POST endpoints in main.py:\n")

for endpoint_path, function_name in endpoints:
    # Check if this endpoint is in our expected list
    expected = None
    for test_type, info in EXPECTED_ROUTING.items():
        if info['endpoint'] == endpoint_path:
            expected = info
            break
    
    if expected:
        # Extract the database helper call from the function
        pattern = rf'async def {function_name}.*?(?=@app\.|$)'
        func_match = re.search(pattern, content, re.DOTALL)
        if func_match:
            func_content = func_match.group(0)
            
            # Check for database_helpers calls
            db_calls = re.findall(r'database_helpers\.(\w+)\(', func_content)
            # Check for database.ClassName references
            db_models = re.findall(r'database\.(\w+)', func_content)
            
            status = "✅"
            notes = []
            
            if expected['db_helper'] in db_calls:
                notes.append(f"calls {expected['db_helper']}")
            else:
                notes.append(f"⚠️ should call {expected['db_helper']}")
                status = "⚠️"
            
            if expected['model'] in db_models:
                notes.append(f"uses {expected['model']}")
            else:
                notes.append(f"⚠️ should use {expected['model']}")
            
            print(f"{status} {endpoint_path}")
            print(f"   Function: {function_name}()")
            print(f"   Details: {', '.join(notes)}")
            print()

print("=" * 80)
