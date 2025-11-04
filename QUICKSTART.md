# MLC Blade Analysis Web Application - Quick Start Guide

## What Was Built

I've created a complete web application for MLC blade position analysis with the following features:

### ✅ Main Analysis Page (index.html)
- Upload multiple DICOM files via drag & drop or file browser
- Automatic validation that all files are from the same day
- Chronological processing (oldest first)
- Real-time results display with:
  - Summary statistics
  - Visualization images (dropdown selector)
  - Filterable results table
- Automatic saving to database

### ✅ Review Page (review.html)
- Browse all historical tests
- Filter by date range
- View database statistics
- Click any test to see full details
- View visualizations for each test
- Search and filter blade measurements
- Delete unwanted tests

### ✅ Backend (FastAPI)
- `/analyze-batch` - Process multiple DICOM files
- `/tests` - Get all tests (with optional date filtering)
- `/tests/{id}` - Get specific test details
- `/delete/{id}` - Delete a test
- `/visualization/{filename}` - Serve visualization images
- `/database/stats` - Get database statistics

### ✅ Database (SQLite)
- `analysis_tests` table - Test metadata and summaries
- `blade_results` table - Individual blade measurements
- Automatic schema creation
- Full relationship mapping
- No auto-delete (data persists)

## How to Run

### Step 1: Start the Backend
Double-click `start_app.bat` or run:
```bash
cd backend
env\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Open Your Browser
Navigate to: `http://localhost:8000`

### Step 3: Use the Application
1. **Upload Files**: Drag & drop or click to browse
2. **Run Analysis**: Click "🚀 Run Analysis"
3. **View Results**: See summary, visualizations, and detailed measurements
4. **Review History**: Click "Review" to see past tests

## Key Features

### Data Persistence
- All results automatically saved to database
- Data never deleted unless manually requested
- Database location: `backend/data/mlc_analysis.db`

### Validation
- Ensures all uploaded files are from the same day
- Processes files in chronological order (oldest first)
- Extracts DICOM creation timestamps

### Trend Analysis Ready
- Database stores all historical data
- Blade positions tracked over time
- Ready for trend graphs and statistical analysis

## File Structure
```
DicomAnalysis/
├── frontend/
│   ├── index.html        # Main analysis page
│   ├── review.html       # Historical review page
│   ├── styles.css        # Styling
│   ├── app.js            # Main page logic
│   └── review.js         # Review page logic
├── backend/
│   ├── main.py           # FastAPI server
│   ├── database.py       # Database models
│   ├── services/
│   │   └── leaf_pos.py   # Analysis engine
│   └── data/
│       └── mlc_analysis.db  # SQLite database
├── start_app.bat         # Quick start script
└── README.md             # Full documentation
```

## Next Steps

1. **Test the Application**
   - Upload some DICOM files
   - Verify analysis runs correctly
   - Check visualizations display properly

2. **Review Database**
   - Go to Review page
   - Confirm tests are saved
   - Try date filtering

3. **Customize** (Optional)
   - Adjust tolerances in `leaf_pos.py`
   - Modify UI colors in `styles.css`
   - Add custom fields to database

## Troubleshooting

### Backend Won't Start
- Check Python environment is activated
- Verify all dependencies installed
- Check port 8000 is not in use

### Files Not Uploading
- Ensure files are `.dcm` format
- Check all files from same day
- View browser console for errors

### Database Errors
- Delete `backend/data/mlc_analysis.db` to reset
- Restart backend server

## Support
See README.md for full documentation and troubleshooting guide.
