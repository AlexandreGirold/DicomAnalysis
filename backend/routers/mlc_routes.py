"""
MLC Routes - Endpoints for MLC Leaf and Jaw tests
Includes test sessions, analysis, trends, and reports
"""
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, Response
from typing import List
from datetime import datetime
import database as db
import database_helpers
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter()


def parse_test_date(date_str):
    """Helper function to parse test date from string or return current datetime"""
    if date_str:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    return datetime.now()


@router.post("/mlc-leaf-jaw-sessions")
async def save_mlc_leaf_jaw_session(data: dict):
    """Save MLC Leaf and Jaw test session"""
    logger.info("[MLC-LEAF-JAW] Saving test session")
    try:
        test_date = parse_test_date(data.get('test_date'))
        if 'operator' not in data or not data['operator']:
            raise ValueError("operator is required")
        
        test_id = database_helpers.save_mlc_leaf_jaw_to_database(
            operator=data['operator'],
            test_date=test_date,
            overall_result=data.get('overall_result', 'PASS'),
            notes=data.get('notes'),
            filenames=data.get('filenames', [])
        )
        
        logger.info(f"[MLC-LEAF-JAW] Saved test with ID: {test_id}")
        return JSONResponse({'success': True, 'test_id': test_id, 'message': 'MLC Leaf Jaw test saved successfully'})
    except ValueError as e:
        logger.error(f"[MLC-LEAF-JAW] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[MLC-LEAF-JAW] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mlc-test-sessions")
async def save_mlc_test_session_legacy(data: dict):
    """DEPRECATED: Use /mlc-leaf-jaw-sessions instead"""
    logger.warning("[MLC-SESSION] DEPRECATED endpoint called, redirecting to mlc-leaf-jaw-sessions")
    return await save_mlc_leaf_jaw_session(data)


@router.get("/mlc-test-sessions")
async def get_mlc_test_sessions(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get all MLC test sessions with optional date filtering"""
    logger.info(f"[MLC-SESSIONS] Getting tests (limit={limit}, start_date={start_date}, end_date={end_date})")
    try:
        tests = db.get_all_mlc_test_sessions(limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        logger.info(f"[MLC-SESSIONS] Retrieved {len(tests)} tests")
        return JSONResponse({'tests': tests, 'count': len(tests)})
    except Exception as e:
        logger.error(f"[MLC-SESSIONS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mlc-test-sessions/{test_id}")
async def get_mlc_test_session(test_id: int):
    """Get a specific MLC test session by ID"""
    logger.info(f"[MLC-SESSION] Getting test ID: {test_id}")
    try:
        test = db.get_mlc_test_session_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test session not found")
        logger.info(f"[MLC-SESSION] Retrieved test session")
        return JSONResponse(test)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MLC-SESSION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mlc-test-sessions/{test_id}")
async def delete_mlc_test_session(test_id: int):
    """Delete a specific MLC test session"""
    logger.info(f"[MLC-SESSION] Deleting test ID: {test_id}")
    try:
        success = db.delete_mlc_test_session(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test session not found")
        logger.info(f"[MLC-SESSION] Successfully deleted test {test_id}")
        return JSONResponse({'message': 'MLC test session deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MLC-SESSION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mlc-trend/{parameter}")
async def get_mlc_trend(parameter: str, limit: int = 50):
    """
    Get trend data for a specific MLC parameter
    Parameters: center_u, center_v, jaw_x1_mm, jaw_x2_mm, 
                blade_top_average, blade_top_std_dev, 
                blade_bottom_average, blade_bottom_std_dev, 
                blade_average_angle
    """
    logger.info(f"[MLC-TREND] Getting trend for parameter: {parameter}")
    try:
        trend_data = db.get_mlc_trend_data(parameter, limit)
        logger.info(f"[MLC-TREND] Retrieved {len(trend_data)} data points")
        return JSONResponse({'parameter': parameter, 'data': trend_data, 'count': len(trend_data)})
    except Exception as e:
        logger.error(f"[MLC-TREND] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mlc-reports/trend")
async def generate_mlc_trend_report(start_date: str = None, end_date: str = None):
    """Generate PDF report for MLC test sessions with trend analysis"""
    logger.info(f"[MLC-REPORT] Generating trend report from {start_date} to {end_date}")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        tests = db.get_all_mlc_test_sessions(limit=1000, start_date=start_date, end_date=end_date)
        
        if not tests:
            raise HTTPException(status_code=404, detail="No MLC test sessions found for the given date range")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24,
                                     textColor=colors.HexColor('#2c3e50'), spaceAfter=30, alignment=TA_CENTER)
        story.append(Paragraph("MLC Leaf and Jaw Test Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        info_style = styles['Normal']
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"<b>Number of Tests:</b> {len(tests)}", info_style))
        if start_date:
            story.append(Paragraph(f"<b>Start Date:</b> {start_date}", info_style))
        if end_date:
            story.append(Paragraph(f"<b>End Date:</b> {end_date}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        table_data = [['Test ID', 'Date', 'Operator', 'Center (U,V)', 'Jaw (X1,X2)', 
                      'Top Blade Avg', 'Bottom Blade Avg', 'Angle', 'Result']]
        
        for test in tests:
            test_date = datetime.fromisoformat(test['test_date']).strftime('%Y-%m-%d')
            center = f"{test['test1_center']['center_u'] or '-'}, {test['test1_center']['center_v'] or '-'}"
            jaw = f"{test['test2_jaw']['jaw_x1_mm'] or '-'}, {test['test2_jaw']['jaw_x2_mm'] or '-'}"
            top_avg = str(test['test3_blade_top']['average'] or '-')
            bottom_avg = str(test['test4_blade_bottom']['average'] or '-')
            angle = str(test['test5_angle']['average_angle'] or '-')
            result = test['overall_result'] or 'N/A'
            
            table_data.append([str(test['id']), test_date, test['operator'][:10], center[:15], jaw[:15],
                             top_avg[:8], bottom_avg[:8], angle[:8], result])
        
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"[MLC-REPORT] Successfully generated report with {len(tests)} tests")
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=mlc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MLC-REPORT] Error generating report: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
