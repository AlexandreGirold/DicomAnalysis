"""
Basic Tests Package
Collection of quality control tests for medical equipment
"""

from .base_test import BaseTest
from .niveau_helium import NiveauHeliumTest, test_helium_level
from .position_table import PositionTableV2Test, test_position_table_v2
from .alignement_laser import AlignementLaserTest, test_alignement_laser
from .mlc_leaf_jaw import MLCLeafJawTest, test_mlc_leaf_jaw

# Import daily, weekly, and monthly tests
import sys
import os

# Ensure services directory is in path
services_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if services_dir not in sys.path:
    sys.path.insert(0, services_dir)

# Manually build DAILY_TESTS dictionary to avoid circular imports
DAILY_TESTS = {}
try:
    # Import the safety systems test directly
    from services.daily.safety_systems import SafetySystemsTest, test_safety_systems
    DAILY_TESTS['safety_systems'] = {
        'class': SafetySystemsTest,
        'function': test_safety_systems,
        'description': 'ANSM - Vérification Quotidienne des Systèmes de Sécurité (ANSM 1.1, 1.5, TG284)',
        'category': 'daily'
    }
except ImportError as e:
    print(f"[DEBUG] Failed to import safety_systems: {e}")

WEEKLY_TESTS = {}
MONTHLY_TESTS = {}

__all__ = [
    'BaseTest',
    'NiveauHeliumTest',
    'PositionTableV2Test', 
    'AlignementLaserTest',
    'MLCLeafJawTest',
    'test_helium_level',
    'test_position_table_v2',
    'test_alignement_laser',
    'test_mlc_leaf_jaw'
]

# Test registry for easy access
AVAILABLE_TESTS = {
    'niveau_helium': {
        'class': NiveauHeliumTest,
        'function': test_helium_level,
        'description': 'Test du niveau d\'hélium - Doit être supérieur à 65%',
        'category': 'basic'
    },
    'position_table_v2': {
        'class': PositionTableV2Test,
        'function': test_position_table_v2,
        'description': 'Test de positionnement de la table',
        'category': 'basic'
    },
    'alignement_laser': {
        'class': AlignementLaserTest,
        'function': test_alignement_laser,
        'description': 'Test d\'alignement des marqueurs laser',
        'category': 'basic'
    },
    'mlc_leaf_jaw': {
        'class': MLCLeafJawTest,
        'function': test_mlc_leaf_jaw,
        'description': 'ANSM - Exactitude des positions de lames MLC - Analyse DICOM',
        'category': 'basic'
    }
}

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