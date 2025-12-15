# MVIC Test Save Enhancements

## Summary
Enhanced MVIC test save functionality to match MVIC Fente V2 pattern, saving detailed per-image results including individual corner angles and visualizations.

## Changes Made

### 1. Database Schema Updates

**File: `backend/database/weekly_tests.py`**
- Added `file_results` column to `MVICTest` model
- Stores JSON string with detailed per-image measurements and metadata

**Migration: `backend/migrate_add_mvic_file_results.py`**
- Created and executed migration script
- Added `file_results TEXT` column to `weekly_mvic` table
- ✓ Migration completed successfully

### 2. Database Helper Updates

**File: `backend/database_helpers.py`**
- Updated `save_mvic_to_database()` function to accept `file_results` parameter
- Enhanced logic to extract individual corner angles from `file_results` if available
- Falls back to legacy `results` parameter for backward compatibility
- Saves `file_results` as JSON string in database

**New Parameters:**
```python
def save_mvic_to_database(
    operator: str,
    test_date: datetime,
    overall_result: str,
    results: List[Dict[str, Any]],
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None,
    file_results: Optional[List[Dict[str, Any]]] = None  # NEW
) -> int:
```

### 3. API Router Updates

**File: `backend/routers/mvic_routes.py`**
- Updated `/mvic-test-sessions` POST endpoint
- Now passes `file_results` from request body to save function
- Includes detailed measurements for each image

### 4. Frontend Updates

**File: `frontend/js/mlc-save.js`**
- Updated `prepareMVICDataForSave()` function
- Now includes `file_results` in the save request
- Also includes `filenames` for proper database storage

**Added code:**
```javascript
// Include file_results with per-file metadata and detailed measurements
if (analysisResult.file_results) {
    mvicData.file_results = analysisResult.file_results;
}

// Include filenames for database storage
if (analysisResult.filenames) {
    mvicData.filenames = analysisResult.filenames;
}
```

### 5. Display Page Enhancements

**File: `backend/result_displays/mvic_display.py`**
- Added `file_results` parsing from database
- Handles JSON string deserialization
- Includes `file_results` in output dictionary

**File: `frontend/result_displays/mvic_display.html`**
- Enhanced image cards to show individual corner angles
- Displays filename for each image
- Shows 4 corner angles (top-left, top-right, bottom-left, bottom-right)
- Uses `file_results` data when available
- Gracefully falls back to summary data if `file_results` not present

## Data Flow

### 1. Test Execution → Frontend
```
MVIC Test (mvic_test.py)
  ├─ execute() processes 5 DICOM files
  ├─ Generates visualizations
  ├─ Creates file_results array with:
  │   ├─ filename
  │   ├─ filepath
  │   ├─ image_number
  │   ├─ acquisition_date
  │   ├─ dimensions (width_mm, height_mm)
  │   ├─ measurements (top_left_angle, top_right_angle, etc.)
  │   └─ status (PASS/FAIL)
  └─ to_dict() includes:
      ├─ visualizations[]
      ├─ filenames[]
      └─ file_results[]
```

### 2. Frontend → Backend API
```
mlc-save.js prepareMVICDataForSave()
  └─ POST /mvic-test-sessions
      ├─ operator
      ├─ test_date
      ├─ overall_result
      ├─ image1..image5 (summary data)
      ├─ visualizations[] (base64 images)
      ├─ filenames[] (DICOM filenames)
      └─ file_results[] (detailed per-image data)
```

### 3. Backend Save → Database
```
save_mvic_to_database()
  ├─ Creates MVICTest record with:
  │   ├─ Basic metadata
  │   ├─ filenames (comma-separated)
  │   ├─ file_results (JSON string)
  │   └─ visualization_paths (JSON array)
  └─ Creates 5 MVICResult records with:
      ├─ image_number (1-5)
      ├─ filename
      ├─ Individual corner angles (from file_results)
      ├─ width_mm
      └─ height_mm
```

### 4. Display Retrieval
```
display_mvic_result(test_id)
  ├─ Queries database for MVICTest
  ├─ Parses file_results JSON
  ├─ Parses visualization_paths JSON
  └─ Returns formatted data with:
      ├─ images[] (summary for 5 images)
      ├─ file_results[] (detailed measurements)
      └─ visualization_paths[]
```

## file_results Structure

Each element in the `file_results` array contains:
```json
{
  "filename": "RTI00348.dcm",
  "filepath": "path/to/file.dcm",
  "image_number": 1,
  "acquisition_date": "2025-09-17 14:30:00",
  "analysis_type": "Field Size and Shape Validation",
  "dimensions": {
    "field_width_mm": 150.2,
    "field_height_mm": 85.1,
    "center_u": 512.5,
    "center_v": 384.2
  },
  "size_validation": {
    "is_valid": true,
    "expected_width": 150.0,
    "detected_width": 150.2,
    "width_error": 0.2
  },
  "angle_validation": {
    "is_valid": true,
    "avg_angle": 90.1,
    "std_angle": 0.5
  },
  "measurements": {
    "top_left_angle": 90.2,
    "top_right_angle": 89.9,
    "bottom_left_angle": 90.3,
    "bottom_right_angle": 90.0,
    "avg_angle": 90.1,
    "angle_std_dev": 0.5,
    "width_mm": 150.2,
    "height_mm": 85.1
  },
  "status": "PASS"
}
```

## Benefits

1. **Complete Data Preservation**: All analysis details saved to database
2. **Individual File Tracking**: Each DICOM file's results stored separately
3. **Corner Angle Detail**: All 4 corner angles available for review
4. **Consistent Pattern**: Matches MVIC Fente V2 implementation
5. **Backward Compatible**: Still supports legacy summary data format
6. **Enhanced Display**: UI shows both summary and detailed measurements

## Testing Checklist

- [x] Database migration successful
- [ ] Run MVIC test with 5 DICOM files
- [ ] Verify visualizations generated
- [ ] Click "Save to Database" button
- [ ] Verify test saved successfully
- [ ] Check database contains `file_results` JSON
- [ ] View saved test in display page
- [ ] Verify corner angles displayed
- [ ] Verify visualizations displayed
- [ ] Verify filenames shown correctly

## Next Steps

1. **Test the complete flow**: Run MVIC test → Save → Display
2. **Verify database storage**: Check that `file_results` is properly saved
3. **Validate display**: Ensure corner angles and visualizations show correctly
4. **Performance check**: Monitor database query performance with large datasets
