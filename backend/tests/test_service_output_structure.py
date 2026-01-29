"""
Simple diagnostic: verify that the Exactitude du MLC (leaf_position) service generates blade_results
"""
import sys
import os
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

# We'll create a minimal mock DICOM file just to test the flow
# Actually, let's just check what the execute() method returns in structure

from services.weekly.leaf_position import LeafPositionTest
from datetime import datetime
import json

print("Testing LeafPositionTest structure...")
print("=" * 50)

# Create instance
test = LeafPositionTest()

# Check what instance variables are initialized
print(f"\nInitial state:")
print(f"  test.blade_results = {test.blade_results}")
print(f"  type = {type(test.blade_results)}")

# Verify _format_output method exists and includes blade_results
print(f"\n_format_output method exists: {hasattr(test, '_format_output')}")

# Manually create a mock result to see output format
test.blade_results = [
    {
        'blades': [
            {'pair': 27, 'field_size_mm': 20.0, 'is_valid': 'OK'},
            {'pair': 28, 'field_size_mm': 20.0, 'is_valid': 'OK'}
        ]
    }
]
test.results = []
test.file_results = []
test.visualizations = []
test.operator = "Test"
test.test_date = datetime.now()
test.overall_result = "PASS"

# Call _format_output
output = test._format_output(notes="Test note")

print(f"\nOutput structure:")
print(f"  Keys: {list(output.keys())}")
print(f"  blade_results present: {'blade_results' in output}")
print(f"  blade_results value: {output.get('blade_results')}")

print("\nFull output:")
print(json.dumps(output, indent=2, default=str))
