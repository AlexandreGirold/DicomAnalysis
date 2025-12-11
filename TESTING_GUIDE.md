# Quick Start Guide - Testing Database Save Fix

## Problem Fixed

✅ **Before:** All tests were saving as MVIC tests regardless of type
✅ **Before:** Save button stayed disabled when running new tests
✅ **Now:** Each test type saves to its correct database table
✅ **Now:** Save button resets for each new test

## How to Test

### 1. Start the Backend Server

```powershell
cd backend
.\env\Scripts\python.exe -m uvicorn main:app --reload
```

Server will start at: http://localhost:8000

### 2. Option A: Test via Frontend (Recommended)

1. Open browser to http://localhost:8000
2. Select any test (e.g., "MLC Leaf and Jaw Position")
3. Upload DICOM files and run test
4. Wait for results to display
5. Click "💾 Save to Database" button
6. Enter operator name when prompted
7. Check success message shows correct test type
8. **Open browser console (F12)** to see:
   - "Final test type: mlc_leaf_jaw"
   - "Saving to endpoint: /mlc-leaf-jaw-sessions"
9. Try running a different test type
10. Verify save button is enabled again

### 3. Option B: Test Endpoints Directly

```powershell
cd backend
.\env\Scripts\python.exe test_all_save_endpoints.py
```

This will test all 10 endpoints with sample data and show:
- ✅ SUCCESS for working endpoints
- ❌ FAILED for broken endpoints

### 4. Verify Database

Check the database has entries in correct tables:

```powershell
cd backend
.\env\Scripts\python.exe
```

```python
from database import SessionLocal, MVICTest, MLCLeafJawTest, NiveauHeliumTest
db = SessionLocal()

# Check MVIC tests
mvic_count = db.query(MVICTest).count()
print(f"MVIC tests: {mvic_count}")

# Check MLC tests
mlc_count = db.query(MLCLeafJawTest).count()
print(f"MLC Leaf Jaw tests: {mlc_count}")

# Check Helium tests
helium_count = db.query(NiveauHeliumTest).count()
print(f"Niveau Helium tests: {helium_count}")

db.close()
```

## Test Type to Endpoint Mapping

| Test Name | Endpoint | Table |
|-----------|----------|-------|
| MVIC (5 images) | `/mvic-test-sessions` | `weekly_mvic` |
| MVIC Fente V2 | `/mvic-fente-v2-sessions` | `weekly_mvic_fente_v2` |
| MLC Leaf Jaw | `/mlc-leaf-jaw-sessions` | `weekly_mlc_leaf_jaw` |
| Niveau Helium | `/niveau-helium-sessions` | `weekly_niveau_helium` |
| PIQT | `/piqt-sessions` | `weekly_piqt` |
| Safety Systems | `/safety-systems-sessions` | `daily_safety_systems` |
| Position Table | `/position-table-sessions` | `monthly_position_table_v2` |
| Alignement Laser | `/alignement-laser-sessions` | `monthly_alignement_laser` |
| Quasar | `/quasar-sessions` | `monthly_quasar` |
| Indice Quality | `/indice-quality-sessions` | `monthly_indice_quality` |

## What to Look For

### Browser Console (F12)

When clicking "Save to Database", you should see:

```
Final test type: mlc_leaf_jaw
Saving to endpoint: http://localhost:8000/mlc-leaf-jaw-sessions
```

**NOT:**
```
Final test type: mvic  ❌ WRONG!
Saving to endpoint: http://localhost:8000/mvic-test-sessions  ❌ WRONG!
```

### Success Alert

Should show:
```
✅ Test saved successfully!

Test ID: 5

You can view this test in the Review page.
```

### Button State

- **After save:** Shows "✅ Saved" and is grayed out
- **After new test runs:** Shows "💾 Save to Database" and is green/enabled

## Troubleshooting

### Problem: "Unknown test type" error

**Check:** Browser console shows `Final test type: null` or `undefined`

**Fix:** The test name detection failed. Check that test result includes a `test_name` field.

### Problem: Still saving to wrong endpoint

**Check:** Browser console shows wrong endpoint

**Fix:** Update `mapTestNameToEndpoint()` in `mlc-save.js` to recognize the test name pattern.

### Problem: Button stays disabled

**Fix:** Already fixed! Clear browser cache (Ctrl+F5) to reload JavaScript.

### Problem: 500 Internal Server Error

**Check:** Backend console shows traceback

**Common causes:**
- Database table doesn't exist → Run `migrate_database.py`
- Missing operator field → Check data structure
- Import error → Check `database_helpers.py` is imported

## Files Modified

All changes are in these files:

**Backend:**
- `backend/main.py` - Added 9 new save endpoints
- `backend/database_helpers.py` - Already had save functions (no changes)

**Frontend:**
- `frontend/js/mlc-save.js` - Added endpoint routing logic
- `frontend/js/test-execution.js` - Pass test ID correctly
- `frontend/js/results-display.js` - Reset button state

## Next Steps

After verifying everything works:

1. ✅ Test each test type individually
2. ✅ Verify correct database table is populated
3. ✅ Check save button resets between tests
4. 📝 Document any test types that need special handling
5. 📝 Add GET endpoints to retrieve saved tests by type
6. 📝 Update Review page to show all test types

## Support

If issues persist:
1. Check `DATABASE_SAVE_ENDPOINTS.md` for detailed documentation
2. Run `test_all_save_endpoints.py` to identify which endpoints fail
3. Check backend logs for detailed error messages
4. Verify database schema with `migrate_database.py`
