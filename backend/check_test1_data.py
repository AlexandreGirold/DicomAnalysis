from database import SessionLocal
from database.weekly_tests import LeafPositionResult

db = SessionLocal()
results = db.query(LeafPositionResult).filter(LeafPositionResult.test_id == 1).limit(10).all()
print(f'Test 1 has {db.query(LeafPositionResult).filter(LeafPositionResult.test_id == 1).count()} results')
for r in results:
    print(f'Img#{r.image_number}, Blade={r.blade_pair}, Top={r.blade_top_average}, Bot={r.blade_bottom_average}')
db.close()
