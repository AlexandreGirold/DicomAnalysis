"""
Basic Tests Package
Collection of quality control tests for medical equipment
"""

from .base_test import BaseTest

# Import daily, weekly, and monthly tests
import sys
import os

# Ensure services directory is in path
services_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if services_dir not in sys.path:
    sys.path.insert(0, services_dir)

# Import tests from daily, weekly, and monthly packages
DAILY_TESTS = {}
try:
    from services.daily.safety_systems import SafetySystemsTest, test_safety_systems
    DAILY_TESTS['safety_systems'] = {
        'class': SafetySystemsTest,
        'function': test_safety_systems,
        'description': 'ANSM - Vérification Quotidienne des Systèmes de Sécurité (ANSM 1.1, 1.5, TG284)',
        'category': 'daily'
    }
except ImportError as e:
    print(f"[DEBUG] Failed to import safety_systems: {e}")

try:
    from services.weekly import WEEKLY_TESTS
except ImportError as e:
    print(f"[DEBUG] Failed to import WEEKLY_TESTS: {e}")
    WEEKLY_TESTS = {}

try:
    from services.monthly import MONTHLY_TESTS
except ImportError as e:
    print(f"[DEBUG] Failed to import MONTHLY_TESTS: {e}")
    MONTHLY_TESTS = {}

__all__ = [
    'BaseTest'
]

# Test registry for easy access
AVAILABLE_TESTS = {}

# Add daily, weekly, and monthly tests to registry
AVAILABLE_TESTS.update(DAILY_TESTS)
AVAILABLE_TESTS.update(WEEKLY_TESTS)
AVAILABLE_TESTS.update(MONTHLY_TESTS)


def get_available_tests():
    """
    Get list of all available tests
    
    Returns:
        dict: Dictionary of available tests with their descriptions and category
    """
    return {
        test_id: {
            'description': test_info['description'],
            'class_name': test_info['class'].__name__,
            'category': test_info.get('category', 'basic')
        }
        for test_id, test_info in AVAILABLE_TESTS.items()
    }


def create_test_instance(test_id: str):
    """
    Create an instance of a specific test
    
    Args:
        test_id: ID of the test to create
    
    Returns:
        BaseTest: Instance of the requested test
    
    Raises:
        ValueError: If test_id is not found
    """
    if test_id not in AVAILABLE_TESTS:
        raise ValueError(f"Test '{test_id}' not found. Available tests: {list(AVAILABLE_TESTS.keys())}")
    
    return AVAILABLE_TESTS[test_id]['class']()


def execute_test(test_id: str, **kwargs):
    """
    Execute a test by ID with given parameters
    
    Args:
        test_id: ID of the test to execute
        **kwargs: Test parameters
    
    Returns:
        dict: Test results
    
    Raises:
        ValueError: If test_id is not found
    """
    if test_id not in AVAILABLE_TESTS:
        raise ValueError(f"Test '{test_id}' not found. Available tests: {list(AVAILABLE_TESTS.keys())}")
    
    return AVAILABLE_TESTS[test_id]['function'](**kwargs)