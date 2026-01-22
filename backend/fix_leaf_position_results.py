"""
Fix overall_result for existing LeafPosition tests
Sets overall_result to PASS if no blades are out of tolerance
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal
from database.weekly_tests import LeafPositionTest, LeafPositionResult

db = SessionLocal()

try:
    # Get all leaf position tests
    tests = db.query(LeafPositionTest).all()
    print(f"Found {len(tests)} LeafPosition tests")
    print("=" * 80)
    
    updated_count = 0
    
    for test in tests:
        # Count out of tolerance blades for this test
        out_of_tolerance_count = db.query(LeafPositionResult).filter(
            LeafPositionResult.test_id == test.id,
            LeafPositionResult.is_valid == 'OUT_OF_TOLERANCE'
        ).count()
        
        total_blades = db.query(LeafPositionResult).filter(
            LeafPositionResult.test_id == test.id
        ).count()
        
        ok_blades = db.query(LeafPositionResult).filter(
            LeafPositionResult.test_id == test.id,
            LeafPositionResult.is_valid == 'OK'
        ).count()
        
        # Determine correct overall result
        correct_result = "PASS" if out_of_tolerance_count == 0 else "FAIL"
        
        print(f"\nTest ID {test.id}:")
        print(f"  Current overall_result: {test.overall_result}")
        print(f"  Total blades: {total_blades}")
        print(f"  OK blades: {ok_blades}")
        print(f"  Out of tolerance: {out_of_tolerance_count}")
        print(f"  Should be: {correct_result}")
        
        if test.overall_result != correct_result:
            print(f"  ⚠️  UPDATING from {test.overall_result} to {correct_result}")
            test.overall_result = correct_result
            updated_count += 1
        else:
            print(f"  ✓ Already correct")
    
    # Commit changes
    if updated_count > 0:
        db.commit()
        print(f"\n{'=' * 80}")
        print(f"✅ Updated {updated_count} test(s)")
    else:
        print(f"\n{'=' * 80}")
        print(f"ℹ️  No updates needed - all tests have correct overall_result")
        
finally:
    db.close()
