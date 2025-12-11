"""
MVIC Routes - Endpoints for MVIC (MV Imaging Control) tests
Includes test sessions, analysis, trends, and results
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import database as db
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/mvic-test-sessions")
async def save_mvic_test_session(data: dict):
    """
    Save MVIC test session with all 5 images
    
    Expected data structure:
    {
        "test_date": "2025-11-26T10:30:00",
        "operator": "Dr. Smith",
        "image1": {"width_mm": 150.2, "height_mm": 85.1, "avg_angle": 90.1, "angle_std_dev": 0.5},
        "image2": {"width_mm": 85.3, "height_mm": 85.2, "avg_angle": 89.9, "angle_std_dev": 0.6},
        "image3": {"width_mm": 50.1, "height_mm": 50.0, "avg_angle": 90.2, "angle_std_dev": 0.4},
        "image4": {"width_mm": 150.0, "height_mm": 85.0, "avg_angle": 90.0, "angle_std_dev": 0.5},
        "image5": {"width_mm": 85.0, "height_mm": 85.1, "avg_angle": 89.8, "angle_std_dev": 0.7},
        "notes": "Optional notes",
        "overall_result": "PASS"
    }
    """
    logger.info("[MVIC-SESSION] Saving MVIC test session")
    try:
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except:
                test_date = datetime.now()
        else:
            test_date = datetime.now()
        
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        from database_helpers import save_mvic_to_database
        
        results = []
        for i in range(1, 6):
            img_data = data.get(f'image{i}', {})
            avg_angle = img_data.get('avg_angle', 90.0)
            results.append({
                'top_left_angle': img_data.get('top_left_angle', avg_angle),
                'top_right_angle': img_data.get('top_right_angle', avg_angle),
                'bottom_left_angle': img_data.get('bottom_left_angle', avg_angle),
                'bottom_right_angle': img_data.get('bottom_right_angle', avg_angle),
                'height': img_data.get('height_mm', 0),
                'width': img_data.get('width_mm', 0)
            })
        
        test_id = save_mvic_to_database(
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            results=results,
            notes=data.get('notes'),
            filenames=data.get('filenames')
        )
        
        logger.info(f"[MVIC-SESSION] Saved test session with ID: {test_id}")
        
        return JSONResponse({
            'success': True,
            'test_id': test_id,
            'message': 'MVIC test session saved successfully'
        })
        
    except ValueError as e:
        logger.error(f"[MVIC-SESSION] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[MVIC-SESSION] Error saving test: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mvic-test-sessions")
async def get_mvic_test_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all MVIC test sessions with optional date filtering"""
    logger.info(f"[MVIC-SESSIONS] Getting tests (limit={limit}, start_date={start_date}, end_date={end_date})")
    try:
        from database import SessionLocal, MVICTest, MVICResult
        db_session = SessionLocal()
        
        query = db_session.query(MVICTest).order_by(MVICTest.test_date.desc())
        
        if start_date:
            query = query.filter(MVICTest.test_date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(MVICTest.test_date <= datetime.fromisoformat(end_date))
        
        tests = query.offset(offset).limit(limit).all()
        
        result_tests = []
        for test in tests:
            test_dict = {
                'id': test.id,
                'test_date': test.test_date.isoformat(),
                'operator': test.operator,
                'overall_result': test.overall_result,
                'notes': test.notes,
                'filenames': test.filenames
            }
            result_tests.append(test_dict)
        
        db_session.close()
        logger.info(f"[MVIC-SESSIONS] Retrieved {len(result_tests)} tests")
        return JSONResponse({'tests': result_tests, 'count': len(result_tests)})
    except Exception as e:
        logger.error(f"[MVIC-SESSIONS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mvic-test-sessions/{test_id}")
async def get_mvic_test_session(test_id: int):
    """Get a specific MVIC test session by ID"""
    logger.info(f"[MVIC-SESSION] Getting test ID: {test_id}")
    try:
        from database import SessionLocal, MVICTest, MVICResult
        db_session = SessionLocal()
        
        test = db_session.query(MVICTest).filter(MVICTest.id == test_id).first()
        
        if not test:
            db_session.close()
            raise HTTPException(status_code=404, detail="Test session not found")
        
        results = db_session.query(MVICResult).filter(MVICResult.test_id == test_id).all()
        
        test_dict = {
            'id': test.id,
            'test_date': test.test_date.isoformat(),
            'operator': test.operator,
            'overall_result': test.overall_result,
            'notes': test.notes,
            'filenames': test.filenames,
            'results': [{
                'image_number': r.image_number,
                'filename': r.filename,
                'top_left_angle': r.top_left_angle,
                'top_right_angle': r.top_right_angle,
                'bottom_left_angle': r.bottom_left_angle,
                'bottom_right_angle': r.bottom_right_angle,
                'height': r.height,
                'width': r.width
            } for r in results]
        }
        
        db_session.close()
        logger.info(f"[MVIC-SESSION] Retrieved test session")
        return JSONResponse(test_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MVIC-SESSION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mvic-test-sessions/{test_id}")
async def delete_mvic_test_session(test_id: int):
    """Delete a specific MVIC test session"""
    logger.info(f"[MVIC-SESSION] Deleting test ID: {test_id}")
    try:
        from database import SessionLocal, MVICTest, MVICResult
        db_session = SessionLocal()
        
        test = db_session.query(MVICTest).filter(MVICTest.id == test_id).first()
        
        if not test:
            db_session.close()
            raise HTTPException(status_code=404, detail="Test session not found")
        
        db_session.query(MVICResult).filter(MVICResult.test_id == test_id).delete()
        db_session.delete(test)
        db_session.commit()
        db_session.close()
        
        logger.info(f"[MVIC-SESSION] Successfully deleted test {test_id}")
        return JSONResponse({'message': 'MVIC test session deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MVIC-SESSION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mvic-trend/{parameter}")
async def get_mvic_trend(parameter: str, limit: int = 50):
    """
    Get trend data for a specific MVIC parameter
    Parameters: width, height, avg_angle, angle_std_dev
    """
    logger.info(f"[MVIC-TREND] Getting trend for parameter: {parameter}")
    try:
        trend_data = db.get_mvic_trend_data(parameter, limit)
        logger.info(f"[MVIC-TREND] Retrieved {len(trend_data)} data points")
        return JSONResponse({'parameter': parameter, 'data': trend_data, 'count': len(trend_data)})
    except Exception as e:
        logger.error(f"[MVIC-TREND] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
