"""
Check all test result names vs database column names
to identify mismatches that could cause errors
"""
import re
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    MVICTest, MLCLeafJawTest, MVICFenteV2Test, NiveauHeliumTest,
    PIQTTest, SafetySystemsTest, PositionTableV2Test, AlignementLaserTest,
    QuasarTest, IndiceQualityTest
)
from sqlalchemy import inspect

def sanitize_field_name(field_name: str) -> str:
    """Same sanitization as backend/main.py"""
    sanitized = re.sub(r'[^\w\s]', '', field_name)
    sanitized = sanitized.replace(' ', '_')
    sanitized = sanitized.lower()
    return sanitized

def get_model_columns(model_class):
    """Get all column names from a model"""
    mapper = inspect(model_class)
    return {col.key for col in mapper.columns}

def extract_result_names_from_file(filepath):
    """Extract all result names from a service file"""
    result_names = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all add_result calls with name= parameter
            matches = re.finditer(r'add_result\s*\([^)]*name\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            for match in matches:
                result_names.append(match.group(1))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return result_names

def check_test(test_name, model_class, service_file):
    """Check one test for result name mismatches"""
    print(f"\n{'='*80}")
    print(f"🔍 {test_name}")
    print(f"{'='*80}")
    
    # Get database columns
    db_columns = get_model_columns(model_class)
    print(f"\n✓ Database columns ({len(db_columns)}): {sorted(db_columns)}")
    
    # Get result names from service file
    if not os.path.exists(service_file):
        print(f"❌ Service file not found: {service_file}")
        return
    
    result_names = extract_result_names_from_file(service_file)
    if not result_names:
        print(f"\n⚠️  No result names found in service file")
        return
    
    print(f"\n📊 Result names ({len(result_names)}): {result_names}")
    
    # Check which result names would become invalid columns
    issues = []
    for result_name in result_names:
        sanitized = sanitize_field_name(result_name)
        if sanitized not in db_columns:
            issues.append({
                'original': result_name,
                'sanitized': sanitized,
                'exists': False
            })
        else:
            print(f"  ✓ '{result_name}' → '{sanitized}' (exists in DB)")
    
    if issues:
        print(f"\n❌ Found {len(issues)} result names that DON'T match database columns:")
        for issue in issues:
            print(f"  ✗ '{issue['original']}' → '{issue['sanitized']}' (NOT in DB)")
    else:
        print(f"\n✅ All result names would map to valid database columns")
    
    return len(issues)

# Test configurations
tests = [
    ("MVIC", MVICTest, "services/weekly/MVIC/mvic_test.py"),
    ("MLC Leaf Jaw", MLCLeafJawTest, "services/basic_tests/mlc_leaf_jaw.py"),
    ("MVIC Fente V2", MVICFenteV2Test, "services/weekly/MVIC_fente/mvic_fente_v2.py"),
    ("Niveau Helium", NiveauHeliumTest, "services/weekly/niveau_helium.py"),
    ("PIQT", PIQTTest, "services/weekly/PIQT.py"),
    ("Safety Systems", SafetySystemsTest, "services/daily/safety_systems.py"),
    ("Position Table V2", PositionTableV2Test, "services/monthly/position_table.py"),
    ("Alignement Laser", AlignementLaserTest, "services/monthly/alignement_laser.py"),
    ("Quasar", QuasarTest, "services/monthly/quasar.py"),
    ("Indice Quality", IndiceQualityTest, "services/monthly/indice_quality.py"),
]

print("\n" + "="*80)
print("🔬 CHECKING ALL TEST RESULT NAMES VS DATABASE COLUMNS")
print("="*80)

total_issues = 0
for test_name, model_class, service_file in tests:
    service_path = os.path.join(os.path.dirname(__file__), service_file)
    issues = check_test(test_name, model_class, service_path)
    if issues:
        total_issues += issues

print(f"\n{'='*80}")
print(f"📋 SUMMARY")
print(f"{'='*80}")
print(f"Total tests checked: {len(tests)}")
print(f"Total mismatches found: {total_issues}")

if total_issues > 0:
    print(f"\n⚠️  These result names are for DISPLAY ONLY and should be filtered out")
    print(f"    The backend filtering in database_helpers.py should handle this automatically")
else:
    print(f"\n✅ No issues found!")
