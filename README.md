# MLC Blade Position Analysis Web Application

## Overview
This web application analyzes DICOM files to determine MLC (Multi-Leaf Collimator) blade positions for quality control purposes. It provides:
- Batch analysis of multiple DICOM files from the same day
- Chronological processing (oldest first)
- Visual detection of blade positions
- Database storage for trend analysis
- Review interface for historical data

## Features

### Main Analysis Page (`index.html`)
- **File Upload**: Drag & drop or browse to select multiple DICOM files
- **Validation**: Ensures all files are from the same day
- **Chronological Processing**: Files analyzed in order (oldest to newest)
- **Results Display**:
  - Summary statistics (total blades, OK count, out of tolerance, closed)
  - Visualization dropdown to view detection images
  - Detailed measurement table with filtering
- **Auto-Save**: Results automatically saved to local database

### Review Page (`review.html`)
- **Date Range Filtering**: Filter tests by specific date ranges
- **Database Statistics**: View total tests and measurement count
- **Test Cards**: Browse all historical tests
- **Detailed View**: 
  - Click any test to view full details
  - View visualizations
  - See all blade measurements
  - Filter and search results
- **Delete Tests**: Remove unwanted test data

## Installation

### Prerequisites
- Python 3.8+
- Modern web browser (Chrome, Firefox, Edge)

### Backend Setup
1. Install Python dependencies:
```bash
cd backend
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the backend server:
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### Frontend
No installation needed - the frontend is served by the FastAPI backend.

## Usage

### Running an Analysis

1. **Access the Application**
   - Open your browser to `http://localhost:8000`
   - You'll see the main analysis page

2. **Upload DICOM Files**
   - Drag and drop `.dcm` files into the upload area, OR
   - Click "Select Files" to browse
   - Multiple files can be selected

3. **Run Analysis**
   - Click "🚀 Run Analysis"
   - The system will:
     - Verify all files are from the same day
     - Sort files chronologically (oldest first)
     - Process each file using `leaf_pos.py`
     - Generate visualizations

4. **View Results**
   - **Summary**: See overall statistics
   - **Visualizations**: Select from dropdown to view detection images
   - **Table**: Browse all blade measurements
   - **Filter**: Search by blade pair or status

5. **Save Results**
   - Results are **automatically saved** to the database

### Reviewing Historical Data

1. **Navigate to Review Page**
   - Click "Review" in the navigation

2. **View Database Stats**
   - See total tests, measurements, and date range

3. **Filter Tests**
   - Select start/end dates to filter
   - Click "🔍 Filter"
   - Click "🗑️ Clear" to reset

4. **View Test Details**
   - Click any test card
   - Detailed view shows:
     - Test metadata
     - Summary statistics
     - Visualizations
     - All blade measurements

5. **Delete Tests**
   - Open test details
   - Click "🗑️ Delete Test"
   - Confirm deletion

## File Structure
```
DicomAnalysis/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── database.py          # Database models and functions
│   ├── requirements.txt     # Python dependencies
│   ├── services/
│   │   └── leaf_pos.py      # MLC blade analysis logic
│   ├── data/
│   │   └── mlc_analysis.db  # SQLite database
│   └── uploads/             # Temporary file storage
│
├── frontend/
│   ├── index.html           # Main analysis page
│   ├── review.html          # Review/history page
│   ├── styles.css           # Shared styles
│   ├── app.js               # Main page JavaScript
│   └── review.js            # Review page JavaScript
│
└── README.md                # This file
```

## Support
For issues or questions, contact your system administrator.
For Curie

cd c:\Users\agirold\Desktop\DicomAnalysis\backend
.\env\Scripts\Activate.ps1
pip install -r requirements.txt


Package	Purpose	Needed?
fastapi	Web framework for building REST API	✅ YES - Core backend
uvicorn	ASGI server to run FastAPI	✅ YES - Required to run the app
pydicom	Read and parse DICOM medical image files	✅ YES - Core functionality
opencv-python	Image processing (filters, analysis, transformations)	✅ YES - Analyze DICOM images
numpy	Numerical computing, array operations	✅ YES - Required by OpenCV & image processing
pillow	Image manipulation (resize, convert formats)	✅ YES - Display/convert images
sqlalchemy	ORM for SQLite database operations	✅ YES - Store analysis results
python-multipart	Handle file uploads in FastAPI	✅ YES - Upload DICOM files via form
pydantic	Data validation for API requests/responses	✅ YES - Validate input data

api/dicom.py (endpoint receives file)
    ↓
services/dicom_service.py (reads DICOM file)
    ↓
services/preprocessing_service.py (preprocessing: normalize, resize, denoise, etc.)
    ↓
services/analysis_service.py (run analysis on preprocessed image)
    ↓
database.py (store results)