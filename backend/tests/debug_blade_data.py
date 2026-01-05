import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.queries import get_leaf_position_test_by_id

# Check test 11
test = get_leaf_position_test_by_id(11)
if test:
    print(f"Test ID: {test['id']}")
    print(f"Number of blade_results: {len(test['blade_results'])}")
    
    if test['blade_results']:
        blade = test['blade_results'][0]
        print(f"\nFirst blade:")
        print(f"  blade_pair: {blade['blade_pair']}")
        print(f"  field_size_mm: {blade['field_size_mm']}")
        print(f"  is_valid: {blade['is_valid']}")
        
        # Test category function
        size = blade['field_size_mm']
        if 18 <= size <= 22:
            cat = "20mm"
        elif 28 <= size <= 32:
            cat = "30mm"
        elif 38 <= size <= 42:
            cat = "40mm"
        else:
            cat = "unknown"
        print(f"  category: {cat}")
        
        print(f"\nAll blade pairs in test 11:")
        for b in test['blade_results'][:5]:
            print(f"  {b['blade_pair']}: {b['field_size_mm']}mm")
