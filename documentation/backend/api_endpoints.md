# API Endpoints Reference

Base URL: `http://localhost:8000`

## Test Execution

### Execute Daily Test
```
POST /api/daily/{test_type}/execute
```
**Test Types**: `safety_systems`

**Form Data**:
- `files`: DICOM files (multipart/form-data)
- `operator`: Operator name (string)
- Additional fields depending on test type

**Response**: 
```json
{
  "test_id": 123,
  "overall_result": "PASS",
  "results": [...],
  "message": "Test saved successfully"
}
```

### Execute Weekly Test
```
POST /api/weekly/{test_type}/execute
```
**Test Types**: `mvic`, `mvic_fente_v2`, `mlc`, `leaf_position`, `piqt`, `niveau_helium`

**Form Data**:
- `files`: DICOM files (multipart/form-data)
- `operator`: Operator name (string)
- `notes`: Optional notes (string)

**Response**: Same as daily test

### Execute Monthly Test
```
POST /api/monthly/{test_type}/execute
```
**Test Types**: `position_table_v2`, `alignement_laser`, `quasar`, `indice_quality`

**Form Data**: Same as weekly test

## Test Results Display

### Get Test Result Details
```
GET /api/result_display/{test_type}/{test_id}
```
**Returns**: Formatted HTML with test measurements and visualizations

### Get Test History
```
GET /api/tests/{test_type}/history?limit=50
```
**Query Params**:
- `limit`: Number of recent tests (default: 50)

**Response**:
```json
[
  {
    "id": 123,
    "test_date": "2026-01-05T10:30:00",
    "operator": "John Doe",
    "overall_result": "PASS",
    ...
  }
]
```

### Get Trend Data
```
GET /api/tests/{test_type}/trends?days=30
```
**Query Params**:
- `days`: Number of days to retrieve (default: 30)

**Response**: Array of test measurements over time

## PDF Reports

### Generate Test Report
```
GET /api/reports/{test_type}/{test_id}
```
**Returns**: PDF file download

### Generate MLC Blade Report
```
GET /api/reports/mlc_blade/{test_id}
```
**Returns**: Detailed MLC blade compliance PDF

## Configuration

### Get Test Configuration
```
GET /api/config/{test_type}
```
**Returns**: Test-specific tolerance values and settings

### Update Test Configuration
```
POST /api/config/{test_type}
```
**Body**: JSON with configuration parameters

## Common Response Codes

- **200**: Success
- **400**: Bad request (missing files, invalid parameters)
- **404**: Test not found
- **500**: Server error (analysis failure, database error)

## File Upload Requirements

- **Format**: DICOM (.dcm)
- **Max Size**: Configured in FastAPI (default: unlimited)
- **Number of Files**: Varies by test type
  - MVIC: 5 files
  - MLC: 1-2 files
  - Leaf Position: 1-3 files
  - PIQT: 1 file

## Authentication

Currently no authentication required. All endpoints are open access.
