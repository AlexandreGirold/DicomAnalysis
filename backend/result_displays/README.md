# Result Display System

This folder contains modules for retrieving and formatting saved test results from the database for display.

## Overview

The result display system provides a clean way to:
1. Retrieve test results from the database
2. Format data matching the original test execution output
3. Serve formatted results via API endpoints
4. Display results in a user-friendly web interface

## Structure

```
result_displays/
├── __init__.py              # Package initialization
├── piqt_display.py          # PIQT test result display
└── [other test displays]    # Future: MLC, MVIC, etc.
```

## Architecture

### Backend Components

1. **Display Modules** (`result_displays/*.py`)
   - Retrieve test data from database
   - Format data for display
   - Organize results by category
   - Return JSON-compatible structures

2. **API Router** (`routers/result_display_router.py`)
   - Endpoints for retrieving formatted test results
   - RESTful API following pattern: `/display/{test_type}/{test_id}`

3. **Database Queries** (existing in `database/queries.py`)
   - Already provides `get_*_test_by_id()` functions
   - Used by display modules to retrieve data

### Frontend Components

1. **Display Pages** (`frontend/*_display.html`)
   - Interactive result viewers
   - Test selection from database
   - Formatted data presentation
   - Match original test visualizations

## PIQT Display Example

### Backend Usage

```python
from result_displays.piqt_display import display_piqt_result

# Get formatted result for test ID 1
result = display_piqt_result(1)

# Result structure:
{
    'test_id': 1,
    'test_name': 'PIQT - Philips Image Quality Test',
    'test_date': '2025-12-11T10:30:00',
    'operator': 'John Doe',
    'overall_result': 'PASS',
    'summary': {
        'snr_value': 45.2,
        'uniformity_value': 2.1,
        'ghosting_value': 0.5
    },
    'detailed_results': {
        'flood_field_uniformity': {...},
        'spatial_linearity': {...},
        'slice_profile': {...},
        'spatial_resolution': {...}
    },
    'results': [
        {'name': 'SNR Value', 'value': 45.2, 'unit': '', 'status': 'INFO'},
        ...
    ]
}
```

### API Endpoints

**Get PIQT Test Display**
```
GET /display/piqt/{test_id}

Response: Formatted test result (JSON)
```

**List PIQT Tests**
```
GET /display/piqt?limit=10&offset=0

Response: List of available tests
```

### Frontend Usage

1. **Direct Link**: `piqt_display.html?id=1`
2. **Test Selector**: Choose from dropdown of available tests
3. **Navigation**: Link from review page

## Adding New Test Displays

To add a display module for a new test type:

### 1. Create Display Module

```python
# result_displays/my_test_display.py

from database import get_my_test_by_id
from database.config import SessionLocal
from database.weekly_tests import MyTest

def display_my_test_result(test_id: int):
    """Retrieve and format MyTest result"""
    session = SessionLocal()
    try:
        test = session.query(MyTest).filter(MyTest.id == test_id).first()
        
        if not test:
            return None
        
        return {
            'test_id': test.id,
            'test_name': 'My Test Name',
            'test_date': test.test_date.isoformat(),
            'operator': test.operator,
            'overall_result': test.overall_result,
            # Add test-specific data
            'summary': {...},
            'results': [...],
            'visualizations': [...]
        }
    finally:
        session.close()
```

### 2. Add Router Endpoint

```python
# routers/result_display_router.py

from result_displays.my_test_display import display_my_test_result

@router.get("/display/my-test/{test_id}")
async def get_my_test_display(test_id: int):
    result = display_my_test_result(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test not found")
    return JSONResponse(result)
```

### 3. Create Frontend Page

Create `frontend/my_test_display.html` following the pattern in `piqt_display.html`:
- Test selector dropdown
- Metadata display
- Summary cards
- Detailed results tables
- Original test visualizations (if applicable)

### 4. Update Package

```python
# result_displays/__init__.py

from .my_test_display import display_my_test_result

__all__ = ['display_piqt_result', 'display_my_test_result']
```

## Design Principles

1. **Match Original Output**: Display should closely match the original test execution format
2. **Reuse Visualizations**: Use the same visualization code when possible
3. **Clean Separation**: Keep display logic separate from test execution logic
4. **Consistent API**: Follow RESTful patterns for all endpoints
5. **User-Friendly**: Frontend should be intuitive and easy to navigate

## Features

- ✅ Retrieve saved test results from database
- ✅ Format data matching original test output
- ✅ RESTful API endpoints
- ✅ Interactive web interface
- ✅ Test selection and navigation
- ⏳ Visualization recreation (images, plots)
- ⏳ Comparison between multiple tests
- ⏳ Export results (PDF, CSV)

## Next Steps

1. Add display modules for other test types:
   - MLC Leaf & Jaw Test
   - MVIC Test (5 images)
   - MVIC Fente V2
   - Niveau Helium
   - Daily/Monthly tests

2. Enhance visualizations:
   - Recreate original test plots
   - Store and retrieve images from test execution
   - Interactive charts and graphs

3. Add comparison features:
   - Compare multiple test results
   - Trend analysis over time
   - Statistical summaries

4. Export capabilities:
   - PDF report generation
   - CSV data export
   - Print-friendly formats
