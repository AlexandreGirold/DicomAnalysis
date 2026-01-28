"""
Trend Reports Router
Handles generation of trend analysis reports for quality control tests
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, Response
from datetime import datetime, date
from typing import Optional, List
import logging
from sqlalchemy import and_
import json

import database as db
from database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/leaf-position-debug")
async def debug_leaf_position_data():
    """Debug endpoint to check what data exists in the database"""
    session = SessionLocal()
    try:
        # Get all tests
        all_tests = session.query(db.LeafPositionTest).all()
        
        # Get all results
        all_results = session.query(db.LeafPositionResult).all()
        
        # Organize by test
        debug_info = {
            'total_tests': len(all_tests),
            'total_blade_results': len(all_results),
            'tests': []
        }
        
        for test in all_tests:
            test_results = session.query(db.LeafPositionResult).filter(
                db.LeafPositionResult.test_id == test.id
            ).all()
            
            debug_info['tests'].append({
                'test_id': test.id,
                'test_date': test.test_date.isoformat() if test.test_date else None,
                'operator': test.operator,
                'overall_result': test.overall_result,
                'blade_results_count': len(test_results),
                'blade_pairs': list(set([r.blade_pair for r in test_results])) if test_results else []
            })
        
        return JSONResponse(debug_info)
    finally:
        session.close()


@router.get("/leaf-position-trend")
async def get_leaf_position_trend(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    format: str = Query("json", description="Response format: 'json' or 'pdf'")
):
    """
    Get trend analysis data for Leaf Position tests over a date range
    
    Returns:
    - format=json: JSON with test metadata and blade measurements
    - format=pdf: PDF report with graphs and analysis
    """
    try:
        # Parse dates and convert to datetime with time components
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        # Set end date to end of day (23:59:59)
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        if start_datetime > end_datetime:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        logger.info(f"[TREND-REPORT] Querying Leaf Position tests from {start_date} to {end_date}")
        logger.info(f"[TREND-REPORT] DateTime range: {start_datetime} to {end_datetime}")
        
        # Query database
        session = SessionLocal()
        try:
            # Get all tests in date range - compare datetime fields properly
            tests = session.query(db.LeafPositionTest).filter(
                and_(
                    db.LeafPositionTest.test_date >= start_datetime,
                    db.LeafPositionTest.test_date <= end_datetime
                )
            ).order_by(db.LeafPositionTest.test_date.asc()).all()
            
            logger.info(f"[TREND-REPORT] Found {len(tests)} tests")
            
            if not tests:
                logger.warning(f"[TREND-REPORT] No tests found for date range {start_date} to {end_date}")
                return JSONResponse({
                    'tests': [],
                    'blade_trends': {},
                    'summary': {
                        'total_tests': 0,
                        'date_range': {'start': start_date, 'end': end_date}
                    }
                })
            
            logger.info(f"[TREND-REPORT] Found {len(tests)} tests")
            
            # Build test metadata list
            test_metadata = []
            for test in tests:
                test_metadata.append({
                    'test_id': test.id,
                    'test_date': test.test_date.isoformat() if test.test_date else None,
                    'operator': test.operator,
                    'overall_result': test.overall_result,
                    'notes': test.notes
                })
            
            # Query all blade results for these tests
            test_ids = [t.id for t in tests]
            logger.info(f"[TREND-REPORT] Querying blade results for test IDs: {test_ids}")
            
            blade_results = session.query(db.LeafPositionResult).filter(
                db.LeafPositionResult.test_id.in_(test_ids)
            ).all()
            
            logger.info(f"[TREND-REPORT] Found {len(blade_results)} blade measurements")
            
            # Query image averages for these tests
            logger.info(f"[TREND-REPORT] Querying image averages for test IDs: {test_ids}")
            image_records = session.query(db.LeafPositionImage).filter(
                db.LeafPositionImage.test_id.in_(test_ids)
            ).all()
            
            logger.info(f"[TREND-REPORT] Found {len(image_records)} image records")
            
            # Organize images by test
            images_by_test = {}
            for img in image_records:
                if img.test_id not in images_by_test:
                    images_by_test[img.test_id] = []
                
                images_by_test[img.test_id].append({
                    'image_number': img.image_number,
                    'identified_image_number': img.identified_image_number,
                    'filename': img.filename,
                    'top_average': img.top_average,
                    'bottom_average': img.bottom_average
                })
                
                top_str = f"{img.top_average:.2f}" if img.top_average is not None else "None"
                bottom_str = f"{img.bottom_average:.2f}" if img.bottom_average is not None else "None"
                logger.info(f"[TREND-REPORT] Test {img.test_id}, Image {img.image_number} → Position {img.identified_image_number}: "
                           f"top={top_str}mm, bottom={bottom_str}mm")
            
            logger.info(f"[TREND-REPORT] Organized images: {len(images_by_test)} tests with image data")
            
            if not blade_results:
                logger.warning(f"[TREND-REPORT] No blade results found for {len(tests)} tests!")
                # Check if results exist at all
                total_results = session.query(db.LeafPositionResult).count()
                logger.warning(f"[TREND-REPORT] Total results in database: {total_results}")
            
            # Organize blade data by blade_pair
            blade_trends = {}
            for result in blade_results:
                blade_pair = result.blade_pair
                
                if blade_pair not in blade_trends:
                    blade_trends[blade_pair] = []
                
                # Find the test date for this result
                test = next((t for t in tests if t.id == result.test_id), None)
                test_date = test.test_date.isoformat() if test and test.test_date else None
                
                blade_trends[blade_pair].append({
                    'test_id': result.test_id,
                    'test_date': test_date,
                    'image_number': result.image_number,
                    'v_sup_px': result.v_sup_px,
                    'v_inf_px': result.v_inf_px,
                    'distance_sup_mm': result.distance_sup_mm,
                    'distance_inf_mm': result.distance_inf_mm,
                    'length_mm': result.length_mm,
                    'field_size_mm': result.field_size_mm,
                    'is_valid': result.is_valid
                })
            
            logger.info(f"[TREND-REPORT] Organized data into {len(blade_trends)} blade pairs")
            
            # Sort each blade's measurements by test date
            for blade_pair in blade_trends:
                blade_trends[blade_pair].sort(key=lambda x: x['test_date'] or '')
            
            response_data = {
                'tests': test_metadata,
                'blade_trends': blade_trends,
                'images_by_test': images_by_test,
                'summary': {
                    'total_tests': len(tests),
                    'total_blades': len(blade_trends),
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    }
                }
            }
            
            if format == 'pdf':
                # Generate PDF report
                from services.pdf_generators.leaf_position_generator import generate_leaf_position_pdf
                pdf_bytes = generate_leaf_position_pdf(response_data)
                
                return Response(
                    content=pdf_bytes,
                    media_type='application/pdf',
                    headers={
                        'Content-Disposition': f'attachment; filename="leaf_position_trend_{start_date}_{end_date}.pdf"'
                    }
                )
            else:
                # Return JSON
                return JSONResponse(response_data)
            
        finally:
            session.close()
            
    except ValueError as e:
        logger.error(f"[TREND-REPORT] Date parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"[TREND-REPORT] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mlc-blade-compliance")
async def generate_mlc_blade_compliance_report(
    test_ids: List[int] = Query(..., description="List of test IDs to include in report"),
    blade_size: str = Query("all", description="Blade size filter: 20mm, 30mm, 40mm, or all")
):
    """
    Generate comprehensive MLC blade compliance report with:
    - Cover page
    - Executive summary with statistics
    - Trend graphs by blade size
    - Detailed tables with all measurements
    - Methodology annex
    
    Example: POST /reports/mlc-blade-compliance?test_ids=1&test_ids=2&test_ids=3&blade_size=20mm
    """
    try:
        logger.info(f"[MLC-BLADE-REPORT] Generating report for {len(test_ids)} tests, size filter: {blade_size}")
        
        # Validate blade size parameter
        valid_sizes = ["all", "20mm", "30mm", "40mm"]
        if blade_size not in valid_sizes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid blade_size. Must be one of: {', '.join(valid_sizes)}"
            )
        
        # Import the report generator
        from services.mlc_blade_report_generator import generate_blade_report
        
        # Generate PDF
        pdf_bytes = generate_blade_report(test_ids, blade_size)
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mlc_blade_compliance_{blade_size}_{timestamp}.pdf"
        
        logger.info(f"[MLC-BLADE-REPORT] Successfully generated report: {filename}")
        
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except ImportError as e:
        logger.error(f"[MLC-BLADE-REPORT] Import error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Report generator not available. Please check server configuration."
        )
    except ValueError as e:
        logger.error(f"[MLC-BLADE-REPORT] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[MLC-BLADE-REPORT] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/piqt-test/{test_id}/pdf")
async def get_piqt_test_pdf(test_id: int):
    """
    Génère un rapport PDF pour un test PIQT individuel
    
    Args:
        test_id: ID du test PIQT
        
    Returns:
        PDF avec les résultats du test PIQT
    """
    try:
        logger.info(f"[PIQT-PDF] Génération du rapport PDF pour le test PIQT ID: {test_id}")
        
        # Récupérer les données du test
        session = SessionLocal()
        try:
            test = session.query(db.PIQTTest).filter(db.PIQTTest.id == test_id).first()
            
            if not test:
                raise HTTPException(status_code=404, detail=f"Test PIQT avec l'ID {test_id} introuvable")
            
            # Préparer les données pour le générateur PDF
            test_data = {
                'test_date': test.test_date.isoformat() if test.test_date else None,
                'operator': test.operator,
                'overall_result': test.overall_result,
                'snr_value': test.snr_value,
                'uniformity_value': test.uniformity_value,
                'ghosting_value': test.ghosting_value,
                'results_json': test.results_json,
                'notes': test.notes
            }
            
            # Générer le PDF
            from services.pdf_generators.piqt_generator import generate_piqt_pdf
            pdf_bytes = generate_piqt_pdf(test_data)
            
            # Créer le nom de fichier
            test_date_str = test.test_date.strftime('%Y%m%d') if test.test_date else 'unknown'
            filename = f"piqt_test_{test_date_str}_{test_id}.pdf"
            
            logger.info(f"[PIQT-PDF] Rapport PDF généré avec succès: {filename}")
            
            return Response(
                content=pdf_bytes,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
            
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PIQT-PDF] Erreur: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Échec de la génération du rapport: {str(e)}")


@router.get("/piqt-trend")
async def get_piqt_trend(
    start_date: str = Query(..., description="Date de début au format YYYY-MM-DD"),
    end_date: str = Query(..., description="Date de fin au format YYYY-MM-DD"),
    format: str = Query("json", description="Format de réponse: 'json' ou 'pdf'")
):
    """
    Obtenir l'analyse de tendances pour les tests PIQT sur une plage de dates
    
    Returns:
    - format=json: JSON avec les métadonnées des tests
    - format=pdf: Rapport PDF avec graphiques et analyse
    """
    try:
        # Analyser les dates
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        if start_datetime > end_datetime:
            raise HTTPException(status_code=400, detail="La date de début doit être antérieure à la date de fin")
        
        logger.info(f"[PIQT-TREND] Requête des tests PIQT du {start_date} au {end_date}")
        
        # Requête en base de données
        session = SessionLocal()
        try:
            tests = session.query(db.PIQTTest).filter(
                and_(
                    db.PIQTTest.test_date >= start_datetime,
                    db.PIQTTest.test_date <= end_datetime
                )
            ).order_by(db.PIQTTest.test_date.asc()).all()
            
            logger.info(f"[PIQT-TREND] Trouvé {len(tests)} tests")
            
            if not tests:
                logger.warning(f"[PIQT-TREND] Aucun test trouvé pour la plage de dates {start_date} à {end_date}")
                return JSONResponse({
                    'tests': [],
                    'date_range': {'start': start_date, 'end': end_date},
                    'summary': {
                        'total_tests': 0,
                        'passed_tests': 0,
                        'failed_tests': 0,
                        'success_rate': 0
                    }
                })
            
            # Préparer les données
            tests_data = []
            passed_count = 0
            failed_count = 0
            
            for test in tests:
                test_dict = {
                    'id': test.id,
                    'test_date': test.test_date.isoformat() if test.test_date else None,
                    'operator': test.operator,
                    'overall_result': test.overall_result,
                    'snr_value': test.snr_value,
                    'uniformity_value': test.uniformity_value,
                    'ghosting_value': test.ghosting_value,
                    'notes': test.notes
                }
                tests_data.append(test_dict)
                
                if test.overall_result == 'PASS':
                    passed_count += 1
                elif test.overall_result == 'FAIL':
                    failed_count += 1
            
            # Calculer les statistiques
            total_tests = len(tests)
            success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
            
            response_data = {
                'tests': tests_data,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_count,
                    'failed_tests': failed_count,
                    'success_rate': success_rate
                }
            }
            
            if format == 'pdf':
                # Générer le rapport PDF
                from services.pdf_generators.piqt_generator import generate_piqt_trend_pdf
                pdf_bytes = generate_piqt_trend_pdf(response_data)
                
                return Response(
                    content=pdf_bytes,
                    media_type='application/pdf',
                    headers={
                        'Content-Disposition': f'attachment; filename="piqt_trend_{start_date}_{end_date}.pdf"'
                    }
                )
            else:
                # Retourner JSON
                return JSONResponse(response_data)
                
        finally:
            session.close()
            
    except ValueError as e:
        logger.error(f"[PIQT-TREND] Erreur d'analyse de date: {e}")
        raise HTTPException(status_code=400, detail=f"Format de date invalide: {str(e)}")
    except Exception as e:
        logger.error(f"[PIQT-TREND] Erreur: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

