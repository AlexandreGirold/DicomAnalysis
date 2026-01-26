# API Endpoints Reference

Base URL: `http://localhost:8000`

## Overview

The backend API is organized into the following router modules:
- **Test Execution**: Execute quality control tests
- **Test Sessions**: Retrieve and delete test history
- **Result Display**: Get formatted HTML results for display
- **Reports**: Generate PDF reports
- **Configuration**: Manage system configuration
- **Daily Tests**: Daily QC test workflows
- **Weekly Tests**: Weekly QC test workflows  
- **Monthly Tests**: Monthly QC test workflows
- **MLC Routes**: MLC-specific operations
- **MVIC Routes**: MVIC-specific operations

## Test Execution Endpoints

### List Available Tests
```
GET /execute
```
**Returns**: JSON list of all available test types with metadata

### Get Test Form Schema
```
GET /execute/{test_id}/form
```
**Parameters**:
- `test_id`: Test identifier (e.g., "piqt", "mvic", "mlc-leaf-jaw")

**Returns**: JSON schema for test form fields

### Execute Tests

All execution endpoints accept multipart/form-data:

#### Weekly Tests
```
POST /execute/niveau-helium
POST /execute/piqt
POST /execute/mvic
POST /execute/mvic-fente-v2
POST /execute/leaf-position
```

#### Monthly Tests
```
POST /execute/position-table-v2
POST /execute/alignement-laser
POST /execute/quasar
POST /execute/indice-quality
```

#### Daily Tests
```
POST /execute/safety-systems
```

#### MLC Tests
```
POST /execute/mlc-leaf-jaw
POST /execute/mlc-leaf-jaw-debug
```

#### Generic Execution
```
POST /execute/{test_id}
```

**Form Data** (common fields):
- `files`: DICOM files (multipart/form-data) - required
- `operator`: Operator name (string) - required
- `notes`: Optional notes (string)
- Additional test-specific fields

**Response**: 
```json
{
  "test_id": 123,
  "overall_result": "PASS",
  "results": [...],
  "message": "Test saved successfully",
  "visualizations": [...]
}
```

## Test Session Management

### Daily Test Sessions

#### Safety Systems
```
GET /safety-systems-sessions
GET /safety-systems-sessions/{test_id}
DELETE /safety-systems-sessions/{test_id}
```

#### Niveau Helium (Helium Level)
```
GET /niveau-helium-sessions
GET /niveau-helium-sessions/{test_id}
DELETE /niveau-helium-sessions/{test_id}
```

### Weekly Test Sessions

#### MVIC Fente V2
```
GET /mvic-fente-v2-sessions
GET /mvic-fente-v2-sessions/{test_id}
DELETE /mvic-fente-v2-sessions/{test_id}
```

#### PIQT (Picket Fence)
```
GET /piqt-sessions
GET /piqt-sessions/{test_id}
DELETE /piqt-sessions/{test_id}
```

#### Leaf Position
```
GET /leaf-position-sessions
GET /leaf-position-sessions/{test_id}
DELETE /leaf-position-sessions/{test_id}
```

### Monthly Test Sessions

#### Position Table
```
GET /position-table-sessions
GET /position-table-sessions/{test_id}
DELETE /position-table-sessions/{test_id}
```

#### Alignement Laser
```
GET /alignement-laser-sessions
GET /alignement-laser-sessions/{test_id}
DELETE /alignement-laser-sessions/{test_id}
```

#### Quasar
```
GET /quasar-sessions
GET /quasar-sessions/{test_id}
DELETE /quasar-sessions/{test_id}
```

#### Indice Quality
```
GET /indice-quality-sessions
GET /indice-quality-sessions/{test_id}
DELETE /indice-quality-sessions/{test_id}
```

### MLC Test Sessions
```
GET /mlc-test-sessions
GET /mlc-test-sessions/{test_id}
POST /mlc-test-sessions
DELETE /mlc-test-sessions/{test_id}
```

### MVIC Test Sessions
```
GET /mvic-test-sessions
GET /mvic-test-sessions/{test_id}
POST /mvic-test-sessions
DELETE /mvic-test-sessions/{test_id}
```

**Query Parameters** (for GET list endpoints):
- `limit`: Max number of records (default: 100)
- `offset`: Pagination offset (default: 0)
- `start_date`: Filter from date (ISO format)
- `end_date`: Filter to date (ISO format)

**Response** (list):
```json
{
  "tests": [...],
  "count": 50
}
```

## Result Display Endpoints

Get formatted HTML for displaying test results in frontend:

```
GET /display/piqt/{test_id}
GET /display/piqt (recent tests)
GET /display/mlc/{test_id}
GET /display/mlc (recent tests)
GET /display/mvic/{test_id}
GET /display/mvic (recent tests)
GET /display/mvic-fente-v2/{test_id}
GET /display/mvic-fente-v2 (recent tests)
GET /display/niveau-helium/{test_id}
GET /display/niveau-helium (recent tests)
```

**Returns**: HTML string with embedded visualizations and formatted measurements

## Reports & Trends

### Leaf Position Debug
```
GET /leaf-position-debug
```
**Returns**: Debugging information for leaf position analysis

### Leaf Position Trend
```
GET /leaf-position-trend
```
**Returns**: Historical trend data for leaf position measurements

### MLC Blade Compliance Report
```
POST /mlc-blade-compliance
```
**Body**: JSON with test selection criteria
**Returns**: Comprehensive PDF report with blade compliance over time

### MLC Trend Analysis
```
GET /mlc-trend/{parameter}
```
**Parameters**:
- `parameter`: Measurement parameter (e.g., "blade_01", "blade_02")

**Returns**: Trend data for specific MLC parameter

```
GET /mlc-reports/trend
```
**Returns**: Overall MLC trend report data

### MVIC Trend Analysis
```
GET /mvic-trend/{parameter}
```
**Parameters**:
- `parameter`: Measurement parameter

**Returns**: Trend data for specific MVIC parameter

## Configuration

### MV Isocenter Configuration
```
GET /config/mv-center
```
**Returns**: 
```json
{
  "u": 512.5,
  "v": 384.0
}
```

```
PUT /config/mv-center
```
**Body**:
```json
{
  "u": 512.5,
  "v": 384.0
}
```
**Returns**: Confirmation message

## Legacy Analysis Endpoints (main.py)

### Root
```
GET /
```
**Returns**: Main frontend page (index.html) or API info

### Batch Analysis
```
POST /analyze-batch
```
Upload multiple DICOM files for batch analysis using MLCBladeAnalyzer

**Form Data**:
- `files`: Multiple DICOM files

**Returns**: Analysis results with blade positions and measurements

### Single File Analysis
```
POST /analyze
```
Upload single DICOM file for analysis

**Form Data**:
- `file`: Single DICOM file

**Returns**: Analysis results

### Get Visualization
```
GET /visualization/{filename:path}
```
**Parameters**:
- `filename`: Path to visualization image

**Returns**: PNG image file

### Get All Tests
```
GET /tests
```
**Returns**: List of all test sessions across all types

### Get Specific Test
```
GET /tests/{test_id}
```
**Returns**: Detailed test information

### Get Blade Trend
```
GET /blade-trend/{blade_pair}
```
**Parameters**:
- `blade_pair`: Blade pair identifier (e.g., "01", "02")

**Returns**: Historical trend data for specific blade pair

### Delete Test
```
DELETE /tests/{test_id}
```
**Returns**: Confirmation message

### Database Statistics
```
GET /database/stats
```
**Returns**: Database statistics (total tests, date ranges, etc.)

### Generate Test Report
```
GET /reports/test/{test_id}
```
**Returns**: PDF report for specific test

## Common Response Codes

- **200**: Success
- **201**: Created (test session saved)
- **400**: Bad request (missing files, invalid parameters)
- **404**: Test not found
- **500**: Server error (analysis failure, database error)

## File Upload Requirements

- **Format**: DICOM (.dcm) files only
- **Content-Type**: multipart/form-data
- **Field Name**: `files` (can be single or multiple)
- **Max Size**: Configured in FastAPI (default: unlimited)
- **Number of Files**: Varies by test type
  - MVIC: 5 files required
  - MLC Leaf & Jaw: 1-2 files
  - Leaf Position: 1-3 files  
  - PIQT: 1 file
  - Safety Systems: Variable
  - Position Table: Multiple files
  - Quasar: Multiple files

## Test Result Structure

Standard test result response:
```json
{
  "test_id": 123,
  "overall_result": "PASS" | "FAIL" | "WARNING",
  "test_date": "2026-01-19T10:30:00",
  "operator": "John Doe",
  "notes": "Optional notes",
  "results": [
    {
      "measurement": "Field Width X",
      "value": 10.05,
      "tolerance": 0.2,
      "status": "PASS",
      "unit": "mm"
    }
  ],
  "visualizations": [
    {
      "title": "Field Detection",
      "path": "/visualizations/mvic/test_123_field.png",
      "base64": "iVBORw0KG..." // Optional
    }
  ],
  "metadata": {
    "analysis_duration": 2.5,
    "file_count": 5,
    "dicom_metadata": {...}
  }
}
```

## Authentication & Security

- **Current Status**: No authentication required
- **CORS**: Enabled for all origins (`allow_origins=["*"]`)
- **Future**: Consider implementing API key or OAuth2 authentication

## Static Files

Frontend is served via mounted static directory at `/static/*`

## Database

- **Type**: SQLite
- **Location**: `backend/data/qc_tests.db`
- **ORM**: SQLAlchemy
- **Tables**: Daily, Weekly, Monthly test tables plus MLC and MVIC specific tables

## Error Handling

All endpoints return consistent error format:
```json
{
  "detail": "Error message"
}
```

## Development Notes

- Server runs with auto-reload (`--reload` flag)
- Logs output to console (INFO level)
- Temporary uploads stored in `backend/uploads/`
- Visualizations saved to `frontend/visualizations/{test_type}/`
- **Important**: `basic_tests_routes` and `test_sessions` routers must be imported and included in main.py for full functionality
