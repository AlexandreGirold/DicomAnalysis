"""Quick test of database save/retrieve"""
from database import SessionLocal, MVICTest, MVICResult

db = SessionLocal()
test = db.query(MVICTest).first()

if test:
    print(f"✓ Test: {test.operator} on {test.test_date.date()}")
    print(f"  Result: {test.overall_result}")
    print(f"  Files: {test.filenames}")
    print(f"  Notes: {test.notes}")
    
    results = db.query(MVICResult).filter(MVICResult.test_id == test.id).all()
    print(f"\n✓ Results: {len(results)} images")
    for r in results:
        print(f"  - Image {r.image_number} ({r.filename}): {r.width}x{r.height}mm")
        print(f"    Angles: TL={r.top_left_angle}° TR={r.top_right_angle}° BL={r.bottom_left_angle}° BR={r.bottom_right_angle}°")
else:
    print("✗ No test found")

db.close()
