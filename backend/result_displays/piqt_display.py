"""
PIQT Result Display
Retrieve and format PIQT test results from database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_piqt_test_by_id
from database.config import SessionLocal
from database.weekly_tests import PIQTTest, PIQTResult
from typing import Optional, Dict, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


def _get_unit_for_field(field_name: str) -> str:
    """Get the appropriate unit for a field based on its name"""
    field_lower = field_name.lower()
    if 'fwhm' in field_lower or 'pxl_size' in field_lower or 'slice_int' in field_lower:
        return 'mm'
    elif 'perc_dif' in field_lower or 'unif' in field_lower:
        return '%'
    return ''


def _format_piqt_details_from_data(test_data: Dict, results: List[PIQTResult]) -> Dict:
    """
    Format detailed PIQT results by category from test data
    
    Args:
        test_data: Dictionary of all test data
        results: List of PIQTResult records
        
    Returns:
        dict: Organized results by measurement category
    """
    formatted = {
        'flood_field_uniformity': {'ffu1': {}, 'ffu2': {}},
        'spatial_linearity': {},
        'slice_profile': {},
        'spatial_resolution': {}
    }
    
    # Extract FFU1 data
    for key, value in test_data.items():
        if value is not None:
            if key.startswith('ffu1_'):
                formatted['flood_field_uniformity']['ffu1'][key.replace('ffu1_', '')] = value
            elif key.startswith('ffu2_'):
                formatted['flood_field_uniformity']['ffu2'][key.replace('ffu2_', '')] = value
            elif key.startswith('spatial_linearity_'):
                formatted['spatial_linearity'][key.replace('spatial_linearity_', '')] = value
            elif key.startswith('slice_profile_'):
                formatted['slice_profile'][key.replace('slice_profile_', '')] = value
            elif key.startswith('spatial_resolution_'):
                formatted['spatial_resolution'][key.replace('spatial_resolution_', '')] = value
    
    # Also include data from PIQTResult if available
    if results:
        result = results[0]
        # Add to FFU1
        if result.ffu1_nema_sn_b1 is not None:
            formatted['flood_field_uniformity']['ffu1']['nema_sn_b1'] = result.ffu1_nema_sn_b1
        if result.ffu1_nema_int_unif1 is not None:
            formatted['flood_field_uniformity']['ffu1']['nema_int_unif1'] = result.ffu1_nema_int_unif1
        # Add more as needed...
    
    return formatted


def display_piqt_result(test_id: int) -> Optional[Dict]:
    """
    Retrieve and format PIQT test result from database
    
    Args:
        test_id: Database ID of the PIQT test
        
    Returns:
        dict: Formatted test result with all data and visualizations
        None: If test not found
    """
    logger.info(f"[PIQT-DISPLAY] Retrieving test ID: {test_id}")
    
    # Use the query function which returns all stored data
    test_data = get_piqt_test_by_id(test_id)
    
    if not test_data:
        logger.warning(f"[PIQT-DISPLAY] Test ID {test_id} not found")
        return None
    
    # Get detailed results from database
    session = SessionLocal()
    try:
        results = session.query(PIQTResult).filter(PIQTResult.test_id == test_id).all()
    finally:
        session.close()
    
    # Extract results from the stored data
    results_list = []
    if test_data.get('results_json'):
        try:
            results_list = json.loads(test_data['results_json'])
            logger.info(f"[PIQT-DISPLAY] Loaded {len(results_list)} results from JSON")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[PIQT-DISPLAY] Failed to parse results_json: {e}")
    
    # If no results from JSON, build from individual stored fields
    if not results_list:
        for key, value in test_data.items():
            if value is not None and key not in ['id', 'operator', 'test_date', 'upload_date', 'notes', 'overall_result', 'filenames', 'results_json']:
                # Format the key for display
                display_name = key.replace('_', ' ').title()
                results_list.append({
                    'name': display_name,
                    'value': value,
                    'status': 'INFO',
                    'unit': _get_unit_for_field(key),
                    'tolerance': 'N/A'
                })
    
    # Format the output similar to the original test execution
    output = {
        'test_id': test_data['id'],
        'test_name': 'PIQT - Philips Image Quality Test',
        'test_date': test_data['test_date'],
        'operator': test_data['operator'],
        'upload_date': test_data['upload_date'],
        'overall_result': test_data['overall_result'],
        'notes': test_data.get('notes'),
        'filenames': test_data.get('filenames', '').split(',') if test_data.get('filenames') else [],
        
        # Detailed results organized by category
        'detailed_results': _format_piqt_details_from_data(test_data, results),
        
        # Results formatted for display (matching original test output structure)
        'results': results_list,
        
        # Visualizations (if any were stored)
        'visualizations': []
    }
    
    logger.info(f"[PIQT-DISPLAY] Successfully retrieved test {test_id} with {len(results_list)} measurements")
    return output


def test_piqt_display():
    """Test function to demonstrate result display"""
    # Example: Display test ID 1
    result = display_piqt_result(1)
    if result:
        print("=" * 80)
        print(f"Test: {result['test_name']}")
        print(f"Date: {result['test_date']}")
        print(f"Operator: {result['operator']}")
        print(f"Result: {result['overall_result']}")
        print("=" * 80)
        print("\nSummary:")
        for key, value in result['summary'].items():
            print(f"  {key}: {value}")
        print("\nDetailed Results:")
        for item in result['results']:
            print(f"  {item['name']}: {item['value']} {item['unit']}")
    else:
        print("Test not found")


if __name__ == "__main__":
    test_piqt_display()
