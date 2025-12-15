"""
MVIC Result Display
Retrieve and format MVIC test results from database (5 images with dimensions and angles)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mvic_test_session_by_id
from typing import Optional, Dict
import logging
import json

logger = logging.getLogger(__name__)


def display_mvic_result(test_id: int) -> Optional[Dict]:
    """
    Retrieve and format MVIC test result from database
    
    Args:
        test_id: Database ID of the MVIC test
        
    Returns:
        dict: Formatted test result with all 5 image analyses
        None: If test not found
    """
    logger.info(f"[MVIC-DISPLAY] Retrieving test ID: {test_id}")
    
    test_data = get_mvic_test_session_by_id(test_id)
    
    if not test_data:
        logger.warning(f"[MVIC-DISPLAY] Test ID {test_id} not found")
        return None
    
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
            logger.warning(f"[MVIC-DISPLAY] Failed to parse visualization_paths: {e}")
    
    # Parse file_results if stored as JSON string
    file_results = []
    if test_data.get('file_results'):
        try:
            if isinstance(test_data['file_results'], str):
                file_results = json.loads(test_data['file_results'])
            else:
                file_results = test_data['file_results']
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[MVIC-DISPLAY] Failed to parse file_results: {e}")
    
    # Format the output
    output = {
        'test_id': test_data['id'],
        'test_name': 'MVIC-Champ Test',
        'test_date': test_data['test_date'],
        'operator': test_data['operator'],
        'upload_date': test_data['upload_date'],
        'overall_result': test_data['overall_result'],
        'notes': test_data.get('notes', ''),
        'filenames': test_data.get('filenames', '').split(',') if test_data.get('filenames') else [],
        'visualization_paths': visualization_paths,
        'file_results': file_results,
        
        # 5 image analyses - get data from MVICResult records via the API route
        'images': []
    }
    
    # Try to get image data from MVICResult records if available
    # The GET /mvic-test-sessions/{id} endpoint should have already populated this
    # But if we're using display endpoint, we need to query MVICResult
    try:
        from database import SessionLocal, MVICResult
        db = SessionLocal()
        results = db.query(MVICResult).filter(MVICResult.test_id == test_data['id']).order_by(MVICResult.image_number).all()
        
        if results:
            for r in results:
                # Calculate average and std dev of corner angles
                angles = [r.top_left_angle, r.top_right_angle, r.bottom_left_angle, r.bottom_right_angle]
                avg_angle = sum(angles) / len(angles)
                # Calculate standard deviation
                variance = sum((x - avg_angle) ** 2 for x in angles) / len(angles)
                std_dev = variance ** 0.5
                
                output['images'].append({
                    'number': r.image_number,
                    'width_mm': r.width,
                    'height_mm': r.height,
                    'avg_angle': round(avg_angle, 3),  # Show 3 decimal places
                    'angle_std_dev': round(std_dev, 3),
                    'filename': r.filename,
                    # Add individual corner angles
                    'top_left_angle': r.top_left_angle,
                    'top_right_angle': r.top_right_angle,
                    'bottom_left_angle': r.bottom_left_angle,
                    'bottom_right_angle': r.bottom_right_angle
                })
        else:
            # Fallback: if no MVICResult records, create empty image entries
            for i in range(1, 6):
                output['images'].append({
                    'number': i,
                    'width_mm': None,
                    'height_mm': None,
                    'avg_angle': None,
                    'angle_std_dev': None
                })
        
        db.close()
    except Exception as e:
        logger.error(f"[MVIC-DISPLAY] Error retrieving MVICResult records: {e}")
        # Fallback: create empty image entries
        for i in range(1, 6):
            output['images'].append({
                'number': i,
                'width_mm': None,
                'height_mm': None,
                'avg_angle': None,
                'angle_std_dev': None
            })
    
    output['visualizations'] = []
    
    logger.info(f"[MVIC-DISPLAY] Successfully retrieved test {test_id} with 5 image analyses")
    return output
