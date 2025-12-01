# Guide: Adding New Tests to the Database

This guide explains how to add new test types to the Quality Control database.

## Database Structure Overview

The database is organized by test frequency:

- **Daily Tests**: `DailySafetySystemsTest`
- **Weekly Tests**: `WeeklyNiveauHeliumTest`, `WeeklyMLCLeafJawTest`, `WeeklyMVICTest`, `WeeklyPIQTTest`
- **Monthly Tests**: `MonthlyPositionTableV2Test`, `MonthlyAlignementLaserTest`, `MonthlyQuasarTest`, `MonthlyIndiceQualityTest`

## How to Add a New Test

### Step 1: Add Table Class in `database.py`

Add a new class to the appropriate section (Daily/Weekly/Monthly):

```python
class WeeklyNewTest(Base):
    """Weekly New Test Description"""
    __tablename__ = "weekly_new_test"
    
    # Required fields for all tests
    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Add your specific test measurements here
    measurement_1 = Column(Float, nullable=False)
    measurement_2 = Column(Float, nullable=True)  # Optional field
    
    # Required fields for all tests
    overall_result = Column(String, nullable=False)  # PASS/FAIL/WARNING
    notes = Column(Text, nullable=True)
```

### Step 2: Restart the Application

The database will automatically create the new table on startup via `init_db()`:

```bash
cd backend
.\env\Scripts\Activate.ps1
uvicorn main:app --reload
```

You should see: `✓ Database initialized at: backend\data\qc_tests.db`

### Step 3: Add CRUD Functions (Optional)

Add helper functions in `database.py` if needed:

```python
def save_weekly_new_test(test_date, operator, measurement_1, overall_result, notes=""):
    """Save a new test to the database"""
    db = SessionLocal()
    try:
        test = WeeklyNewTest(
            test_date=test_date,
            operator=operator,
            measurement_1=measurement_1,
            overall_result=overall_result,
            notes=notes
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        return test.id
    finally:
        db.close()

def get_weekly_new_tests():
    """Get all tests from the database"""
    db = SessionLocal()
    try:
        tests = db.query(WeeklyNewTest).order_by(WeeklyNewTest.test_date.desc()).all()
        return [{
            'id': test.id,
            'test_date': test.test_date.isoformat(),
            'operator': test.operator,
            'measurement_1': test.measurement_1,
            'overall_result': test.overall_result,
            'notes': test.notes
        } for test in tests]
    finally:
        db.close()
```

### Step 4: Add API Endpoint in `main.py`

```python
@app.post("/weekly-new-test")
async def create_weekly_new_test(data: dict):
    from datetime import datetime
    from backend.database import save_weekly_new_test
    
    test_id = save_weekly_new_test(
        test_date=datetime.fromisoformat(data['test_date']),
        operator=data['operator'],
        measurement_1=data['measurement_1'],
        overall_result=data['overall_result'],
        notes=data.get('notes', '')
    )
    
    return {"success": True, "test_id": test_id}

@app.get("/weekly-new-test")
async def get_weekly_new_tests():
    from backend.database import get_weekly_new_tests
    return get_weekly_new_tests()
```

## Common Patterns

### Required Fields (All Tests)
- `id` - Auto-increment primary key
- `test_date` - When the test was performed
- `operator` - Who performed the test
- `upload_date` - When saved to database
- `overall_result` - PASS/FAIL/WARNING
- `notes` - Optional text notes

### Measurement Fields
- Use `Float` for numeric measurements
- Use `String` for status/enum values (PASS/FAIL)
- Use `Text` for long text content
- Set `nullable=True` for optional fields
- Set `nullable=False` for required fields

### Naming Convention
- Table names: `{frequency}_{test_name}` (lowercase with underscores)
- Class names: `{Frequency}{TestName}Test` (PascalCase)

## Example: Adding Monthly Gating Test

```python
class MonthlyGatingTest(Base):
    """Monthly Gating System Test"""
    __tablename__ = "monthly_gating"
    
    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Gating-specific measurements
    amplitude_mm = Column(Float, nullable=False)
    frequency_hz = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=False)
    
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
```

That's it! The database is persistent - existing data is never deleted, and new tables are automatically created.
