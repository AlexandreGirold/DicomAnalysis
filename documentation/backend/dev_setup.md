# Development Setup Guide

## Prerequisites

- **Python 3.13** (or compatible version)
- **Git** (for version control)
- **Text editor/IDE** (VS Code recommended)

## Initial Setup

### 1. Clone Repository
```powershell
git clone <repository-url>
cd DicomAnalysis
```

### 2. Create Virtual Environment
```powershell
cd backend
python -m venv env
```

### 3. Activate Virtual Environment
```powershell
.\env\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Verify Database
Check that `backend/data/qc_tests.db` exists. If missing, it will be created automatically on first run.

## Running the Application

### Development Mode
```powershell
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- `--reload`: Auto-restart on code changes
- Open browser to `http://localhost:8000`

### Production Mode (Hidden Window)
```powershell
# From root directory
python launch_app.py
```
or
```powershell
.\start.ps1
```

### Stop Server
```powershell
.\stop_server.ps1
```
or manually kill Python processes

## Project Structure

```
DicomAnalysis/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database compatibility layer
│   ├── database_helpers.py  # CRUD operations
│   ├── database/            # Database models
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── result_displays/     # Display formatters
│   ├── data/                # SQLite database
│   └── uploads/             # Temporary DICOM storage
├── frontend/
│   ├── index.html           # Main page
│   ├── review.html          # Test history
│   ├── trends.html          # Trend charts
│   ├── js/                  # JavaScript modules
│   └── visualizations/      # Generated images
└── documentation/           # Documentation files
```

## Development Workflow

### Adding a New Test Type
1. Create database model in `backend/database/{frequency}_tests.py`
2. Add save function in `backend/database_helpers.py`
3. Create router endpoint in `backend/routers/{frequency}_tests.py`
4. Add display logic in `backend/result_displays/{test_name}_display.py`
5. Update frontend with new test button in `index.html`

See `GUIDE_AJOUT_TEST.md` for detailed steps.

### Database Changes
- Models use SQLAlchemy ORM
- Database auto-creates tables on startup
- To add columns: modify model, restart server
- No migration system currently (manual SQL if needed)

### Testing DICOM Files
- Place test DICOM files in `backend/uploads/` for debugging
- Use real DICOM files from medical equipment
- Check pydicom compatibility: `pydicom.dcmread(file_path)`

## Common Development Tasks

### View Database
```powershell
sqlite3 backend/data/qc_tests.db
.tables
.schema weekly_mvic
SELECT * FROM weekly_mvic LIMIT 5;
```

### Check Logs
FastAPI logs to console. Add custom logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")
```

### Clear Uploads Folder
```powershell
Remove-Item backend/uploads/* -Force
```

### Reset Database
```powershell
Remove-Item backend/data/qc_tests.db
# Restart server to recreate
```

## Debugging Tips

- Use `--reload` flag for automatic server restart
- Check browser console (F12) for JavaScript errors
- Use `print()` or `logger.info()` in Python code
- Test API endpoints with browser DevTools Network tab
- Use VS Code debugger with FastAPI launch configuration

## IDE Configuration (VS Code)

### Recommended Extensions
- Python (Microsoft)
- Pylance
- Python Debugger
- SQLite Viewer

### Launch Configuration
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

## Dependencies Overview

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **sqlalchemy**: ORM for database
- **pydicom**: DICOM file parsing
- **numpy/scipy**: Numerical analysis
- **matplotlib**: Visualization generation
- **reportlab**: PDF generation
- **pandas**: Data manipulation

## Troubleshooting

**Port 8000 already in use**:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

**Module not found**:
```powershell
pip install -r requirements.txt --upgrade
```

**Database locked**:
- Stop all running instances
- Check no other process is accessing `qc_tests.db`

**DICOM parsing errors**:
- Verify DICOM file validity with `pydicom.dcmread()`
- Check pixel data exists: `ds.pixel_array`
