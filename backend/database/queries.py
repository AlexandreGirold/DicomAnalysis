"""
Database query functions for retrieving test data
"""
from sqlalchemy import desc
from datetime import datetime
from typing import List, Dict, Optional
from .config import SessionLocal
from . import (
    SafetySystemsTest, NiveauHeliumTest, MLCLeafJawTest,
    MVICTest, PIQTTest, PositionTableV2Test,
    AlignementLaserTest, QuasarTest, IndiceQualityTest,
    MVICFenteV2Test, LeafPositionTest, LeafPositionResult
)


def _test_to_dict(test) -> Dict:
    """Convert test model to dictionary"""
    result = {
        'id': test.id,
        'operator': test.operator,
        'test_date': test.test_date.isoformat() if test.test_date else None,
        'upload_date': test.upload_date.isoformat() if test.upload_date else None,
        'notes': getattr(test, 'notes', None),
        'overall_result': getattr(test, 'overall_result', None)
    }
    
    # Add all other attributes
    for key in dir(test):
        if not key.startswith('_') and key not in ['metadata', 'registry', 'id', 'operator', 'test_date', 'upload_date', 'notes', 'overall_result']:
            value = getattr(test, key, None)
            if value is not None and not callable(value):
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, list) and len(value) > 0 and hasattr(value[0], '__table__'):
                    # Skip lists of relationship objects (e.g., blade_results, images)
                    continue
                elif not hasattr(value, '__table__'):  # Skip relationship objects
                    result[key] = value
    
    return result


def get_all_tests_generic(model_class, limit: int = 100, offset: int = 0, 
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """Generic function to get all tests for a given model"""
    db = SessionLocal()
    try:
        query = db.query(model_class).order_by(desc(model_class.test_date))
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(model_class.test_date >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(model_class.test_date <= end_dt)
        
        tests = query.offset(offset).limit(limit).all()
        return [_test_to_dict(test) for test in tests]
    finally:
        db.close()


def get_test_by_id_generic(model_class, test_id: int) -> Optional[Dict]:
    """Generic function to get a test by ID"""
    db = SessionLocal()
    try:
        test = db.query(model_class).filter(model_class.id == test_id).first()
        return _test_to_dict(test) if test else None
    finally:
        db.close()


def delete_test_by_id_generic(model_class, test_id: int) -> bool:
    """Generic function to delete a test by ID"""
    db = SessionLocal()
    try:
        test = db.query(model_class).filter(model_class.id == test_id).first()
        if test:
            db.delete(test)
            db.commit()
            return True
        return False
    finally:
        db.close()


# Safety Systems (Daily)
def get_all_safety_systems_tests(limit: int = 100, offset: int = 0, 
                                  start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(SafetySystemsTest, limit, offset, start_date, end_date)


def get_safety_systems_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(SafetySystemsTest, test_id)


def delete_safety_systems_test(test_id: int) -> bool:
    return delete_test_by_id_generic(SafetySystemsTest, test_id)


# Niveau Helium (Weekly)
def get_all_niveau_helium_tests(limit: int = 100, offset: int = 0, 
                                 start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(NiveauHeliumTest, limit, offset, start_date, end_date)


def get_niveau_helium_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(NiveauHeliumTest, test_id)


def delete_niveau_helium_test(test_id: int) -> bool:
    return delete_test_by_id_generic(NiveauHeliumTest, test_id)


# MLC Leaf Jaw (Weekly)
def get_all_mlc_test_sessions(limit: int = 100, offset: int = 0, 
                               start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(MLCLeafJawTest, limit, offset, start_date, end_date)


def get_mlc_test_session_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(MLCLeafJawTest, test_id)


def delete_mlc_test_session(test_id: int) -> bool:
    return delete_test_by_id_generic(MLCLeafJawTest, test_id)


# MVIC (Weekly)
def get_all_mvic_test_sessions(limit: int = 100, offset: int = 0, 
                                start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(MVICTest, limit, offset, start_date, end_date)


def get_mvic_test_session_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(MVICTest, test_id)


def delete_mvic_test_session(test_id: int) -> bool:
    return delete_test_by_id_generic(MVICTest, test_id)


# MVIC Fente V2 (Weekly)
def get_all_mvic_fente_v2_tests(limit: int = 100, offset: int = 0, 
                                 start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(MVICFenteV2Test, limit, offset, start_date, end_date)


def get_mvic_fente_v2_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(MVICFenteV2Test, test_id)


def delete_mvic_fente_v2_test(test_id: int) -> bool:
    return delete_test_by_id_generic(MVICFenteV2Test, test_id)


# PIQT (Weekly)
def get_all_piqt_tests(limit: int = 100, offset: int = 0, 
                       start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(PIQTTest, limit, offset, start_date, end_date)


def get_piqt_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(PIQTTest, test_id)


def delete_piqt_test(test_id: int) -> bool:
    return delete_test_by_id_generic(PIQTTest, test_id)


# Position Table V2 (Monthly)
def get_all_position_table_tests(limit: int = 100, offset: int = 0, 
                                  start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(PositionTableV2Test, limit, offset, start_date, end_date)


def get_position_table_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(PositionTableV2Test, test_id)


def delete_position_table_test(test_id: int) -> bool:
    return delete_test_by_id_generic(PositionTableV2Test, test_id)


# Alignement Laser (Monthly)
def get_all_alignement_laser_tests(limit: int = 100, offset: int = 0, 
                                    start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(AlignementLaserTest, limit, offset, start_date, end_date)


def get_alignement_laser_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(AlignementLaserTest, test_id)


def delete_alignement_laser_test(test_id: int) -> bool:
    return delete_test_by_id_generic(AlignementLaserTest, test_id)


# Quasar (Monthly)
def get_all_quasar_tests(limit: int = 100, offset: int = 0, 
                         start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(QuasarTest, limit, offset, start_date, end_date)


def get_quasar_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(QuasarTest, test_id)


def delete_quasar_test(test_id: int) -> bool:
    return delete_test_by_id_generic(QuasarTest, test_id)


# Indice Quality (Monthly)
def get_all_indice_quality_tests(limit: int = 100, offset: int = 0, 
                                  start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    return get_all_tests_generic(IndiceQualityTest, limit, offset, start_date, end_date)


def get_indice_quality_test_by_id(test_id: int) -> Optional[Dict]:
    return get_test_by_id_generic(IndiceQualityTest, test_id)


def delete_indice_quality_test(test_id: int) -> bool:
    return delete_test_by_id_generic(IndiceQualityTest, test_id)


# Leaf Position (Weekly)
def get_all_leaf_position_tests(limit: int = 100, offset: int = 0, 
                                 start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """Get all Leaf Position tests with blade results and image averages"""
    from .weekly_leaf_position_images import LeafPositionImage
    
    db = SessionLocal()
    try:
        query = db.query(LeafPositionTest).order_by(desc(LeafPositionTest.test_date))
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(LeafPositionTest.test_date >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(LeafPositionTest.test_date <= end_dt)
        
        tests = query.offset(offset).limit(limit).all()
        
        result = []
        for test in tests:
            test_dict = _test_to_dict(test)
            
            # Add blade results
            blade_results = db.query(LeafPositionResult).filter(
                LeafPositionResult.test_id == test.id
            ).all()
            test_dict['blade_results'] = [
                {
                    'image_number': br.image_number,
                    'filename': br.filename,
                    'blade_pair': br.blade_pair,
                    'position_u_px': br.position_u_px,
                    'v_sup_px': br.v_sup_px,
                    'v_inf_px': br.v_inf_px,
                    'distance_sup_mm': br.distance_sup_mm,
                    'distance_inf_mm': br.distance_inf_mm,
                    'length_mm': br.length_mm,
                    'field_size_mm': br.field_size_mm,
                    'is_valid': br.is_valid,
                    'status_message': br.status_message
                }
                for br in blade_results
            ]
            
            # Add image averages
            image_records = db.query(LeafPositionImage).filter(
                LeafPositionImage.test_id == test.id
            ).all()
            test_dict['image_averages'] = [
                {
                    'image_number': img.image_number,
                    'identified_image_number': img.identified_image_number,
                    'filename': img.filename,
                    'top_average': img.top_average,
                    'bottom_average': img.bottom_average
                }
                for img in image_records
            ]
            
            result.append(test_dict)
        
        return result
    finally:
        db.close()

def get_leaf_position_test_by_id(test_id: int) -> Optional[Dict]:
    """Get a Leaf Position test by ID with all blade results and image averages"""
    db = SessionLocal()
    try:
        test = db.query(LeafPositionTest).filter(LeafPositionTest.id == test_id).first()
        if not test:
            return None
        
        # Force load blade_results BEFORE closing session
        # Access the relationship to trigger loading
        _ = len(test.blade_results)
        _ = len(test.images)
        
        test_dict = _test_to_dict(test)
        
        # Manually add blade results from the loaded relationship
        test_dict['blade_results'] = [
            {
                'image_number': br.image_number,
                'filename': br.filename,
                'blade_pair': br.blade_pair,
                'position_u_px': br.position_u_px,
                'v_sup_px': br.v_sup_px,
                'v_inf_px': br.v_inf_px,
                'distance_sup_mm': br.distance_sup_mm,
                'distance_inf_mm': br.distance_inf_mm,
                'length_mm': br.length_mm,
                'field_size_mm': br.field_size_mm,
                'is_valid': br.is_valid,
                'status_message': br.status_message
            }
            for br in test.blade_results
        ]
        
        # Add image averages from the images relationship
        test_dict['image_averages'] = [
            {
                'image_number': img.image_number,
                'identified_image_number': img.identified_image_number,
                'filename': img.filename,
                'top_average': img.top_average,
                'bottom_average': img.bottom_average
            }
            for img in test.images
        ]
        
        return test_dict
    finally:
        db.close()


def delete_leaf_position_test(test_id: int) -> bool:
    """Delete a Leaf Position test and all associated blade results"""
    db = SessionLocal()
    try:
        # Delete associated blade results first
        db.query(LeafPositionResult).filter(LeafPositionResult.test_id == test_id).delete()
        
        # Delete test
        test = db.query(LeafPositionTest).filter(LeafPositionTest.id == test_id).first()
        if test:
            db.delete(test)
            db.commit()
            return True
        return False
    finally:
        db.close()

