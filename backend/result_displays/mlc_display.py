"""
MLC Leaf & Jaw Result Display
Retrieve and format MLC test results from database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mlc_test_session_by_id
from typing import Optional, Dict
import logging
import json

logger = logging.getLogger(__name__)


def display_mlc_result(test_id: int) -> Optional[Dict]:
    """
    Retrieve and format MLC test result from database
    
    Args:
        test_id: Database ID of the MLC test
        
    Returns:
        dict: Formatted test result with all data and visualizations
        None: If test not found
    """
    logger.info(f"[MLC-DISPLAY] Retrieving test ID: {test_id}")
    
    test_data = get_mlc_test_session_by_id(test_id)
    
    if not test_data:
        logger.warning(f"[MLC-DISPLAY] Test ID {test_id} not found")
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
            logger.warning(f"[MLC-DISPLAY] Failed to parse file_results: {e}")
    
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
            logger.warning(f"[MLC-DISPLAY] Failed to parse visualization_paths: {e}")
    
    # Format the output
    output = {
        'test_id': test_data['id'],
        'test_name': 'MLC Leaf & Jaw Test',
        'test_date': test_data['test_date'],
        'operator': test_data['operator'],
        'upload_date': test_data['upload_date'],
        'overall_result': test_data['overall_result'],
        'notes': test_data.get('notes', ''),
        'filenames': test_data.get('filenames', '').split(',') if test_data.get('filenames') else [],
        'visualization_paths': visualization_paths,
        
        # Test summary data
        'test1_center': test_data.get('test1_center'),
        'test2_jaw': test_data.get('test2_jaw'),
        'test3_blade_top': test_data.get('test3_blade_top'),
        'test4_blade_bottom': test_data.get('test4_blade_bottom'),
        'test5_angle': test_data.get('test5_angle'),
        
        # Detailed file results (per-blade measurements)
        'file_results': file_results,
        
        # Visualizations
        'visualizations': []
    }
    
    logger.info(f"[MLC-DISPLAY] Successfully retrieved test {test_id} with {len(file_results)} blade measurements")
    return output
