import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.config import SessionLocal
from database.weekly_tests import LeafPositionTest

db = SessionLocal()

# Get test ID 5
test = db.query(LeafPositionTest).filter(LeafPositionTest.id == 5).first()

if not test:
    print("Test ID 5 not found")
else:
    print(f"=== Test ID 5 ===")
    print(f"Operator: {test.operator}")
    print(f"Date: {test.test_date}")
    print(f"Overall Result: {test.overall_result}")
    print(f"Filenames: {test.filenames}")
    print(f"Total blade_results: {len(test.blade_results)}")
    
    # Group by blade_pair to see how many images per blade
    from collections import defaultdict
    blades_by_pair = defaultdict(list)
    
    for br in test.blade_results:
        blades_by_pair[br.blade_pair].append({
            'image_number': br.image_number,
            'filename': br.filename,
            'field_size_mm': br.field_size_mm,
            'is_valid': br.is_valid
        })
    
    print(f"\nBlade pairs: {len(blades_by_pair)}")
    print(f"\nFirst 3 blade pairs:")
    for pair_num in sorted(list(blades_by_pair.keys()))[:3]:
        entries = blades_by_pair[pair_num]
        print(f"  Blade {pair_num}: {len(entries)} entries")
        for entry in entries:
            print(f"    Image {entry['image_number']}: {entry['field_size_mm']}mm - {entry['is_valid']}")

db.close()
