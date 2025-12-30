import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from database.config import SessionLocal
from database.weekly_tests import LeafPositionTest, LeafPositionResult
from datetime import datetime

db = SessionLocal()

# Create a test with blade 27 having -10mm deviation
test = LeafPositionTest(
    test_date=datetime(2025, 12, 15, 10, 0, 0),
    operator="Test",
    overall_result="FAIL",
    notes="Test avec lame 27 défectueuse",
    filenames="test_defect.dcm"
)
db.add(test)
db.flush()

# Add blade 27 with -10mm deviation (target 20mm, measured 10mm)
blade = LeafPositionResult(
    test_id=test.id,
    image_number=1,
    filename="test_defect.dcm",
    blade_pair=27,
    position_u_px=100.0,
    v_sup_px=200.0,
    v_inf_px=250.0,
    distance_sup_mm=15.0,
    distance_inf_mm=5.0,
    length_mm=10.0,
    field_size_mm=10.0,  # 10mm instead of 20mm = -10mm deviation
    is_valid="OUT_OF_TOLERANCE",
    status_message="OUT OF TOLERANCE: -10.0mm deviation"
)
db.add(blade)

# Add other blades as OK
for blade_num in range(28, 55):
    blade = LeafPositionResult(
        test_id=test.id,
        image_number=1,
        filename="test_defect.dcm",
        blade_pair=blade_num,
        position_u_px=100.0,
        v_sup_px=200.0,
        v_inf_px=300.0,
        distance_sup_mm=20.0,
        distance_inf_mm=10.0,
        length_mm=20.0,
        field_size_mm=20.0,
        is_valid="OK",
        status_message="OK"
    )
    db.add(blade)

db.commit()
print(f"✅ Created test ID {test.id} with blade 27 having -10mm deviation")
print(f"   Test date: {test.test_date}")
print(f"   Total blades: 28")

db.close()
