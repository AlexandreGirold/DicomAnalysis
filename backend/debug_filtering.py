import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.queries import get_leaf_position_test_by_id

# Simulate what the report generator does
tests_data = []
for test_id in [11, 12, 13, 14, 15]:
    test_dict = get_leaf_position_test_by_id(test_id)
    if test_dict:
        tests_data.append(test_dict)

print(f"Number of tests: {len(tests_data)}")

# Check blade_size filtering
blade_size = "all"
count = 0

for test in tests_data:
    blade_results = test.get('blade_results', [])
    print(f"\nTest {test['id']}: {len(blade_results)} blade_results")
    
    for blade in blade_results[:3]:
        # Check if filtering works
        size = blade.get('field_size_mm', 0)
        if 18 <= size <= 22:
            cat = "20mm"
        elif 28 <= size <= 32:
            cat = "30mm"
        elif 38 <= size <= 42:
            cat = "40mm"
        else:
            cat = "unknown"
        
        passes_filter = (blade_size == "all" or cat == blade_size)
        count += 1
        print(f"  Blade {blade['blade_pair']}: size={size}mm, cat={cat}, passes_filter={passes_filter}")

print(f"\nTotal blades that should be displayed: {count}")
