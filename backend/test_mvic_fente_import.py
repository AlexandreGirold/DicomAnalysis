"""
Test script for MVIC Fente
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / 'services'))

print("Testing MVIC Fente import...")

try:
    from services.weekly.MVIC_fente import MVICFenteTest
    print("✓ Successfully imported MVICFenteTest")
    
    # Create test instance
    test = MVICFenteTest()
    print(f"✓ Created test instance: {test.test_name}")
    
    # Get form data
    form_data = test.get_form_data()
    print(f"✓ Got form data: {form_data['title']}")
    print(f"  Fields: {len(form_data['fields'])}")
    
    print("\n✓✓✓ All tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
