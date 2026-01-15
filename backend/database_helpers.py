"""
Database Helper Functions
Common utilities for saving test results to database
"""

from database import (
    SessionLocal,
    MVICTest, MVICResult,
    MVICFenteV2Test, MVICFenteV2Result,
    MLCLeafJawTest,
    NiveauHeliumTest, NiveauHeliumResult,
    PIQTTest, PIQTResult,
    LeafPositionTest, LeafPositionResult,
    SafetySystemsTest,
    PositionTableV2Test,
    AlignementLaserTest,
    QuasarTest,
    IndiceQualityTest
)
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import os
import json

logger = logging.getLogger(__name__)


def update_visualization_paths(test_id: int, test_type: str, paths: List[str]) -> bool:
    """
    Update visualization_paths field for a test
    
    Args:
        test_id: Database ID of the test
        test_type: Type of test (mlc, mvic, mvic_fente_v2)
        paths: List of relative paths to visualization files
        
    Returns:
        bool: True if successful
    """
    db = SessionLocal()
    try:
        # Map test type to database model
        test_models = {
            'mlc': MLCLeafJawTest,
            'mvic': MVICTest,
            'mvic_fente_v2': MVICFenteV2Test,
            'leaf_position': LeafPositionTest
        }
        
        model = test_models.get(test_type)
        if not model:
            logger.error(f"Unknown test type: {test_type}")
            return False
        
        test = db.query(model).filter(model.id == test_id).first()
        if not test:
            logger.error(f"Test not found: {test_type} ID {test_id}")
            return False
        
        test.visualization_paths = json.dumps(paths)
        db.commit()
        logger.info(f"✓ Updated visualization paths for {test_type} test {test_id}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating visualization paths: {e}")
        return False
    finally:
        db.close()



def save_mvic_to_database(
    operator: str,
    test_date: datetime,
    overall_result: str,
    results: List[Dict[str, Any]],
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None,
    file_results: Optional[List[Dict[str, Any]]] = None
) -> int:
    """
    Save MVIC-Champ test results to database
    
    Args:
        operator: Name of operator
        test_date: Test date
        overall_result: PASS/FAIL/WARNING
        results: List of results for each of 5 images (legacy format)
        notes: Optional notes
        filenames: List of filenames
        file_results: Optional list of file-level results for display (contains detailed measurements)
    
    Returns:
        test_id: ID of saved test
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone
        
        # Create main test record
        test = MVICTest(
            test_date=test_date,
            operator=operator,
            overall_result=overall_result,
            notes=notes,
            upload_date=datetime.now(timezone.utc),
            filenames=",".join([os.path.basename(f) for f in filenames]) if filenames else None,
            file_results=json.dumps(file_results) if file_results else None
        )
        db.add(test)
        db.flush()  # Get the test ID
        
        # Save results for each image
        for i, result in enumerate(results, 1):
            # Try to get more detailed data from file_results if available
            filename = os.path.basename(filenames[i-1]) if filenames and i <= len(filenames) else None
            
            # Extract corner angles from file_results if available
            top_left = result.get('top_left_angle', 0)
            top_right = result.get('top_right_angle', 0)
            bottom_left = result.get('bottom_left_angle', 0)
            bottom_right = result.get('bottom_right_angle', 0)
            
            # If file_results is provided, try to extract angles from there
            if file_results and i <= len(file_results):
                file_result = file_results[i-1]
                measurements = file_result.get('measurements', {})
                if measurements:
                    top_left = measurements.get('top_left_angle', top_left)
                    top_right = measurements.get('top_right_angle', top_right)
                    bottom_left = measurements.get('bottom_left_angle', bottom_left)
                    bottom_right = measurements.get('bottom_right_angle', bottom_right)
            
            mvic_result = MVICResult(
                test_id=test.id,
                image_number=i,
                filename=filename,
                top_left_angle=top_left,
                top_right_angle=top_right,
                bottom_left_angle=bottom_left,
                bottom_right_angle=bottom_right,
                height=result.get('height', 0),
                width=result.get('width', 0)
            )
            db.add(mvic_result)
        
        db.commit()
        logger.info(f"✓ Saved MVIC-Champ test to database (ID: {test.id})")
        return test.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving MVIC-Champ test to database: {e}")
        raise
    finally:
        db.close()


def save_mvic_fente_v2_to_database(
    operator: str,
    test_date: datetime,
    overall_result: str,
    results: List[Dict[str, Any]],
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None,
    file_results: Optional[List[Dict[str, Any]]] = None
) -> int:
    """
    Save MVIC Fente V2 test results to database
    
    Args:
        operator: Name of operator
        test_date: Test date
        overall_result: PASS/FAIL/WARNING (usually PASS for info-only test)
        results: List of image results, each containing slits
        notes: Optional notes
        filenames: List of filenames
        file_results: Optional list of file-level results for display
    
    Returns:
        test_id: ID of saved test
    """
    db = SessionLocal()
    try:
        # Create main test record
        test = MVICFenteV2Test(
            test_date=test_date,
            operator=operator,
            overall_result=overall_result,
            notes=notes,
            filenames=",".join([os.path.basename(f) for f in filenames]) if filenames else None,
            file_results=json.dumps(file_results) if file_results else None
        )
        db.add(test)
        db.flush()
        
        # Save results for each slit in each image
        for image_idx, image_result in enumerate(results, 1):
            filename = os.path.basename(filenames[image_idx-1]) if filenames and image_idx <= len(filenames) else None
            
            # Handle both dict and string (skip strings, they're not valid)
            if not isinstance(image_result, dict):
                logger.warning(f"Skipping non-dict image_result at index {image_idx}: {type(image_result)}")
                continue
            
            # Each image can have multiple slits
            slits = image_result.get('slits', [])
            for slit_idx, slit in enumerate(slits, 1):
                fente_result = MVICFenteV2Result(
                    test_id=test.id,
                    image_number=image_idx,
                    filename=filename,
                    slit_number=slit_idx,
                    width_mm=slit.get('width_mm', 0),
                    height_pixels=slit.get('height_pixels', 0),
                    center_u=slit.get('center_u'),
                    center_v=slit.get('center_v')
                )
                db.add(fente_result)
        
        db.commit()
        logger.info(f"✓ Saved MVIC Fente V2 test to database (ID: {test.id})")
        return test.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving MVIC Fente V2 test to database: {e}")
        raise
    finally:
        db.close()


def save_leaf_position_to_database(
    operator: str,
    test_date: datetime,
    overall_result: str,
    results: List[Dict[str, Any]],
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None,
    file_results: Optional[List[Dict[str, Any]]] = None,
    visualization_paths: Optional[List[str]] = None
) -> int:
    """
    Save Leaf Position test results to database
    
    Args:
        operator: Name of operator
        test_date: Test date
        overall_result: PASS/FAIL/WARNING
        results: List of blade results from each image
        notes: Optional notes
        filenames: List of filenames
        file_results: Optional list of file-level results for display
        visualization_paths: List of visualization file paths
    
    Returns:
        test_id: ID of saved test
    """
    db = SessionLocal()
    try:
        # Create main test record
        test = LeafPositionTest(
            test_date=test_date,
            operator=operator,
            overall_result=overall_result,
            notes=notes,
            filenames=",".join([os.path.basename(f) for f in filenames]) if filenames else None,
            file_results=json.dumps(file_results) if file_results else None,
            visualization_paths=json.dumps(visualization_paths) if visualization_paths else None
        )
        db.add(test)
        db.flush()
        
        # Save results for each blade in each image
        logger.info(f"[SAVE-LEAF] Processing blade results - type: {type(results)}")
        
        # Check if results is a dict (old format with file_1_summary keys) or list (blade_results format)
        if isinstance(results, dict):
            logger.info(f"[SAVE-LEAF] Results is a dict with keys: {list(results.keys())}")
            # Results is the old format (file summaries), not individual blades
            # We should be empty here since old tests don't have blade data
            logger.warning("[SAVE-LEAF] Results is a dict, no blade data to save")
        elif isinstance(results, list):
            logger.info(f"[SAVE-LEAF] Processing {len(results)} blade result entries")
            
            for image_idx, image_result in enumerate(results, 1):
                filename = os.path.basename(filenames[image_idx-1]) if filenames and image_idx <= len(filenames) else None
                
                logger.info(f"[SAVE-LEAF] Image {image_idx}: type={type(image_result)}, keys={list(image_result.keys()) if isinstance(image_result, dict) else 'NOT A DICT'}")
                
                # Handle both dict and string (skip strings)
                if not isinstance(image_result, dict):
                    logger.warning(f"Skipping non-dict image_result at index {image_idx}: {type(image_result)}")
                    continue
                
                # Each image has multiple blade results
                blades = image_result.get('blades', [])
                logger.info(f"[SAVE-LEAF] Image {image_idx}: Found {len(blades)} blades")
                
                # Calculate averages for this image
                top_distances = [b.get('distance_sup_mm') for b in blades if b.get('distance_sup_mm') is not None]
                bottom_distances = [b.get('distance_inf_mm') for b in blades if b.get('distance_inf_mm') is not None]
                
                image_top_avg = sum(top_distances) / len(top_distances) if top_distances else None
                image_bottom_avg = sum(bottom_distances) / len(bottom_distances) if bottom_distances else None
                
                if image_top_avg is not None or image_bottom_avg is not None:
                    logger.info(f"[SAVE-LEAF] Image {image_idx} averages - Top: {image_top_avg:.2f}mm, Bottom: {image_bottom_avg:.2f}mm")
                
                for blade in blades:
                    blade_result = LeafPositionResult(
                        test_id=test.id,
                        image_number=image_idx,
                        filename=filename,
                        blade_pair=blade.get('pair'),
                        position_u_px=blade.get('position_u_px'),
                        v_sup_px=blade.get('v_sup_px'),
                        v_inf_px=blade.get('v_inf_px'),
                        distance_sup_mm=blade.get('distance_sup_mm'),
                        distance_inf_mm=blade.get('distance_inf_mm'),
                        length_mm=blade.get('length_mm'),
                        field_size_mm=blade.get('field_size_mm'),
                        is_valid=blade.get('is_valid', 'UNKNOWN'),
                        status_message=blade.get('status_message'),
                        blade_top_average=image_top_avg,
                        blade_bottom_average=image_bottom_avg
                    )
                    db.add(blade_result)
                    logger.info(f"[SAVE-LEAF] Added blade {blade.get('pair')} for test {test.id}")
        else:
            logger.warning(f"[SAVE-LEAF] Unexpected results type: {type(results)}")
        
        db.commit()
        logger.info(f"✓ Saved Leaf Position test to database (ID: {test.id})")
        return test.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving Leaf Position test to database: {e}")
        raise
    finally:
        db.close()


def save_mlc_leaf_jaw_to_database(
    operator: str,
    test_date: datetime,
    overall_result: str,
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None
) -> int:
    """
    Save MLC Leaf and Jaw test to database
    
    Args:
        operator: Name of operator
        test_date: Test date
        overall_result: PASS/FAIL/WARNING
        notes: Optional notes
        filenames: List of filenames
    
    Returns:
        test_id: ID of saved test
    """
    db = SessionLocal()
    try:
        test = MLCLeafJawTest(
            test_date=test_date,
            operator=operator,
            overall_result=overall_result,
            notes=notes,
            filenames=",".join([os.path.basename(f) for f in filenames]) if filenames else None
        )
        db.add(test)
        db.commit()
        logger.info(f"✓ Saved MLC Leaf Jaw test to database (ID: {test.id})")
        return test.id
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving MLC Leaf Jaw test: {e}")
        raise
    finally:
        db.close()


def save_niveau_helium_to_database(
    operator: str,
    test_date: datetime,
    overall_result: str,
    helium_level: float,
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None
) -> int:
    """Save Niveau Helium test to database"""
    db = SessionLocal()
    try:
        test = NiveauHeliumTest(
            test_date=test_date,
            operator=operator,
            helium_level=helium_level,  # Store directly in test table
            overall_result=overall_result,
            notes=notes,
            filenames=",".join([os.path.basename(f) for f in filenames]) if filenames else None
        )
        db.add(test)
        db.commit()
        logger.info(f"✓ Saved Niveau Helium test to database (ID: {test.id})")
        return test.id
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving Niveau Helium test: {e}")
        raise
    finally:
        db.close()


def save_generic_test_to_database(
    test_class,
    operator: str,
    test_date: datetime,
    overall_result: str,
    notes: Optional[str] = None,
    filenames: Optional[List[str]] = None,
    **extra_fields
) -> int:
    """
    Save generic test to database with optional test-specific fields
    
    Args:
        test_class: Database model class (e.g., PIQTTest, QuasarTest)
        operator: Name of operator
        test_date: Test date
        overall_result: PASS/FAIL/WARNING
        notes: Optional notes
        filenames: List of filenames
        **extra_fields: Test-specific fields (e.g., helium_level, position_175, etc.)
    
    Returns:
        test_id: ID of saved test
    """
    db = SessionLocal()
    try:
        # Get valid column names from the model class
        from sqlalchemy import inspect
        mapper = inspect(test_class)
        valid_columns = {col.key for col in mapper.columns}
        logger.debug(f"Valid columns for {test_class.__name__}: {valid_columns}")
        
        # Build test data dictionary with standard fields
        test_data = {
            'test_date': test_date,
            'operator': operator,
            'overall_result': overall_result,
            'notes': notes,
            'filenames': ",".join([os.path.basename(f) for f in filenames]) if filenames else None
        }
        
        # Add test-specific fields, but ONLY if they're valid columns
        for key, value in extra_fields.items():
            if key in valid_columns:
                if value is not None:  # Only add non-None values
                    test_data[key] = value
                    logger.debug(f"  ✓ Adding field: {key} = {value}")
            else:
                logger.debug(f"  ✗ Skipping unknown field: {key} = {value}")
        
        test = test_class(**test_data)
        db.add(test)
        db.commit()
        logger.info(f"✓ Saved {test_class.__name__} to database (ID: {test.id})")
        return test.id
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving {test_class.__name__}: {e}")
        raise
    finally:
        db.close()
