"""
Daily Tests Package
Collection of daily quality control tests for medical equipment
"""

import sys
import os
# Add services directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from basic_tests.base_test import BaseTest

# Import after path setup
from services.daily.safety_systems import SafetySystemsTest, test_safety_systems

__all__ = [
    'SafetySystemsTest',
    'test_safety_systems'
]

# Daily test registry
DAILY_TESTS = {
    'safety_systems': {
        'class': SafetySystemsTest,
        'function': test_safety_systems,
        'description': 'ANSM - Vérification Quotidienne des Systèmes de Sécurité (ANSM 1.1, 1.5, TG284)',
        'category': 'daily'
    }
}


def get_daily_tests():
    """
    Get list of all available daily tests
    
    Returns:
        dict: Dictionary of available daily tests with their descriptions
    """
    return {
        test_id: {
            'description': test_info['description'],
            'class_name': test_info['class'].__name__,
            'category': test_info['category']
        }
        for test_id, test_info in DAILY_TESTS.items()
    }


def create_daily_test_instance(test_id: str):
    """
    Create an instance of a specific daily test
    
    Args:
        test_id: ID of the test to create
    
    Returns:
        BaseTest: Instance of the requested test
    
    Raises:
        ValueError: If test_id is not found
    """
    if test_id not in DAILY_TESTS:
        raise ValueError(f"Daily test '{test_id}' not found. Available tests: {list(DAILY_TESTS.keys())}")
    
    return DAILY_TESTS[test_id]['class']()


def execute_daily_test(test_id: str, **kwargs):
    """
    Execute a daily test by ID with given parameters
    
    Args:
        test_id: ID of the test to execute
        **kwargs: Test parameters
    
    Returns:
        dict: Test results
    
    Raises:
        ValueError: If test_id is not found
    """
    if test_id not in DAILY_TESTS:
        raise ValueError(f"Daily test '{test_id}' not found. Available tests: {list(DAILY_TESTS.keys())}")
    
    return DAILY_TESTS[test_id]['function'](**kwargs)
