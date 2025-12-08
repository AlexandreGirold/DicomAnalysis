"""
DATABASE QUERY EXAMPLES
=======================
Complete guide for retrieving data from the QC database
"""

from database import (
    SessionLocal, 
    MVCenterConfig,
    MLCLeafJawTest, 
    BladePositions,
    NiveauHeliumTest,
    NiveauHeliumResult,
    MVICTest,
    MVICResult
)
from datetime import datetime, timedelta
from sqlalchemy import desc, func


# =============================================================================
# EXAMPLE 1: Simple Query - Get Single Record
# =============================================================================
def get_mv_center():
    """Retrieve MV center configuration (single record)"""
    db = SessionLocal()
    try:
        # Query the first (and only) MV center configuration
        config = db.query(MVCenterConfig).first()
        
        if config:
            print(f"✓ MV Center: u={config.u}, v={config.v}")
            return config.u, config.v
        else:
            print("✗ No MV center found in database")
            return None, None
    finally:
        db.close()


# =============================================================================
# EXAMPLE 2: Query with Filter - Get Specific Record by ID
# =============================================================================
def get_test_by_id(test_id: int):
    """Retrieve a specific MLC test by ID"""
    db = SessionLocal()
    try:
        # Filter by ID
        test = db.query(MLCLeafJawTest).filter(MLCLeafJawTest.id == test_id).first()
        
        if test:
            print(f"✓ Test ID {test_id}:")
            print(f"  - Date: {test.test_date}")
            print(f"  - Operator: {test.operator}")
            print(f"  - Result: {test.overall_result}")
            return test
        else:
            print(f"✗ No test found with ID {test_id}")
            return None
    finally:
        db.close()


# =============================================================================
# EXAMPLE 3: Query All Records - Get List of Tests
# =============================================================================
def get_all_helium_tests():
    """Retrieve all helium level tests"""
    db = SessionLocal()
    try:
        # Get all records
        tests = db.query(NiveauHeliumTest).all()
        
        print(f"✓ Found {len(tests)} helium tests:")
        for test in tests:
            print(f"  - {test.test_date}: {test.overall_result}")
        
        return tests
    finally:
        db.close()


# =============================================================================
# EXAMPLE 4: Query with Multiple Filters - Date Range
# =============================================================================
def get_tests_in_date_range(start_date: datetime, end_date: datetime):
    """Retrieve MLC tests within a specific date range"""
    db = SessionLocal()
    try:
        # Multiple filter conditions with AND
        tests = db.query(MLCLeafJawTest).filter(
            MLCLeafJawTest.test_date >= start_date,
            MLCLeafJawTest.test_date <= end_date
        ).all()
        
        print(f"✓ Found {len(tests)} tests between {start_date.date()} and {end_date.date()}")
        return tests
    finally:
        db.close()


# =============================================================================
# EXAMPLE 5: Query with ORDER BY - Get Latest Test
# =============================================================================
def get_latest_mvic_test():
    """Get the most recent MVIC test"""
    db = SessionLocal()
    try:
        # Order by date descending, get first result
        latest_test = db.query(MVICTest).order_by(
            desc(MVICTest.test_date)
        ).first()
        
        if latest_test:
            print(f"✓ Latest MVIC test:")
            print(f"  - Date: {latest_test.test_date}")
            print(f"  - Operator: {latest_test.operator}")
            return latest_test
        else:
            print("✗ No MVIC tests found")
            return None
    finally:
        db.close()


# =============================================================================
# EXAMPLE 6: Query with LIMIT - Get Last N Tests
# =============================================================================
def get_last_n_tests(n: int = 5):
    """Get the last N MLC tests"""
    db = SessionLocal()
    try:
        # Order by date descending, limit to N results
        tests = db.query(MLCLeafJawTest).order_by(
            desc(MLCLeafJawTest.test_date)
        ).limit(n).all()
        
        print(f"✓ Last {len(tests)} MLC tests:")
        for test in tests:
            print(f"  - {test.test_date}: {test.overall_result}")
        
        return tests
    finally:
        db.close()


# =============================================================================
# EXAMPLE 7: Query with JOIN - Get Test with Results
# =============================================================================
def get_mvic_test_with_results(test_id: int):
    """Retrieve MVIC test and all its slit results"""
    db = SessionLocal()
    try:
        # Get the main test
        test = db.query(MVICTest).filter(MVICTest.id == test_id).first()
        
        if not test:
            print(f"✗ No test found with ID {test_id}")
            return None, []
        
        # Get all related results
        results = db.query(MVICResult).filter(
            MVICResult.test_id == test_id
        ).all()
        
        print(f"✓ Test ID {test_id} with {len(results)} results:")
        for result in results:
            print(f"  - Result: {result}")
        
        return test, results
    finally:
        db.close()


# =============================================================================
# EXAMPLE 8: Query with Aggregation - Count Tests
# =============================================================================
def count_tests_by_operator():
    """Count how many tests each operator has performed"""
    db = SessionLocal()
    try:
        # Group by operator and count
        results = db.query(
            MLCLeafJawTest.operator,
            func.count(MLCLeafJawTest.id).label('test_count')
        ).group_by(MLCLeafJawTest.operator).all()
        
        print("✓ Tests per operator:")
        for operator, count in results:
            print(f"  - {operator}: {count} tests")
        
        return results
    finally:
        db.close()


# =============================================================================
# EXAMPLE 9: Query with Filter by String Pattern - LIKE
# =============================================================================
def get_tests_by_operator_pattern(pattern: str):
    """Find tests by operator name pattern (e.g., 'Alex%' for names starting with Alex)"""
    db = SessionLocal()
    try:
        # Use like() for pattern matching
        tests = db.query(MLCLeafJawTest).filter(
            MLCLeafJawTest.operator.like(f"%{pattern}%")
        ).all()
        
        print(f"✓ Found {len(tests)} tests with operator matching '{pattern}':")
        for test in tests:
            print(f"  - {test.operator} on {test.test_date}")
        
        return tests
    finally:
        db.close()


# =============================================================================
# EXAMPLE 10: Query with Multiple Conditions - OR
# =============================================================================
def get_failed_or_warning_tests():
    """Retrieve tests that failed or have warnings"""
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        
        # Use or_() for OR conditions
        tests = db.query(MLCLeafJawTest).filter(
            or_(
                MLCLeafJawTest.overall_result == "FAIL",
                MLCLeafJawTest.overall_result == "WARNING"
            )
        ).all()
        
        print(f"✓ Found {len(tests)} tests with issues:")
        for test in tests:
            print(f"  - {test.test_date}: {test.overall_result}")
        
        return tests
    finally:
        db.close()


# =============================================================================
# EXAMPLE 11: Complex Query - Blade Positions for Specific Test
# =============================================================================
def get_blade_positions_for_test(test_id: int, image_id: int):
    """Get all blade positions for a specific test and image"""
    db = SessionLocal()
    try:
        # Query with multiple filters and ordering
        positions = db.query(BladePositions).filter(
            BladePositions.mlc_test_id == test_id,
            BladePositions.image_id == image_id
        ).order_by(
            BladePositions.blade_type,
            BladePositions.leaf_number
        ).all()
        
        print(f"✓ Found {len(positions)} blade positions for test {test_id}, image {image_id}:")
        for pos in positions[:5]:  # Show first 5
            print(f"  - {pos.blade_type} leaf {pos.leaf_number}: position={pos.position:.3f}mm")
        
        return positions
    finally:
        db.close()


# =============================================================================
# EXAMPLE 12: Update Record
# =============================================================================
def update_test_notes(test_id: int, new_notes: str):
    """Update notes for a specific test"""
    db = SessionLocal()
    try:
        # Get the test
        test = db.query(MLCLeafJawTest).filter(MLCLeafJawTest.id == test_id).first()
        
        if test:
            # Update the field
            test.notes = new_notes
            db.commit()
            print(f"✓ Updated notes for test ID {test_id}")
            return True
        else:
            print(f"✗ No test found with ID {test_id}")
            return False
    except Exception as e:
        db.rollback()
        print(f"✗ Error updating test: {e}")
        return False
    finally:
        db.close()


# =============================================================================
# EXAMPLE 13: Create New Record
# =============================================================================
def create_mv_center_if_not_exists(u: float, v: float):
    """Create MV center configuration if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if exists
        config = db.query(MVCenterConfig).first()
        
        if config:
            print(f"✓ MV center already exists: u={config.u}, v={config.v}")
            return config
        else:
            # Create new record
            new_config = MVCenterConfig(u=u, v=v)
            db.add(new_config)
            db.commit()
            db.refresh(new_config)  # Refresh to get ID and defaults
            print(f"✓ Created new MV center: u={u}, v={v}")
            return new_config
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating MV center: {e}")
        return None
    finally:
        db.close()


# =============================================================================
# EXAMPLE 14: Delete Record
# =============================================================================
def delete_test_by_id(test_id: int):
    """Delete a specific test (use with caution!)"""
    db = SessionLocal()
    try:
        # Get the test
        test = db.query(MLCLeafJawTest).filter(MLCLeafJawTest.id == test_id).first()
        
        if test:
            db.delete(test)
            db.commit()
            print(f"✓ Deleted test ID {test_id}")
            return True
        else:
            print(f"✗ No test found with ID {test_id}")
            return False
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting test: {e}")
        return False
    finally:
        db.close()


# =============================================================================
# EXAMPLE 15: Real-World Usage - Get MV Center (from your actual code)
# =============================================================================
def _get_mv_center_from_db():
    """
    Real example from mvic_fente_v2.py
    This is the pattern used in your actual tests
    """
    db = SessionLocal()
    try:
        config = db.query(MVCenterConfig).first()
        if config:
            print(f"[MV-CENTER] Retrieved from database: u={config.u}, v={config.v}")
            return config.u, config.v
        else:
            # Create default if not exists
            print("[MV-CENTER] No config found, creating default values...")
            default_config = MVCenterConfig(u=511.03, v=652.75)
            db.add(default_config)
            db.commit()
            db.refresh(default_config)
            print(f"[MV-CENTER] Created default: u={default_config.u}, v={default_config.v}")
            return default_config.u, default_config.v
    except Exception as e:
        print(f"[MV-CENTER] Error accessing database: {e}")
        print("[MV-CENTER] Using fallback values: u=511.03, v=652.75")
        return 511.03, 652.75
    finally:
        db.close()


# =============================================================================
# RUN EXAMPLES
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE QUERY EXAMPLES")
    print("=" * 70)
    
    # Example 1: Simple query
    print("\n[1] Get MV Center:")
    get_mv_center()
    
    # Example 5: Latest test
    print("\n[2] Get Latest MVIC Test:")
    get_latest_mvic_test()
    
    # Example 6: Last N tests
    print("\n[3] Get Last 5 MLC Tests:")
    get_last_n_tests(5)
    
    # Example 4: Date range
    print("\n[4] Get Tests from Last 30 Days:")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    get_tests_in_date_range(start_date, end_date)
    
    # Example 8: Count by operator
    print("\n[5] Count Tests by Operator:")
    count_tests_by_operator()
    
    # Example 15: Real-world usage
    print("\n[6] Real-World Pattern (from your code):")
    _get_mv_center_from_db()
    
    print("\n" + "=" * 70)
    print("✓ Examples completed!")
    print("=" * 70)
