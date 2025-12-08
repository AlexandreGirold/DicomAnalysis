# Database Module

Modular database structure for Quality Control tests.

## Structure

```
database/
├── __init__.py          # Main entry point, exports all models
├── config.py            # Database configuration & SQLAlchemy setup
├── daily_tests.py       # Daily QC test models
├── weekly_tests.py      # Weekly QC test models
├── monthly_tests.py     # Monthly QC test models
└── mlc_curie.py        # MLC Curie test models & configuration
```

## Usage

Import from the database package as before:

```python
from database import SessionLocal, MVCenterConfig, MLCLeafJawTest
```

All imports work exactly the same way - the refactoring is transparent to existing code.

## Adding New Tests

1. Choose the appropriate file based on test frequency:
   - `daily_tests.py` - Daily tests
   - `weekly_tests.py` - Weekly tests
   - `monthly_tests.py` - Monthly tests
   - `mlc_curie.py` - MLC-specific tests

2. Create your model class:
```python
class NewTest(Base):
    __tablename__ = "frequency_test_name"
    
    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
```

3. Export it in `__init__.py`:
```python
from .weekly_tests import NewTest

__all__ = [
    # ... existing exports
    'NewTest',
]
```

4. Restart the application - SQLAlchemy auto-creates the table.

## Benefits

- **Organized**: Each file has a clear purpose
- **Maintainable**: Easier to find and modify specific tests
- **Scalable**: Add new tests without cluttering a single file
- **Readable**: Shorter files are easier to understand
