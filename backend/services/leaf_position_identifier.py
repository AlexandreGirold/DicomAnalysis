"""
Exactitude du MLC - Leaf Position Image Identification
Identifies which reference profile (1-6) each image matches based on blade averages
"""
import logging
from typing import Dict, List, Tuple, Optional
import math

logger = logging.getLogger(__name__)


# Reference profiles: (top_average_mm, bottom_average_mm)
# These represent the expected values for each of the 6 standard positions
REFERENCE_PROFILES = {
    1: {'top': 40.0, 'bottom': 20.0},
    2: {'top': 30.0, 'bottom': 10.0},
    3: {'top': 20.0, 'bottom': 0.0},
    4: {'top': 0.0, 'bottom': -20.0},
    5: {'top': -10.0, 'bottom': -30.0},
    6: {'top': -20.0, 'bottom': -40.0}
}


def calculate_distance(top1: float, bottom1: float, top2: float, bottom2: float) -> float:
    """
    Calculate Euclidean distance between two (top, bottom) pairs
    
    Args:
        top1, bottom1: First point coordinates
        top2, bottom2: Second point coordinates
    
    Returns:
        Euclidean distance
    """
    return math.sqrt((top1 - top2) ** 2 + (bottom1 - bottom2) ** 2)


def identify_image_position(top_average: float, bottom_average: float) -> int:
    """
    Identify which reference profile (1-6) best matches the given averages
    
    Args:
        top_average: Average blade top position in mm
        bottom_average: Average blade bottom position in mm
    
    Returns:
        Image position (1-6) that best matches
    """
    min_distance = float('inf')
    best_match = 1
    
    for position, profile in REFERENCE_PROFILES.items():
        distance = calculate_distance(
            top_average, bottom_average,
            profile['top'], profile['bottom']
        )
        
        if distance < min_distance:
            min_distance = distance
            best_match = position
    
    logger.info(f"[IDENTIFY] (top={top_average:.2f}, bottom={bottom_average:.2f}) "
                f"→ Position {best_match} (distance={min_distance:.2f})")
    
    return best_match


def identify_all_images(image_data: List[Dict]) -> List[Dict]:
    """
    Identify positions for all images and ensure no duplicates
    
    Args:
        image_data: List of dicts with 'upload_order', 'top_average', 'bottom_average', 'filename'
    
    Returns:
        List of dicts with added 'identified_position' field
    """
    # First pass: identify all images
    for img in image_data:
        if img['top_average'] is not None and img['bottom_average'] is not None:
            img['identified_position'] = identify_image_position(
                img['top_average'], 
                img['bottom_average']
            )
        else:
            logger.warning(f"[IDENTIFY] Image {img['upload_order']} has no averages - cannot identify")
            img['identified_position'] = None
    
    # Check for conflicts (multiple images matching same position)
    position_counts = {}
    for img in image_data:
        pos = img.get('identified_position')
        if pos is not None:
            position_counts[pos] = position_counts.get(pos, 0) + 1
    
    # Log any conflicts
    conflicts = [pos for pos, count in position_counts.items() if count > 1]
    if conflicts:
        logger.warning(f"[IDENTIFY] Conflicts detected: positions {conflicts} matched multiple images")
        logger.warning("[IDENTIFY] Using closest match for each position")
        
        # Resolve conflicts by keeping only the closest match for each position
        for conflict_pos in conflicts:
            # Get all images that matched this position
            matching_images = [img for img in image_data if img.get('identified_position') == conflict_pos]
            
            # Calculate distance for each
            for img in matching_images:
                ref = REFERENCE_PROFILES[conflict_pos]
                img['_distance_to_match'] = calculate_distance(
                    img['top_average'], img['bottom_average'],
                    ref['top'], ref['bottom']
                )
            
            # Sort by distance and keep only the closest
            matching_images.sort(key=lambda x: x.get('_distance_to_match', float('inf')))
            
            # Reassign others to their second-best match
            for img in matching_images[1:]:
                logger.warning(f"[IDENTIFY] Image {img['upload_order']} reassigned from position {conflict_pos}")
                # Find second-best match
                distances = []
                for pos, profile in REFERENCE_PROFILES.items():
                    if pos != conflict_pos:
                        dist = calculate_distance(
                            img['top_average'], img['bottom_average'],
                            profile['top'], profile['bottom']
                        )
                        distances.append((pos, dist))
                
                distances.sort(key=lambda x: x[1])
                img['identified_position'] = distances[0][0]
                logger.info(f"[IDENTIFY] Reassigned to position {distances[0][0]} (distance={distances[0][1]:.2f})")
    
    # Log final assignments
    logger.info("[IDENTIFY] Final image assignments:")
    for img in sorted(image_data, key=lambda x: x.get('identified_position') or 99):
        logger.info(f"  Upload order {img['upload_order']} → Position {img.get('identified_position')} "
                   f"({img.get('filename', 'no filename')})")
    
    return image_data


def validate_identification(image_data: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate that all 6 positions are uniquely identified
    
    Args:
        image_data: List of dicts with 'identified_position'
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Check we have 6 images
    if len(image_data) != 6:
        errors.append(f"Expected 6 images, got {len(image_data)}")
    
    # Check all positions are identified
    identified = [img.get('identified_position') for img in image_data if img.get('identified_position') is not None]
    if len(identified) != 6:
        errors.append(f"Not all images were identified: {len(identified)}/6")
    
    # Check for duplicates
    if len(identified) != len(set(identified)):
        duplicates = [pos for pos in identified if identified.count(pos) > 1]
        errors.append(f"Duplicate positions found: {set(duplicates)}")
    
    # Check all positions 1-6 are present
    expected = set(range(1, 7))
    actual = set(identified)
    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        if missing:
            errors.append(f"Missing positions: {sorted(missing)}")
        if extra:
            errors.append(f"Unexpected positions: {sorted(extra)}")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info("[VALIDATE] ✓ All 6 images uniquely identified")
    else:
        logger.error(f"[VALIDATE] ✗ Validation failed: {'; '.join(errors)}")
    
    return is_valid, errors
