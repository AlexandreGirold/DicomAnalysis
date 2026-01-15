# How the Application Works

## Application Flow

### 1. Launch
- User double-clicks `launch_app.py` or `start.ps1`
- Python script starts FastAPI server with uvicorn on port 8000
- Process runs
- Browser automatically opens to `http://localhost:8000`

### 2. Frontend Interface
- User selects test type from `index.html` (Daily/Weekly/Monthly)
- Clicks test button (e.g., "MVIC-Champ", "MLC Leaf & Jaw", "PIQT")
- Upload modal appears requesting DICOM files and operator name

### 3. File Upload & Processing
- Files sent via POST to `/api/{frequency}/{test_type}/execute`
- Router (e.g., `routers/weekly_tests.py`) receives request
- DICOM files saved temporarily to `backend/uploads/`
- Visualization images saved to `frontend/visualizations/{test_type}/`
- Service function analyzes DICOM pixel data:
  - Extract image geometry, measure field dimensions
  - Detect blade positions, angles, or intensity values
  - Apply test-specific tolerances and validations

### 4. Result Generation
- Service returns structured results with:
  - `overall_result`: PASS/FAIL/WARNING
  - `results`: Individual measurements per image/blade
  - `file_results`: Detailed data for display
  - `visualizations`: Base64-encoded plots (if applicable)

### 5. Database Save
- Router calls `database_helpers.py` function (e.g., `save_mvic_to_database()`)
- Creates main test record in appropriate table (e.g., `weekly_mvic`)
- Saves individual results to results table (e.g., `weekly_mvic_results`)
- Stores visualization paths if images were generated
- Returns test ID to frontend

### 6. Display Results
- Frontend shows results immediately after save
- User can navigate to "Review Tests" (`review.html`)
- Clicks "View Details" for specific test
- Frontend calls `/api/result_display/{test_type}/{test_id}`
- `result_display_router.py` queries database via `result_displays/*.py`
- Returns formatted HTML with measurements, pass/fail status, and visualizations

### 7. PDF Report Generation
- User clicks "Generate PDF" button from results page
- Frontend calls `/api/reports/{test_type}/{test_id}`
- `routers/reports.py` retrieves test data from database
- Calls `report_generator.py` or specialized generator (e.g., `mlc_blade_report_generator.py`)
- Generates PDF with ReportLab including:
  - Test metadata (date, operator, result)
  - Tables of measurements
  - Embedded visualizations
  - Pass/fail indicators
- Returns PDF file for download

### 8. Trends & History
- User navigates to "Trends" (`trends.html`)
- Frontend queries `/api/tests/{test_type}/history`
- Retrieves historical data from database
- Renders charts showing measurement trends over time

## Key Technologies
- **Backend**: FastAPI (Python), SQLAlchemy ORM, SQLite
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Analysis**: NumPy, SciPy, pydicom
- **Visualization**: Matplotlib (backend), Chart.js (frontend)
- **Reports**: ReportLab PDF generation

## Storage Locations
- **Database**: `backend/data/qc_tests.db` (SQLite)
- **DICOM uploads**: `backend/uploads/` (temporary)
- **Visualizations**: `frontend/visualizations/{test_type}/` (PNG images)
- **Generated PDFs**: Downloaded directly to user's browser


## A lot of code is missing (to be implemented) or not working (some errors for some tests)