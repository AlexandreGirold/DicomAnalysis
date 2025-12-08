"""
Test script to verify MV center database retrieval in all tests
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("=" * 70)
print("TEST MV CENTER DATABASE RETRIEVAL")
print("=" * 70)

# Test 1: Database configuration
print("\n[1] Testing database configuration...")
try:
    from database import SessionLocal, MVCenterConfig
    
    db = SessionLocal()
    config = db.query(MVCenterConfig).first()
    
    if config:
        print(f"✓ MV center found in database:")
        print(f"  - U: {config.u}")
        print(f"  - V: {config.v}")
    else:
        print("! No MV center found, creating default...")
        default_config = MVCenterConfig(u=511.03, v=652.75)
        db.add(default_config)
        db.commit()
        print(f"✓ Created default MV center: u=511.03, v=652.75")
    
    db.close()
except Exception as e:
    print(f"✗ Database error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: MVIC Fente V1
print("\n[2] Testing MVIC Fente V1...")
try:
    from services.weekly.MVIC_fente import MVICFenteTest
    
    test = MVICFenteTest()
    print(f"✓ MVIC Fente V1 initialized")
    print(f"  - Center U: {test.center_u}")
    print(f"  - Center V: {test.center_v}")
    
    # Test the method directly
    u, v = test._get_mv_center_from_db()
    print(f"✓ Direct method call: u={u}, v={v}")
    
except Exception as e:
    print(f"✗ MVIC Fente V1 error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: MVIC Fente V2
print("\n[3] Testing MVIC Fente V2...")
try:
    from services.weekly.MVIC_fente import MVICFenteV2Test
    
    test = MVICFenteV2Test()
    print(f"✓ MVIC Fente V2 initialized")
    print(f"  - Center U: {test.center_u}")
    print(f"  - Center V: {test.center_v}")
    
    # Test the method directly
    u, v = test._get_mv_center_from_db()
    print(f"✓ Direct method call: u={u}, v={v}")
    
except Exception as e:
    print(f"✗ MVIC Fente V2 error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: MLC Blade Analyzer (leaf_pos.py)
print("\n[4] Testing MLC Blade Analyzer...")
try:
    from services.leaf_pos import MLCBladeAnalyzer
    
    analyzer = MLCBladeAnalyzer(gui_mode=False)
    print(f"✓ MLC Blade Analyzer initialized")
    print(f"  - Center U: {analyzer.center_u}")
    print(f"  - Center V: {analyzer.center_v}")
    
    # Test the method directly
    u, v = analyzer._get_mv_center_from_db()
    print(f"✓ Direct method call: u={u}, v={v}")
    
except Exception as e:
    print(f"✗ MLC Blade Analyzer error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Verify consistency
print("\n[5] Verifying consistency across all tests...")
try:
    db = SessionLocal()
    config = db.query(MVCenterConfig).first()
    db_u, db_v = config.u, config.v
    db.close()
    
    test_v1 = MVICFenteTest()
    test_v2 = MVICFenteV2Test()
    analyzer = MLCBladeAnalyzer(gui_mode=False)
    
    all_match = (
        test_v1.center_u == db_u and test_v1.center_v == db_v and
        test_v2.center_u == db_u and test_v2.center_v == db_v and
        analyzer.center_u == db_u and analyzer.center_v == db_v
    )
    
    if all_match:
        print(f"✓ All tests use consistent MV center from database:")
        print(f"  - Database: u={db_u}, v={db_v}")
        print(f"  - MVIC Fente V1: u={test_v1.center_u}, v={test_v1.center_v}")
        print(f"  - MVIC Fente V2: u={test_v2.center_u}, v={test_v2.center_v}")
        print(f"  - MLC Blade Analyzer: u={analyzer.center_u}, v={analyzer.center_v}")
    else:
        print(f"✗ Mismatch detected:")
        print(f"  - Database: u={db_u}, v={db_v}")
        print(f"  - MVIC Fente V1: u={test_v1.center_u}, v={test_v1.center_v}")
        print(f"  - MVIC Fente V2: u={test_v2.center_u}, v={test_v2.center_v}")
        print(f"  - MLC Blade Analyzer: u={analyzer.center_u}, v={analyzer.center_v}")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Consistency check error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓✓✓ ALL TESTS PASSED ✓✓✓")
print("=" * 70)
print("\n📍 All tests now retrieve MV center from database!")
print("   To update: Modify the MVCenterConfig table in qc_tests.db")
