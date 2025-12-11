## Fix Summary: Result Names vs Database Columns

### Problem
Frontend was extracting **both inputs and results** from test analysis and trying to save them all to database:
- **Inputs** (✓ correct): `latence_status`, `latence_reason`, `d10_m1`, `d10_m2`, etc.
- **Results** (✗ wrong): `"Latence du gating"`, `"D10 Moyenne"`, `"Position X"`, etc.

Result names are **display labels with spaces/special chars** that don't match database column names.

### Tests Affected
Script found **23 mismatched result names** across all tests:

1. **MLC Leaf Jaw** (3): analysis_error, analysis_result, analysis_completed
2. **Niveau Helium** (1): helium_level_check  
3. **PIQT** (1): Erreur de parsing
4. **Safety Systems** (1): audio_beam_indicator
5. **Position Table V2** (2): actual_difference, ecart_mm
6. **Quasar** (7): Latence du gating (×3), Correction Système Coord., Position X/Y/Z
7. **Indice Quality** (8): D10/D20/D5/D15 Moyenne, Ratio D20/D10, Ratio D15/D5

### Solution Applied

**Two-layer fix:**

#### 1. Field Name Sanitization (backend/main.py)
```python
def sanitize_field_name(field_name: str) -> str:
    # "Latence du gating" → "latence_du_gating"
    # "D10 Moyenne" → "d10_moyenne"
    # "Position X" → "position_x"
```

#### 2. Column Validation (backend/database_helpers.py)
```python
# Get valid columns from model
mapper = inspect(test_class)
valid_columns = {col.key for col in mapper.columns}

# Only add fields that exist in database
for key, value in extra_fields.items():
    if key in valid_columns:  # ← Filter here
        test_data[key] = value
    else:
        logger.debug(f"Skipping unknown field: {key}")
```

### Result
- Frontend sends: `latence_status`, `latence_reason`, `latence_du_gating` (sanitized from "Latence du gating")
- Backend filters to: `latence_status`, `latence_reason` (only valid columns)
- Database saves: Only the valid fields, no errors!

### To Apply Fix
1. **Stop the backend server** (Ctrl+C in terminal)
2. **Restart it**: `cd C:\Users\agirold\Desktop\DicomAnalysis\backend ; .\env\Scripts\Activate.ps1 ; python main.py`
3. **Refresh browser** (cache is already v=2000)
4. **Test saving** any test type - should work now!

### Verification
Run this to see all mismatches:
```bash
cd C:\Users\agirold\Desktop\DicomAnalysis\backend
.\env\Scripts\Activate.ps1
python check_result_names.py
```

Shows which result names are display-only and will be filtered out.

### Why This Works
- **Before**: Backend crashed when receiving unknown field names
- **After**: Backend silently filters unknown fields, saves only valid ones
- **Display results** (calculations, formatted values) never reach database
- **Input data** (raw measurements) is saved correctly
