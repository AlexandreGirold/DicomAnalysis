# Leaf Position Test - Database Integration Summary

## Overview
Successfully added complete database support for the Leaf Position test, storing detailed blade measurements including positions, lengths, and validation status.

## Database Schema

### Main Test Table: `weekly_leaf_position`
Stores high-level test information:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| test_date | DATETIME | Date of the test |
| operator | VARCHAR | Operator name |
| upload_date | DATETIME | When test was saved |
| overall_result | VARCHAR | PASS/FAIL/WARNING |
| notes | TEXT | Optional notes |
| filenames | TEXT | Comma-separated DICOM filenames |
| visualization_paths | TEXT | JSON array of visualization paths |
| file_results | TEXT | JSON summary data |

### Blade Results Table: `weekly_leaf_position_results`
Stores individual blade measurements (one row per blade per image):

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| test_id | INTEGER | Foreign key to weekly_leaf_position |
| image_number | INTEGER | Which DICOM file (1, 2, 3...) |
| filename | VARCHAR | DICOM filename |
| blade_pair | INTEGER | Blade pair number (27-54) |
| position_u_px | FLOAT | Horizontal position in pixels |
| v_sup_px | FLOAT | Top edge V coordinate (pixels) |
| v_inf_px | FLOAT | Bottom edge V coordinate (pixels) |
| distance_sup_mm | FLOAT | Distance from center to top (mm) |
| distance_inf_mm | FLOAT | Distance from center to bottom (mm) |
| length_mm | FLOAT | Total blade length (mm) |
| field_size_mm | FLOAT | Detected field size (mm) |
| is_valid | VARCHAR | OK / OUT_OF_TOLERANCE / CLOSED |
| status_message | TEXT | Detailed status information |

## Code Components

### 1. Database Models
**File**: `backend/database/weekly_tests.py`
- Added `LeafPositionTest` class (lines 243-256)
- Added `LeafPositionResult` class (lines 259-281)

### 2. Database Helper Functions
**File**: `backend/database_helpers.py`
- Added `save_leaf_position_to_database()` function (lines 235-320)
- Handles saving main test record and all blade results
- Automatically extracts blade data from test results

### 3. Query Functions
**File**: `backend/database/queries.py`
- `get_all_leaf_position_tests()` - Retrieve all tests with blade results
- `get_leaf_position_test_by_id()` - Get specific test by ID
- `delete_leaf_position_test()` - Delete test and associated blade results

### 4. API Endpoints
**File**: `backend/routers/weekly_tests.py`
- `GET /weekly/leaf-position-sessions` - List all tests
- `GET /weekly/leaf-position-sessions/{test_id}` - Get specific test
- `DELETE /weekly/leaf-position-sessions/{test_id}` - Delete test

### 5. Test Execution with Auto-Save
**File**: `backend/routers/test_execution.py`
- Updated `POST /execute/leaf-position` endpoint
- Automatically saves to database after test execution
- Returns `test_id` in response

## Data Flow

1. **Test Execution**:
   ```
   User uploads DICOM files → execute_leaf_position endpoint
   → LeafPositionTest.execute() → MLCBladeAnalyzer.process_image()
   ```

2. **Data Extraction**:
   ```
   Test results → Extract blade data for each image
   → Format as list of dictionaries with blade measurements
   ```

3. **Database Saving**:
   ```
   save_leaf_position_to_database()
   → Create LeafPositionTest record
   → Create LeafPositionResult records (one per blade)
   → Commit transaction
   ```

4. **Data Retrieval**:
   ```
   GET /weekly/leaf-position-sessions
   → get_all_leaf_position_tests()
   → Return tests with blade_results array
   ```

## Example Data Structure

### Saved Blade Result:
```json
{
  "image_number": 1,
  "filename": "RTI00348.dcm",
  "blade_pair": 27,
  "position_u_px": 512.5,
  "v_sup_px": 450.2,
  "v_inf_px": 490.8,
  "distance_sup_mm": 10.1,
  "distance_inf_mm": 9.9,
  "length_mm": 20.0,
  "field_size_mm": 20.0,
  "is_valid": "OK",
  "status_message": "[RTI00348.dcm] Blade 27: Length=20.00mm, Top=10.10mm, Bottom=9.90mm, Status=OK"
}
```

## Migration

**File**: `backend/database/migrate_add_leaf_position.py`
- Creates both tables in the database
- Run with: `python -m database.migrate_add_leaf_position`
- ✅ Successfully executed - tables created

## Testing

**File**: `backend/database/test_leaf_position_db.py`
- Verifies table creation
- Tests query functions
- Validates table structure
- ✅ All tests passed

## Validation Logic

Blade results are validated against three acceptable field sizes:
- **20mm** ± 1mm tolerance
- **30mm** ± 1mm tolerance  
- **40mm** ± 1mm tolerance

Status values:
- **OK**: Field size within ±1mm of 20, 30, or 40mm
- **OUT_OF_TOLERANCE**: Field size outside acceptable ranges
- **CLOSED**: Blade pair detected as closed (no opening)

## Usage Example

### Execute Test and Save:
```python
# Frontend sends DICOM files to:
POST /execute/leaf-position

# Response includes test_id:
{
  "overall_result": "PASS",
  "test_id": 123,
  "results": {...},
  "visualizations": [...]
}
```

### Retrieve Saved Test:
```python
# Get specific test with all blade results:
GET /weekly/leaf-position-sessions/123

# Returns:
{
  "id": 123,
  "operator": "John Doe",
  "test_date": "2025-12-17T10:30:00",
  "overall_result": "PASS",
  "filenames": "RTI00348.dcm,RTI00349.dcm",
  "blade_results": [
    {
      "blade_pair": 27,
      "length_mm": 20.0,
      "is_valid": "OK",
      ...
    },
    ...
  ]
}
```

## Benefits

1. **Complete Audit Trail**: Every blade measurement is stored permanently
2. **Historical Analysis**: Compare blade performance over time
3. **Quality Trends**: Track which blades frequently go out of tolerance
4. **Detailed Reports**: Generate comprehensive reports from stored data
5. **Data Integrity**: Foreign key relationships ensure data consistency
6. **Flexible Queries**: Easy to filter by date, operator, blade number, etc.

## Next Steps (Optional Enhancements)

1. Add visualization storage (save PNG files to disk)
2. Create blade-specific trend analysis queries
3. Add statistics aggregation (average lengths per blade over time)
4. Implement export to CSV/Excel functionality
5. Add blade tolerance threshold configuration
