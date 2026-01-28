# How the Application Works

## Application Flow

### 1. Launch
- User runs `launch_app.bat` (Windows) or `launch_app.py` (cross-platform)
- Script activates Python virtual environment (`.venv` in root directory)
- Python script starts FastAPI server with uvicorn on port 8000
- Browser automatically opens to `http://localhost:8000`

**Note**: Virtual environment is `.venv` in project root, NOT `backend/env`

### 2. Frontend Interface
- User navigates to main page (`index.html`)
- Interface provides access to tests organized by frequency:
  - Daily tests (Safety Systems, etc.)
  - Weekly tests (MVIC, PIQT, Leaf Position, Helium Level)
  - Monthly tests (Position Table, Laser Alignment, Quasar, Quality Index)
- User clicks test button to start execution
- Upload modal appears requesting DICOM files and operator name

### 3. File Upload & Processing
- Files sent via POST to `/execute/{test_type}`
- **Test Execution Router** (`routers/test_execution.py`) receives request
- DICOM files saved temporarily to `backend/uploads/`
- Service function analyzes DICOM pixel data:
  - Extract image geometry, measure field dimensions
  - Detect blade positions, angles, or intensity values
  - Apply test-specific tolerances and validations
  - Generate visualization images
- Visualization images saved to `frontend/visualizations/{test_type}/`

### 4. Result Generation
- Service returns structured results with:
  - `overall_result`: PASS/FAIL/WARNING
  - `results`: Individual measurements per image/blade
  - `file_results`: Detailed data for display
  - `visualizations`: Image paths and/or base64-encoded plots

### 5. Database Save
- Router calls appropriate database function (e.g., `database.save_mvic_test()`)
- Creates main test record in appropriate table (e.g., `weekly_mvic`)
- Saves individual results to results table (e.g., `weekly_mvic_results`)
- Stores visualization paths in database if images were generated
- Returns test ID to frontend

### 6. Display Results
- Frontend shows results immediately after save
- User can navigate to "Review Tests" page
- Clicks "View Details" for specific test
- Frontend calls `/display/{test_type}/{test_id}`
- **Result Display Router** (`routers/result_display_router.py`) queries database
- Uses display modules (`result_displays/*.py`) to format HTML
- Returns formatted HTML with measurements, pass/fail status, and embedded visualizations

### 7. PDF Report Generation
- User clicks "Generate PDF" button from results page
- Frontend calls `/reports/test/{test_id}` or specialized endpoint
- **Reports Router** (`routers/reports.py`) retrieves test data from database
- Calls report generator (`services/pdf_generators/*`)
- Generates PDF with ReportLab including:
  - Test metadata (date, operator, result)
  - Tables of measurements with pass/fail indicators
  - Embedded visualizations
  - Tolerance limits and statistics
- Returns PDF file for browser download

### 8. Trends & History
- User navigates to trends page or views session history
- Frontend queries session endpoints (e.g., `/piqt-sessions`)
- **Test Sessions Router** (`routers/test_sessions.py`) retrieves historical data
- Retrieves data from database with optional date filtering
- Frontend renders charts showing measurement trends over time using Chart.js

### 9. Configuration Management
- User accesses configuration page
- Frontend calls `/config/mv-center` to get current settings
- **Config Router** (`routers/config_routes.py`) manages system configuration
- User can update MV isocenter coordinates via PUT request
- Configuration stored in database for persistence

## Key Technologies
- **Backend**: FastAPI (Python), SQLAlchemy ORM, SQLite
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Analysis**: NumPy, SciPy, pydicom
- **Visualization**: Matplotlib (backend), Chart.js (frontend)
- **Reports**: ReportLab PDF generation

- Configuration stored in database for persistence

## Router Architecture

The application uses a modular router system with clear separation of concerns:

### Core Routers

1. **test_execution.py** - Main execution endpoint (`/execute/*`)
   - Handles all test execution requests
   - Processes DICOM uploads
   - Coordinates with service layer for analysis
   - Returns results to frontend

2. **test_sessions.py** - Session management (`/*-sessions/*`)
   - GET endpoints to retrieve test history
   - DELETE endpoints to remove tests
   - Handles pagination and filtering
   - Serves data for review pages

3. **result_display_router.py** - Result formatting (`/display/*`)
   - Generates HTML displays for test results
   - Embeds visualizations
   - Formats measurements tables
   - Used by review/detail pages

4. **reports.py** - PDF generation (`/reports/*`, `/leaf-position-*`, `/mlc-*`)
   - Generates downloadable PDF reports
   - Handles trend analysis endpoints
   - Specializes in compliance reports

5. **config_routes.py** - Configuration (`/config/*`)
   - Manages system configuration
   - MV isocenter settings
   - Tolerance values

### Test-Specific Routers

6. **daily_tests.py** - Daily test workflows
   - Safety systems POST and session management
   
7. **weekly_tests.py** - Weekly test workflows
   - Helium level, PIQT, MVIC Fente V2, Leaf Position
   - POST execution and session management

8. **monthly_tests.py** - Monthly test workflows
   - Position table, Laser alignment, Quasar, Quality Index
   - POST execution and session management

9. **mlc_routes.py** - MLC-specific operations
   - MLC test sessions
   - MLC trend analysis

10. **mvic_routes.py** - MVIC-specific operations
    - MVIC test sessions  
    - MVIC trend analysis

11. **basic_tests_routes.py** - Generic test interface (NEEDS TO BE INCLUDED)
    - Alternative execution paths for basic tests
    - Test form schema generation

## Service Layer

The service layer contains the actual analysis logic:

### Analysis Services
- **leaf_pos.py** - MLCBladeAnalyzer class for MLC analysis
- **leaf_position_identifier.py** - Identifies leaf positions in images (Exactitude du MLC)
- **services/weekly/** - Weekly test implementations
- **services/monthly/** - Monthly test implementations  
- **services/daily/** - Daily test implementations
- **services/basic_tests/** - Reusable test components

### Report Generators
- **mlc_blade_report_generator.py** - Specialized MLC blade PDF reports
- **pdf_report_generator.py** - Generic PDF report generation
- **services/pdf_generators/** - Test-specific PDF generators

### Utilities
- **visualization_storage.py** - Manages visualization image storage
- **mv_center_utils.py** - MV isocenter configuration management
- **database_helpers.py** - Database utility functions

## Database Layer

### Database Structure
- **database.py** - SQLAlchemy models and core database operations
- **database/config.py** - Database configuration
- **database/queries.py** - Complex query operations
- **database/*_tests.py** - Test-specific database operations
- **database/weekly_leaf_position_images.py** - Exactitude du MLC (leaf position) image management

### Tables Organization
- Daily tests: `daily_*` tables
- Weekly tests: `weekly_*` tables
- Monthly tests: `monthly_*` tables
- Specialized: `mlc_*`, `mvic_*`, `images` tables

## Key Technologies
- **Backend Framework**: FastAPI (Python) - Modern async web framework
- **ASGI Server**: Uvicorn - High-performance server
- **Database**: SQLite with SQLAlchemy ORM
- **DICOM Processing**: pydicom - Medical image format handling
- **Image Analysis**: OpenCV, NumPy, SciPy - Computer vision and numerical processing
- **Visualization**: Matplotlib - Plot generation (backend)
- **PDF Generation**: ReportLab - Professional PDF reports
- **Frontend**: Vanilla JavaScript, HTML5, CSS3 - No framework dependencies
- **Frontend Charts**: Chart.js - Interactive trend visualization

## Storage Locations
- **Database**: `backend/data/qc_tests.db` (SQLite)
- **DICOM uploads**: `backend/uploads/` (temporary, cleaned periodically)
- **Visualizations**: `frontend/visualizations/{test_type}/` (PNG images)
- **Generated PDFs**: Downloaded directly to user's browser (not stored)
- **Static frontend**: `frontend/` directory

## Current Limitations & Known Issues

1. **Missing Router Registrations**: 
   - `basic_tests_routes` and `test_sessions` routers exist but are not imported/included in main.py
   - This causes 404 errors for `/execute` and some session endpoints
   - **Solution**: Add router imports and `app.include_router()` calls in main.py

2. **Missing Dependencies**:
   - PyPDF2 and reportlab may not be installed in environment
   - Causes import errors in PDF generation
   - **Solution**: Run `pip install -r requirements.txt`

3. **Launch Script Issues**:
   - `launch_app.bat` was looking for `backend/env` but actual venv is `.venv` in root
   - **Fixed**: Updated to use `.venv` and correct paths

4. **Incomplete Test Implementations**:
   - Some tests have placeholders or incomplete analysis logic
   - Error handling varies across test types
   - **Status**: Ongoing development

5. **Frontend-Backend API Mismatch**:
   - Some frontend code expects older API endpoint patterns
   - Configuration loading may fail on some pages
   - **Status**: Requires frontend updates to match current API