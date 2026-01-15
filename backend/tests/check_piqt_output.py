"""
Check what data the PIQT test actually outputs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.weekly.PIQT import PIQTTest
import json

# You'll need to provide a PIQT HTML file path
# This is just to show what fields are in the output

print("PIQT Test Output Structure:")
print("=" * 80)
print("\nWhen execute() is called, it returns to_dict() which contains:")
print("  - test_name: str")
print("  - description: str")
print("  - test_date: ISO datetime")
print("  - operator: str")
print("  - inputs: list")
print("  - results: list of {name, value, status, unit, tolerance}")
print("  - overall_result: str")
print("  - overall_status: str")
print("\nThe 'results' array contains ALL measurements.")
print("We need to extract specific values from this array:")
print("  - Look for 'snr' or 'signal' + 'noise' in name")
print("  - Look for 'uniformity' or 'unif' in name")
print("  - Look for 'ghost' in name")
print("\n" + "=" * 80)
