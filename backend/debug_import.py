#!/usr/bin/env python
"""Debug script to check what's in weekly_tests module"""

import sys
import os

# Ensure we're in the right directory
os.chdir(r"R:\Radiotherapie - Physique Medicale\90 Encadrement etudiant\07EPITA\Etudiant Epita 2025\Alexandre Girold\DicomAnalysis\backend")
sys.path.insert(0, os.getcwd())

print("=" * 60)
print("DEBUG: Checking weekly_tests.py module")
print("=" * 60)

# Try to load the module directly without going through __init__.py
try:
    import database.weekly_tests as wt
    print("\n✓ Successfully imported database.weekly_tests")
    
    # List all classes
    classes = [name for name in dir(wt) if not name.startswith('_') and name[0].isupper()]
    print(f"\nFound {len(classes)} classes:")
    for cls_name in sorted(classes):
        print(f"  - {cls_name}")
    
    # Check specifically for LeafPosition classes
    print("\nLeafPosition classes:")
    leaf_classes = [name for name in classes if 'Leaf' in name]
    for cls_name in leaf_classes:
        cls_obj = getattr(wt, cls_name)
        print(f"  ✓ {cls_name}: {cls_obj}")
    
    # Check if LeafPositionImage exists
    if hasattr(wt, 'LeafPositionImage'):
        print("\n✓✓✓ LeafPositionImage EXISTS in module!")
        print(f"  Class: {wt.LeafPositionImage}")
        print(f"  Table: {wt.LeafPositionImage.__tablename__}")
    else:
        print("\n✗✗✗ LeafPositionImage NOT FOUND in module!")
        
except Exception as e:
    print(f"\n✗ Error importing: {e}")
    import traceback
    traceback.print_exc()
