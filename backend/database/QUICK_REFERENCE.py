"""
Quick Reference: Database Module Structure
===========================================

BEFORE (Single File):
  database.py (375 lines)
    - Config + All test models mixed together
    - Hard to find specific models
    - Difficult to maintain

AFTER (Modular Package):
  database/
    ├── __init__.py (50 lines) ← Main entry point
    ├── config.py (23 lines) ← Core setup
    ├── daily_tests.py (25 lines) ← Daily QC
    ├── weekly_tests.py (130 lines) ← Weekly QC  
    ├── monthly_tests.py (75 lines) ← Monthly QC
    └── mlc_curie.py (95 lines) ← MLC tests

USAGE (No changes needed!):
  from database import SessionLocal, MVCenterConfig
  
ADDING NEW TEST:
  1. Edit appropriate file (daily/weekly/monthly)
  2. Add model class
  3. Export in __init__.py
  4. Restart app
  
WHERE TO FIND MODELS:
  
  Daily Tests:
    • SafetySystemsTest → daily_tests.py
    
  Weekly Tests:
    • NiveauHeliumTest → weekly_tests.py
    • MLCLeafJawTest → weekly_tests.py
    • MVICTest → weekly_tests.py
    • PIQTTest → weekly_tests.py
    
  Monthly Tests:
    • PositionTableV2Test → monthly_tests.py
    • AlignementLaserTest → monthly_tests.py
    • QuasarTest → monthly_tests.py
    • IndiceQualityTest → monthly_tests.py
    
  MLC Curie:
    • MVCenterConfig → mlc_curie.py
    • All blade/leaf/jaw models → mlc_curie.py

BENEFITS:
  ✓ Organized - Clear file structure
  ✓ Maintainable - Easy to find and edit
  ✓ Scalable - Add tests without clutter
  ✓ Readable - Shorter, focused files
  ✓ Compatible - No code changes needed
"""
