import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

# Force reload of all modules
import importlib
if 'database.queries' in sys.modules:
    importlib.reload(sys.modules['database.queries'])
if 'services.mlc_blade_report_generator' in sys.modules:
    importlib.reload(sys.modules['services.mlc_blade_report_generator'])

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("=" * 70)
print("STEP 1: Testing database query")
print("=" * 70)

from database.queries import get_leaf_position_test_by_id

test_data = get_leaf_position_test_by_id(1)
print(f"Test data retrieved: {test_data is not None}")
print(f"Test ID: {test_data.get('id')}")
print(f"blade_results in test_data: {len(test_data.get('blade_results', []))} items")

if test_data.get('blade_results'):
    first_blade = test_data['blade_results'][0]
    print(f"First blade: pair={first_blade.get('blade_pair')}, field_size={first_blade.get('field_size_mm')}")

print("\n" + "=" * 70)
print("STEP 2: Testing report generator")
print("=" * 70)

from services.mlc_blade_report_generator import MLCBladeReportGenerator

generator = MLCBladeReportGenerator()

# Manually test the internal flow
from database import SessionLocal

session = SessionLocal()
tests_data = []

try:
    # Simulate what generate_blade_compliance_report does
    test_dict = get_leaf_position_test_by_id(1)
    if test_dict:
        tests_data.append(test_dict)
        print(f"Test added to tests_data: ID={test_dict.get('id')}")
        print(f"blade_results in test_dict: {len(test_dict.get('blade_results', []))} items")
finally:
    session.close()

# Now test the executive summary extraction logic
print("\n" + "=" * 70)
print("STEP 3: Testing blade extraction in executive summary")
print("=" * 70)

blade_size = "all"
all_blades = []

for test in tests_data:
    blade_results = test.get('blade_results', [])
    print(f"Processing test {test.get('id')}: blade_results has {len(blade_results)} items")
    
    for idx, blade in enumerate(blade_results):
        field_size = blade.get('field_size_mm', 0)
        blade_pair = blade.get('blade_pair')
        
        # Check category
        if 18 <= field_size <= 22:
            category = "20mm"
        elif 28 <= field_size <= 32:
            category = "30mm"
        elif 38 <= field_size <= 42:
            category = "40mm"
        else:
            category = "unknown"
        
        if idx < 3:  # Print first 3
            print(f"  Blade {blade_pair}: field_size={field_size}mm, category={category}")
        
        if blade_size == "all" or category == blade_size:
            all_blades.append(blade)

print(f"\nTotal blades collected: {len(all_blades)}")

if all_blades:
    print("✅ SUCCESS - Blades were collected correctly!")
    
    # Test statistics calculation
    compliant = sum(1 for b in all_blades if b.get('is_valid') == 'OK')
    non_compliant = sum(1 for b in all_blades if b.get('is_valid') == 'OUT_OF_TOLERANCE')
    closed = sum(1 for b in all_blades if b.get('is_valid') == 'CLOSED')
    
    print(f"Statistics:")
    print(f"  Compliant: {compliant}")
    print(f"  Non-compliant: {non_compliant}")
    print(f"  Closed: {closed}")
else:
    print("❌ FAILURE - No blades collected!")

print("\n" + "=" * 70)
print("STEP 4: Generating actual PDF")
print("=" * 70)

pdf_bytes = generator.generate_blade_compliance_report([1], 'all')
print(f"PDF generated: {len(pdf_bytes)} bytes")

with open('test_complete_debug.pdf', 'wb') as f:
    f.write(pdf_bytes)
print("Saved to: test_complete_debug.pdf")
