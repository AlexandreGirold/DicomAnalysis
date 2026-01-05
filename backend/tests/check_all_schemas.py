"""
Check all test tables for schema mismatches between Python models and actual database
"""
import sqlite3
from pathlib import Path
from database import *
from sqlalchemy import inspect

db_path = Path(__file__).parent / "data" / "qc_tests.db"

# Define all test tables and their model classes
TEST_TABLES = {
    # Weekly tests
    'weekly_niveau_helium': NiveauHeliumTest,
    'weekly_mlc_leaf_jaw': MLCLeafJawTest,
    'weekly_mvic': MVICTest,
    'weekly_mvic_fente_v2': MVICFenteV2Test,
    'weekly_piqt': PIQTTest,
    
    # Daily tests
    'daily_safety_systems': SafetySystemsTest,
    
    # Monthly tests
    'monthly_position_table_v2': PositionTableV2Test,
    'monthly_alignement_laser': AlignementLaserTest,
    'monthly_quasar': QuasarTest,
    'monthly_indice_quality': IndiceQualityTest,
}

print("=" * 80)
print("CHECKING ALL TEST TABLES FOR SCHEMA MISMATCHES")
print("=" * 80)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

mismatches = []

for table_name, model_class in TEST_TABLES.items():
    print(f"\n{'='*80}")
    print(f"Table: {table_name}")
    print(f"Model: {model_class.__name__}")
    print(f"{'='*80}")
    
    # Get actual database columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    db_columns = {}
    for row in cursor.fetchall():
        col_name = row[1]
        col_type = row[2]
        not_null = row[3]
        db_columns[col_name] = {'type': col_type, 'not_null': bool(not_null)}
    
    # Get model columns
    inspector = inspect(model_class)
    model_columns = {}
    for column in inspector.columns:
        col_name = column.name
        col_type = str(column.type)
        not_null = not column.nullable
        model_columns[col_name] = {'type': col_type, 'not_null': not_null}
    
    # Compare
    print(f"\n📊 Database columns ({len(db_columns)}):")
    for col_name, info in sorted(db_columns.items()):
        req = "REQUIRED" if info['not_null'] else "optional"
        print(f"  - {col_name:30} {info['type']:15} {req}")
    
    print(f"\n🐍 Model columns ({len(model_columns)}):")
    for col_name, info in sorted(model_columns.items()):
        req = "REQUIRED" if info['not_null'] else "optional"
        print(f"  - {col_name:30} {info['type']:15} {req}")
    
    # Find mismatches
    db_only = set(db_columns.keys()) - set(model_columns.keys())
    model_only = set(model_columns.keys()) - set(db_columns.keys())
    
    if db_only:
        print(f"\n❌ MISMATCH: Columns in DATABASE but NOT in MODEL:")
        for col in sorted(db_only):
            info = db_columns[col]
            req = "REQUIRED" if info['not_null'] else "optional"
            print(f"  - {col:30} {info['type']:15} {req}")
            mismatches.append({
                'table': table_name,
                'issue': 'db_only',
                'column': col,
                'details': f"Database has {col} but model doesn't"
            })
    
    if model_only:
        print(f"\n⚠️  WARNING: Columns in MODEL but NOT in DATABASE:")
        for col in sorted(model_only):
            info = model_columns[col]
            req = "REQUIRED" if info['not_null'] else "optional"
            print(f"  - {col:30} {info['type']:15} {req}")
            mismatches.append({
                'table': table_name,
                'issue': 'model_only',
                'column': col,
                'details': f"Model has {col} but database doesn't"
            })
    
    if not db_only and not model_only:
        print(f"\n✅ Schema matches perfectly!")

conn.close()

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} schema mismatches:\n")
    for i, mismatch in enumerate(mismatches, 1):
        print(f"{i}. {mismatch['table']}: {mismatch['details']}")
else:
    print("\n✅ All test tables match their Python models perfectly!")

print("\n" + "="*80)
