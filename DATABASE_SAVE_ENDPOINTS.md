# Database Save Endpoints - Complete Implementation

## Summary

Fixed the issue where all tests were being saved as MVIC tests. Now each test type has its own dedicated save endpoint and the frontend correctly routes to the appropriate endpoint based on the test type.

## Changes Made

### 1. Backend Changes (main.py)

#### Added Helper Function
```python
def parse_test_date(date_str):
    """Helper function to parse test date from string or return current datetime"""
```

#### Added 9 New Save Endpoints

1. **POST /mlc-leaf-jaw-sessions** - MLC Leaf and Jaw test
2. **POST /mvic-fente-v2-sessions** - MVIC Fente V2 (slit analysis)
3. **POST /niveau-helium-sessions** - Niveau Helium test
4. **POST /piqt-sessions** - PIQT test
5. **POST /safety-systems-sessions** - Safety Systems test
6. **POST /position-table-sessions** - Position Table V2 test
7. **POST /alignement-laser-sessions** - Alignement Laser test
8. **POST /quasar-sessions** - Quasar test
9. **POST /indice-quality-sessions** - Indice Quality test

Each endpoint:
- Accepts JSON with: `test_date`, `operator`, `overall_result`, `notes`, `filenames`
- Validates operator is present
- Calls appropriate `database_helpers` function
- Returns: `{success: true, test_id: X, message: "..."}`

### 2. Frontend Changes (mlc-save.js)

#### Added Test Type Mapping
```javascript
const TEST_SAVE_ENDPOINTS = {
    'mvic': '/mvic-test-sessions',
    'mvic_fente': '/mvic-fente-v2-sessions',
    'mvic_fente_v2': '/mvic-fente-v2-sessions',
    'mlc_leaf_jaw': '/mlc-leaf-jaw-sessions',
    'niveau_helium': '/niveau-helium-sessions',
    'piqt': '/piqt-sessions',
    'safety_systems': '/safety-systems-sessions',
    'position_table_v2': '/position-table-sessions',
    'alignement_laser': '/alignement-laser-sessions',
    'quasar': '/quasar-sessions',
    'indice_quality': '/indice-quality-sessions'
};
```

#### Added Helper Functions
- `extractFilenames(analysisResult)` - Extracts filenames from various result structures
- `prepareGenericTestData(analysisResult)` - Prepares data for simple tests
- `mapTestNameToEndpoint(testName)` - Maps test names to endpoint keys

#### Enhanced Test Type Detection
The `enableMLCTestSave()` function now:
1. Tries to detect test type from `test_name` field
2. Falls back to checking result structure (visualizations, file_results)
3. Uses intelligent mapping to determine correct endpoint

#### Updated Save Function
`saveMLCTestToDatabase()` now:
- Looks up correct endpoint from `TEST_SAVE_ENDPOINTS`
- Shows error if test type is unknown
- Routes to appropriate backend endpoint

### 3. Frontend Changes (test-execution.js)

#### Updated Test Execution
`handleFileUploadTest()` now:
- Passes `testId` directly to `enableMLCTestSave()`
- Frontend uses testId to determine endpoint

### 4. Frontend Changes (results-display.js)

#### Fixed Save Button State
`displayTestResults()` now:
- Resets button state when new test results displayed
- Sets: `disabled = false`, text = "💾 Save to Database", class = "btn-success"
- This fixes the issue where button stayed disabled after first save

## Test Endpoint Mapping

| Test Type | Frontend ID | Backend Endpoint | Database Table |
|-----------|------------|------------------|----------------|
| MVIC (5 images) | `mvic` | `/mvic-test-sessions` | `weekly_mvic` |
| MVIC Fente V2 | `mvic_fente_v2` | `/mvic-fente-v2-sessions` | `weekly_mvic_fente_v2` |
| MLC Leaf Jaw | `mlc_leaf_jaw` | `/mlc-leaf-jaw-sessions` | `weekly_mlc_leaf_jaw` |
| Niveau Helium | `niveau_helium` | `/niveau-helium-sessions` | `weekly_niveau_helium` |
| PIQT | `piqt` | `/piqt-sessions` | `weekly_piqt` |
| Safety Systems | `safety_systems` | `/safety-systems-sessions` | `daily_safety_systems` |
| Position Table V2 | `position_table_v2` | `/position-table-sessions` | `monthly_position_table_v2` |
| Alignement Laser | `alignement_laser` | `/alignement-laser-sessions` | `monthly_alignement_laser` |
| Quasar | `quasar` | `/quasar-sessions` | `monthly_quasar` |
| Indice Quality | `indice_quality` | `/indice-quality-sessions` | `monthly_indice_quality` |

## Testing

### Manual Testing Steps

1. **Start the Backend Server**
   ```powershell
   cd backend
   .\env\Scripts\python.exe -m uvicorn main:app --reload
   ```

2. **Run Automated Test Script**
   ```powershell
   cd backend
   .\env\Scripts\python.exe test_all_save_endpoints.py
   ```
   This will test all 10 save endpoints with sample data.

3. **Test via Frontend**
   - Open http://localhost:8000
   - Run any test
   - Click "Save to Database"
   - Check that correct endpoint is called in browser console
   - Verify test appears in database

### Expected Behavior

✅ **Before clicking save:**
- Button shows: "💾 Save to Database"
- Button is enabled
- Console shows: "Final test type: [correct_type]"

✅ **After clicking save:**
- Prompt for operator name
- Button shows: "⏳ Saving..."
- Console shows: "Saving to endpoint: /[correct-endpoint]"
- Success alert with test ID
- Button shows: "✅ Saved"

✅ **Running new test:**
- Button resets to: "💾 Save to Database"
- Button is enabled again
- Can save new test

## Database Schema

All test tables have these common fields:
- `id` - Primary key
- `test_date` - When test was performed
- `operator` - Who performed the test
- `overall_result` - PASS/FAIL/WARNING
- `notes` - Optional notes
- `filenames` - Comma-separated list of source files
- `upload_date` - When saved to database

Special tables with results:
- `weekly_mvic` → `weekly_mvic_results` (5 rows per test, one per image)
- `weekly_mvic_fente_v2` → `weekly_mvic_fente_v2_results` (N rows, one per slit)
- `weekly_niveau_helium` → `weekly_niveau_helium_results` (1 row with helium level)

## Troubleshooting

### Issue: "Unknown test type" error
**Solution:** Check that test name contains recognizable keyword (MVIC, MLC, etc.) or that testId is passed correctly from test-execution.js

### Issue: "operator is required" error
**Solution:** Ensure operator name is prompted and entered when saving

### Issue: Button stays disabled after save
**Solution:** Fixed - displayTestResults() now resets button state

### Issue: Wrong endpoint called
**Solution:** Check browser console for "Final test type:" message. If incorrect, update mapTestNameToEndpoint() function

## Files Modified

1. `backend/main.py` - Added 9 save endpoints, parse_test_date helper
2. `backend/database_helpers.py` - Already had save functions
3. `frontend/js/mlc-save.js` - Added endpoint mapping, test detection
4. `frontend/js/test-execution.js` - Pass testId to save function
5. `frontend/js/results-display.js` - Reset button state on new results

## Files Created

1. `backend/test_all_save_endpoints.py` - Automated test script

## Next Steps

1. **Test all endpoints** with real DICOM files
2. **Verify database** entries are correct for each test type
3. **Add GET endpoints** for each test type (retrieve saved tests)
4. **Update Review page** to show all test types in separate tabs
5. **Add DELETE endpoints** for each test type
6. **Add filtering/search** functionality for saved tests
