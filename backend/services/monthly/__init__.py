"""
Monthly Tests Package
Collection of monthly quality control tests for medical equipment
"""

from .position_table import PositionTableV2Test, test_position_table_v2
from .alignement_laser import AlignementLaserTest, test_alignement_laser
from .quasar import QuasarTest, test_quasar
from .indice_quality import IndiceQualityTest, test_indice_quality

# Monthly test registry
MONTHLY_TESTS = {
    'position_table_v2': {
        'class': PositionTableV2Test,
        'function': test_position_table_v2,
        'description': 'ANSM - Laser et Table - Test de positionnement',
        'category': 'monthly'
    },
    'alignement_laser': {
        'class': AlignementLaserTest,
        'function': test_alignement_laser,
        'description': 'ANSM - Alignement Laser - Test des marqueurs',
        'category': 'monthly'
    },
    'quasar': {
        'class': QuasarTest,
        'function': test_quasar,
        'description': 'ANSM - Test QUASAR - Latence du gating et Précision',
        'category': 'monthly'
    },
    'indice_quality': {
        'class': IndiceQualityTest,
        'function': test_indice_quality,
        'description': 'ANSM - Indice de Qualité - Test D10/D20 et D5/D15',
        'category': 'monthly'
    }
}

def get_monthly_tests():
    """
    Get list of all available monthly tests
    
    Returns:
        dict: Dictionary of available monthly tests with their descriptions
    """
    return {
        test_id: {
            'description': test_info['description'],
            'class_name': test_info['class'].__name__,
            'category': test_info['category']
        }
        for test_id, test_info in MONTHLY_TESTS.items()
    }
