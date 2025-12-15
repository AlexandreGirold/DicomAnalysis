"""
Niveau Helium Result Display
Retrieve and format Helium level test results from database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_niveau_helium_test_by_id
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def display_niveau_helium_result(test_id: int) -> Optional[Dict]:
    """
    Retrieve and format Niveau Helium test result from database
    
    Args:
        test_id: Database ID of the Niveau Helium test
        
    Returns:
        dict: Formatted test result with helium level
        None: If test not found
    """
    logger.info(f"[HELIUM-DISPLAY] Retrieving test ID: {test_id}")
    
    test_data = get_niveau_helium_test_by_id(test_id)
    
    if not test_data:
        logger.warning(f"[HELIUM-DISPLAY] Test ID {test_id} not found")
        return None
    
    # Format the output
    output = {
        'test_id': test_data['id'],
        'test_name': 'Niveau Helium - Helium Level Check',
        'test_date': test_data['test_date'],
        'operator': test_data['operator'],
        'upload_date': test_data['upload_date'],
        'overall_result': test_data['overall_result'],
        'notes': test_data.get('notes', ''),
        'filenames': test_data.get('filenames', '').split(',') if test_data.get('filenames') else [],
        
        # Helium level measurement
        'helium_level': test_data.get('helium_level'),
        'tolerance': '≥ 65%',
        
        'visualizations': []
    }
    
    logger.info(f"[HELIUM-DISPLAY] Successfully retrieved test {test_id} with level {test_data.get('helium_level')}%")
    return output
