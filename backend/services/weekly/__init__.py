"""
Weekly Tests Package
Collection of weekly quality control tests for medical equipment
all the weekly tests, this is the same for monthly and daily and if added later yearly
"""
from .niveau_helium import NiveauHeliumTest, test_helium_level
from .PIQT import PIQTTest, test_piqt
from .MVIC import MVICTest, test_mvic
from .MVIC_fente import MVICFenteTest, test_mvic_fente, MVICFenteV2Test, test_mvic_fente_v2
import sys
import os
services_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if services_dir not in sys.path:
    sys.path.insert(0, services_dir)

from basic_tests.mlc_leaf_jaw import MLCLeafJawTest, test_mlc_leaf_jaw

# THIS IS WHERE YOU ADD NEW WEEKLY TESTS -> 
WEEKLY_TESTS = {
    'niveau_helium': {
        'class': NiveauHeliumTest,
        'function': test_helium_level,
        'description': 'ANSM - Test du niveau d\'hélium - Doit être supérieur à 65%',
        'category': 'weekly'
    },
    'mlc_leaf_jaw': {
        'class': MLCLeafJawTest,
        'function': test_mlc_leaf_jaw,
        'description': 'ANSM - Exactitude des positions de lames MLC - Analyse DICOM',
        'category': 'weekly'
    },
    'mvic': {
        'class': MVICTest,
        'function': test_mvic,
        'description': 'MVIC - MV Imaging Check - Validation taille et forme du champ (±1mm, 90° ±1°)',
        'category': 'weekly'
    },
    'piqt': {
        'class': PIQTTest,
        'function': test_piqt,
        'description': 'PIQT - Philips Image Quality Test - Parse rapport HTML',
        'category': 'weekly'
    },
    'mvic_fente': {
        'class': MVICFenteTest,
        'function': test_mvic_fente,
        'description': 'MVIC Fente - Analyse des fentes MLC individuelles - Largeur, hauteur, séparation',
        'category': 'weekly'
    },
    'mvic_fente_v2': {
        'class': MVICFenteV2Test,
        'function': test_mvic_fente_v2,
        'description': 'MVIC Fente V2 - Détection par contours (méthode ImageJ) - Largeur et espacement',
        'category': 'weekly'
    }
}

def get_weekly_tests():
    """
    Get list of all available weekly tests
    
    Returns:
        dict: Dictionary of available weekly tests with their descriptions
    """
    return {
        test_id: {
            'description': test_info['description'],
            'class_name': test_info['class'].__name__,
            'category': test_info['category']
        }
        for test_id, test_info in WEEKLY_TESTS.items()
    }
