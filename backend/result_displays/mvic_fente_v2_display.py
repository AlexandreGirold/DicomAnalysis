"""
MVIC Fente Result Display
Retrieve and format MVIC Fente test results from database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mvic_fente_v2_test_by_id
from typing import Optional, Dict
import logging
import json

logger = logging.getLogger(__name__)


def display_mvic_fente_v2_result(test_id: int) -> Optional[Dict]:
    """
    Retrieve and format MVIC Fente test result from database
    
    Args:
        test_id: Database ID of the MVIC Fente test
        
    Returns:
        dict: Formatted test result with slit analysis
        None: If test not found
    """
    logger.info(f"[MVIC-FENTE-V2-DISPLAY] Retrieving test ID: {test_id}")
    
    test_data = get_mvic_fente_v2_test_by_id(test_id)
    
    if not test_data:
        logger.warning(f"[MVIC-FENTE-V2-DISPLAY] Test ID {test_id} not found")
        return None
    
    # Parse file_results if stored as JSON string
    file_results = []
    if test_data.get('file_results'):
        try:
            if isinstance(test_data['file_results'], str):
                file_results = json.loads(test_data['file_results'])
            else:
                file_results = test_data['file_results']
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[MVIC-FENTE-V2-DISPLAY] Failed to parse file_results: {e}")
    
    # Parse visualization_paths if stored as JSON string
    visualization_paths = []
    if test_data.get('visualization_paths'):
        try:
            if isinstance(test_data['visualization_paths'], str):
                visualization_paths = json.loads(test_data['visualization_paths'])
            else:
                visualization_paths = test_data['visualization_paths']
            # Convert backslashes to forward slashes for web URLs
            visualization_paths = [path.replace('\\', '/') for path in visualization_paths]
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[MVIC-FENTE-V2-DISPLAY] Failed to parse visualization_paths: {e}")
    
    # Format the output
    output = {
        'test_id': test_data['id'],
        'test_name': 'MVIC Fente - Slit Analysis',
        'test_date': test_data['test_date'],
        'operator': test_data['operator'],
        'upload_date': test_data['upload_date'],
        'overall_result': test_data['overall_result'],
        'notes': test_data.get('notes', ''),
        'filenames': test_data.get('filenames', '').split(',') if test_data.get('filenames') else [],
        
        # Slit analysis results
        'slit_results': file_results,
        
        # Visualization file paths
        'visualization_paths': visualization_paths
    }
    
    logger.info(f"[MVIC-FENTE-V2-DISPLAY] Successfully retrieved test {test_id} with {len(file_results)} slit measurements")
    return output
