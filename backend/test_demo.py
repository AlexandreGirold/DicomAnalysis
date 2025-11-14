"""
Test demonstration script for basic quality control tests
"""
import sys
import os
from datetime import datetime

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

from basic_tests import (
    test_helium_level,
    test_position_table_v2, 
    test_alignement_laser,
    get_available_tests,
    create_test_instance
)


def demo_niveau_helium():
    """Demonstrate the helium level test"""
    print("=== Niveau d'Hélium Test Demo ===")
    
    # Test case 1: PASS (above 65%)
    result1 = test_helium_level(
        helium_level=75.5,
        operator="Dr. Dupont"
    )
    print(f"Test 1 (75.5%): {result1['overall_result']}")
    
    # Test case 2: FAIL (below 65%)
    result2 = test_helium_level(
        helium_level=60.0,
        operator="Dr. Dupont"
    )
    print(f"Test 2 (60.0%): {result2['overall_result']}")
    
    print("Detailed result for Test 1:")
    print(f"  Input: {result1['inputs']}")
    print(f"  Results: {result1['results']}")
    print()


def demo_position_table():
    """Demonstrate the position table test"""
    print("=== Position Table V2 Test Demo ===")
    
    # Test case 1: PASS (within tolerance)
    result1 = test_position_table_v2(
        position_175=17.5,
        position_215=21.48,  # Should give ~16mm difference
        operator="Dr. Martin"
    )
    print(f"Test 1 (17.5, 21.48): {result1['overall_result']}")
    
    # Test case 2: FAIL (outside tolerance)
    result2 = test_position_table_v2(
        position_175=17.5,
        position_215=21.8,   # Should give ~20mm difference, ecart = 4mm
        operator="Dr. Martin"
    )
    print(f"Test 2 (17.5, 21.8): {result2['overall_result']}")
    
    print("Detailed result for Test 1:")
    print(f"  Results: {result1['results']}")
    print()


def demo_alignement_laser():
    """Demonstrate the laser alignment test"""
    print("=== Alignement Laser Test Demo ===")
    
    # Test case 1: PASS (all within tolerance)
    result1 = test_alignement_laser(
        ecart_proximal=1.2,
        ecart_central=0.8,
        ecart_distal=1.5,
        operator="Dr. Leroy"
    )
    print(f"Test 1 (1.2, 0.8, 1.5): {result1['overall_result']}")
    
    # Test case 2: FAIL (one outside tolerance)
    result2 = test_alignement_laser(
        ecart_proximal=1.2,
        ecart_central=2.8,  # Above 2mm tolerance
        ecart_distal=1.5,
        operator="Dr. Leroy"
    )
    print(f"Test 2 (1.2, 2.8, 1.5): {result2['overall_result']}")
    
    print("Detailed result for Test 1:")
    print(f"  Results: {result1['results']}")
    print()


def demo_test_registry():
    """Demonstrate the test registry functionality"""
    print("=== Available Tests ===")
    available = get_available_tests()
    for test_id, info in available.items():
        print(f"  {test_id}: {info['description']}")
    print()
    
    # Create test instance and get form data
    print("=== Form Data Example ===")
    helium_test = create_test_instance('niveau_helium')
    form_data = helium_test.get_form_data()
    print("Niveau Helium form fields:")
    for field in form_data['fields']:
        print(f"  - {field['label']} ({field['type']})")
    print()


def main():
    """Run all demonstrations"""
    print("Basic Tests Demonstration")
    print("=" * 50)
    print()
    
    demo_niveau_helium()
    demo_position_table()
    demo_alignement_laser()
    demo_test_registry()
    
    print("All demonstrations completed!")


if __name__ == "__main__":
    main()