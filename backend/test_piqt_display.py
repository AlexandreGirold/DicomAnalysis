"""
Test PIQT Display Module
Quick test to verify the display system works
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from result_displays.piqt_display import display_piqt_result

def test_display():
    print("=" * 80)
    print("TESTING PIQT DISPLAY MODULE")
    print("=" * 80)
    
    # Try to display first test (ID 1)
    print("\nAttempting to retrieve test ID 1...")
    result = display_piqt_result(1)
    
    if result:
        print("\n✅ SUCCESS - Test retrieved")
        print(f"\nTest Name: {result['test_name']}")
        print(f"Test ID: {result['test_id']}")
        print(f"Date: {result['test_date']}")
        print(f"Operator: {result['operator']}")
        print(f"Result: {result['overall_result']}")
        
        print(f"\nFilenames: {len(result['filenames'])} file(s)")
        if result['filenames']:
            for f in result['filenames']:
                print(f"  - {f}")
        
        print(f"\nSummary:")
        for key, value in result['summary'].items():
            print(f"  {key}: {value}")
        
        print(f"\nResults Count: {len(result['results'])} measurements")
        if result['results']:
            print("\nFirst 5 measurements:")
            for r in result['results'][:5]:
                print(f"  {r['name']}: {r['value']} {r['unit']}")
        
        print(f"\nDetailed Results Categories:")
        if result['detailed_results']:
            for category in result['detailed_results'].keys():
                print(f"  - {category}")
        
        print("\n✅ Display module working correctly!")
        
    else:
        print("\n⚠️  No test found with ID 1")
        print("This is normal if the database is empty")
        print("Run some PIQT tests first to populate the database")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_display()
