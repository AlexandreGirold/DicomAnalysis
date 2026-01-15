"""
Visualization Storage Helper
Utilities for saving test visualizations as image files
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)

VISUALIZATIONS_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    '..', 'frontend', 'visualizations'
)


def save_visualization(
    base64_data: str,
    test_type: str,
    test_id: int,
    file_index: int,
    analysis_name: str = "",
    original_filename: str = ""
) -> Optional[str]:
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',', 1)[1]
        
        image_data = base64.b64decode(base64_data)
        
        # Create test type directory
        test_dir = os.path.join(VISUALIZATIONS_BASE_PATH, test_type)
        os.makedirs(test_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        analysis_suffix = f"_{analysis_name}" if analysis_name else ""
        filename = f"test_{test_id}_img_{file_index}{analysis_suffix}_{timestamp}.png"
        
        filepath = os.path.join(test_dir, filename)
        
        # Save image
        image = Image.open(io.BytesIO(image_data))
        image.save(filepath, 'PNG', optimize=True)
        
        relative_path = f"visualizations/{test_type}/{filename}"
        logger.info(f"Saved visualization: {relative_path}")
        
        return relative_path
        
    except Exception as e:
        logger.error(f"Failed to save visualization: {e}")
        return None


def save_multiple_visualizations(
    visualizations: list,
    test_type: str,
    test_id: int
) -> list:
    saved_visualizations = []
    
    for i, viz in enumerate(visualizations):
        if 'data' not in viz:
            logger.warning(f"Visualization {i} missing 'data' field")
            continue
            
        analysis_name = viz.get('name', '').split(':')[-1].strip().replace(' ', '_').lower()
        filename = viz.get('filename', '')
        
        file_path = save_visualization(
            base64_data=viz['data'],
            test_type=test_type,
            test_id=test_id,
            file_index=viz.get('index', i),
            analysis_name=analysis_name,
            original_filename=filename
        )
        
        if file_path:
            viz_with_path = viz.copy()
            viz_with_path['file_path'] = file_path
            saved_visualizations.append(viz_with_path)
        else:
            logger.error(f"Failed to save visualization {i}")
    
    logger.info(f"Saved {len(saved_visualizations)}/{len(visualizations)} visualizations")
    return saved_visualizations


def get_visualization_path(test_type: str, test_id: int, file_index: int = 0) -> Optional[str]:
    test_dir = os.path.join(VISUALIZATIONS_BASE_PATH, test_type)
    if not os.path.exists(test_dir):
        return None
    
    pattern = f"test_{test_id}_img_{file_index}_"
    for filename in os.listdir(test_dir):
        if filename.startswith(pattern):
            return os.path.join('visualizations', test_type, filename)
    
    return None


def cleanup_old_visualizations(test_type: str, test_id: int) -> int:
    test_dir = os.path.join(VISUALIZATIONS_BASE_PATH, test_type)
    if not os.path.exists(test_dir):
        return 0
    
    deleted = 0
    pattern = f"test_{test_id}_"
    
    for filename in os.listdir(test_dir):
        if filename.startswith(pattern):
            try:
                filepath = os.path.join(test_dir, filename)
                os.remove(filepath)
                deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete {filename}: {e}")
    
    logger.info(f"Cleaned up {deleted} old visualizations for {test_type} test {test_id}")
    return deleted
