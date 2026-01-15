"""
Migration script to populate LeafPositionImage table for existing tests
This script calculates and saves image averages for tests that don't have them yet
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, LeafPositionTest, LeafPositionResult
from database.weekly_leaf_position_images import LeafPositionImage
from services.leaf_position_identifier import identify_all_images, validate_identification
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_existing_tests():
    """Populate LeafPositionImage table for tests that don't have image data"""
    db = SessionLocal()
    
    try:
        # Find all tests
        all_tests = db.query(LeafPositionTest).all()
        logger.info(f"Found {len(all_tests)} Leaf Position tests")
        
        for test in all_tests:
            # Check if this test already has image data
            existing_images = db.query(LeafPositionImage).filter(
                LeafPositionImage.test_id == test.id
            ).count()
            
            if existing_images > 0:
                logger.info(f"Test {test.id} already has {existing_images} image records - skipping")
                continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Migrating Test {test.id}")
            logger.info(f"{'='*60}")
            
            # Get blade results for this test
            blade_results = db.query(LeafPositionResult).filter(
                LeafPositionResult.test_id == test.id
            ).all()
            
            if not blade_results:
                logger.warning(f"Test {test.id} has no blade results - skipping")
                continue
            
            # Organize by image
            images_data = {}
            for br in blade_results:
                img_num = br.image_number
                if img_num not in images_data:
                    images_data[img_num] = {
                        'blades': [],
                        'filename': br.filename
                    }
                
                images_data[img_num]['blades'].append({
                    'distance_sup_mm': br.distance_sup_mm,
                    'distance_inf_mm': br.distance_inf_mm
                })
            
            logger.info(f"Found {len(images_data)} images for test {test.id}")
            
            # Calculate averages for each image
            image_data_for_identification = []
            
            for img_num in sorted(images_data.keys()):
                img = images_data[img_num]
                blades = img['blades']
                
                # Calculate averages
                top_distances = [b['distance_sup_mm'] for b in blades if b['distance_sup_mm'] is not None]
                bottom_distances = [b['distance_inf_mm'] for b in blades if b['distance_inf_mm'] is not None]
                
                top_avg = sum(top_distances) / len(top_distances) if top_distances else None
                bottom_avg = sum(bottom_distances) / len(bottom_distances) if bottom_distances else None
                
                if top_avg is not None and bottom_avg is not None:
                    image_data_for_identification.append({
                        'upload_order': img_num,
                        'filename': img['filename'],
                        'top_average': top_avg,
                        'bottom_average': bottom_avg
                    })
                    
                    logger.info(f"  Image {img_num}: top={top_avg:.2f}mm, bottom={bottom_avg:.2f}mm ({len(blades)} blades)")
            
            if len(image_data_for_identification) != 6:
                logger.warning(f"Test {test.id} has {len(image_data_for_identification)} images instead of 6 - proceeding anyway")
            
            # Identify positions
            if image_data_for_identification:
                identified_images = identify_all_images(image_data_for_identification)
                is_valid, errors = validate_identification(identified_images)
                
                if not is_valid:
                    logger.warning(f"Validation failed for test {test.id}: {errors}")
                
                # Save to database
                for img_data in identified_images:
                    image_record = LeafPositionImage(
                        test_id=test.id,
                        image_number=img_data['upload_order'],
                        identified_image_number=img_data.get('identified_position'),
                        filename=img_data['filename'],
                        top_average=img_data['top_average'],
                        bottom_average=img_data['bottom_average']
                    )
                    db.add(image_record)
                    logger.info(f"  ✓ Saved Image {img_data['upload_order']} → Position {img_data.get('identified_position')}")
                
                db.commit()
                logger.info(f"✓ Successfully migrated test {test.id}")
            else:
                logger.warning(f"No valid image data for test {test.id}")
        
        logger.info(f"\n{'='*60}")
        logger.info("Migration complete!")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during migration: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == '__main__':
    migrate_existing_tests()
