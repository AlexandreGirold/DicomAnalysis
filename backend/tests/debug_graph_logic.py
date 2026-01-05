import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.queries import get_leaf_position_test_by_id

# Simulate the graph function
tests_data = []
for test_id in [11]:
    test_dict = get_leaf_position_test_by_id(test_id)
    if test_dict:
        tests_data.append(test_dict)

blade_size = "all"
blade_data_dict = {}

for test in tests_data:
    blade_results = test.get('blade_results', [])
    print(f"Processing test with {len(blade_results)} blade_results")
    
    for blade in blade_results[:5]:
        # Check filtering (should not skip when blade_size == "all")
        should_skip = (blade_size != "all")
        print(f"  blade_size={blade_size}, should_skip={should_skip}")
        
        if should_skip:
            continue
        
        blade_id = blade.get('blade_pair', 'unknown')
        print(f"  Processing blade_id: {blade_id}")
        
        try:
            blade_num = int(blade_id) if blade_id.isdigit() else int(''.join(filter(str.isdigit, blade_id.split('-')[0])))
            print(f"    Extracted blade_num: {blade_num}")
        except Exception as e:
            print(f"    Error extracting number: {e}")
            continue
        
        if blade_num not in blade_data_dict:
            blade_data_dict[blade_num] = {
                'sizes': [],
                'statuses': [],
                'target': blade.get('field_size_mm', 20.0)
            }
        
        blade_data_dict[blade_num]['sizes'].append(blade.get('field_size_mm', 0))
        blade_data_dict[blade_num]['statuses'].append(blade.get('is_valid', 'UNKNOWN'))

print(f"\nFinal blade_data_dict has {len(blade_data_dict)} entries")
for k, v in list(blade_data_dict.items())[:3]:
    print(f"  Blade {k}: {v}")
