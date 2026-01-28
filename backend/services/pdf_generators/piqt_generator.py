"""
Générateur de Rapport PDF pour le Test PIQT
Génère un rapport PDF professionnel pour le test PIQT (Philips Image Quality Test)
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO

logger = logging.getLogger(__name__)


def generate_piqt_pdf(data: Dict[str, Any]) -> bytes:
    """
    Génère un rapport PDF pour un test PIQT individuel
    
    Args:
        data: Dictionnaire contenant les données du test PIQT
            - test_date: Date du test
            - operator: Opérateur
            - overall_result: Résultat global (PASS/FAIL)
            - snr_value: Valeur SNR
            - uniformity_value: Valeur d'uniformité
            - ghosting_value: Valeur de ghosting
            - results_json: Résultats détaillés au format JSON
            - notes: Notes optionnelles
    
    Returns:
        bytes: Contenu du fichier PDF
    """
    logger.info("[PDF-PIQT] Début de la génération du rapport PDF PIQT")
    
    # Créer le PDF en mémoire
    buffer = BytesIO()
    
    # Créer le document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Éléments du document
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        spaceBefore=8
    )
    
    # Titre
    elements.append(Paragraph("Rapport de Test PIQT", title_style))
    elements.append(Paragraph("Philips Image Quality Test", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Informations générales
    elements.append(Paragraph("Informations Générales", heading_style))
    
    # Formater la date
    test_date_str = data.get('test_date', 'N/A')
    if isinstance(test_date_str, str) and test_date_str != 'N/A':
        try:
            test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
            test_date_str = test_date.strftime('%d/%m/%Y %H:%M')
        except:
            pass
    
    # Déterminer le statut et la couleur
    overall_result = data.get('overall_result', 'UNKNOWN')
    if overall_result == 'PASS':
        result_text = "✓ RÉUSSI"
        result_color = colors.green
    elif overall_result == 'FAIL':
        result_text = "✗ ÉCHOUÉ"
        result_color = colors.red
    else:
        result_text = "? INCONNU"
        result_color = colors.orange
    
    # Tableau des informations générales
    general_info_data = [
        ['Date du test:', test_date_str],
        ['Opérateur:', data.get('operator', 'N/A')],
        ['Résultat global:', result_text],
    ]
    
    general_info_table = Table(general_info_data, colWidths=[5*cm, 10*cm])
    general_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (1, 2), (1, 2), result_color),
        ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(general_info_table)
    elements.append(Spacer(1, 0.75*cm))
    
    # Résultats détaillés si disponibles
    results_json = data.get('results_json')
    if results_json:
        import json
        try:
            detailed_results = json.loads(results_json) if isinstance(results_json, str) else results_json
            
            elements.append(Paragraph("Résultats Détaillés", heading_style))
            
            # FFU1 NEMA
            if any('ffu1_nema' in str(k).lower() for k in detailed_results if isinstance(detailed_results, dict)):
                elements.append(Paragraph("FFU1 NEMA", subheading_style))
                ffu1_data = [['Paramètre', 'Valeur']]
                
                for key, value in detailed_results.items():
                    if 'ffu1_nema' in str(key).lower():
                        param_name = key.replace('ffu1_nema_', '').replace('_', ' ').title()
                        ffu1_data.append([param_name, str(value) if value is not None else 'N/A'])
                
                if len(ffu1_data) > 1:
                    ffu1_table = create_detail_table(ffu1_data)
                    elements.append(ffu1_table)
                    elements.append(Spacer(1, 0.5*cm))
            
            # FFU2 NEMA
            if any('ffu2_nema' in str(k).lower() for k in detailed_results if isinstance(detailed_results, dict)):
                elements.append(Paragraph("FFU2 NEMA", subheading_style))
                ffu2_data = [['Paramètre', 'Valeur']]
                
                for key, value in detailed_results.items():
                    if 'ffu2_nema' in str(key).lower():
                        param_name = key.replace('ffu2_nema_', '').replace('_', ' ').title()
                        ffu2_data.append([param_name, str(value) if value is not None else 'N/A'])
                
                if len(ffu2_data) > 1:
                    ffu2_table = create_detail_table(ffu2_data)
                    elements.append(ffu2_table)
                    elements.append(Spacer(1, 0.5*cm))
            
            # Spatial Linearity
            if any('spatial_linearity' in str(k).lower() for k in detailed_results if isinstance(detailed_results, dict)):
                elements.append(Paragraph("Linéarité Spatiale", subheading_style))
                spatial_data = [['Paramètre', 'Valeur']]
                
                for key, value in detailed_results.items():
                    if 'spatial_linearity' in str(key).lower():
                        param_name = key.replace('spatial_linearity_nema_', '').replace('_', ' ').title()
                        spatial_data.append([param_name, str(value) if value is not None else 'N/A'])
                
                if len(spatial_data) > 1:
                    spatial_table = create_detail_table(spatial_data)
                    elements.append(spatial_table)
                    elements.append(Spacer(1, 0.5*cm))
            
            # Slice Profile
            if any('slice_profile' in str(k).lower() for k in detailed_results if isinstance(detailed_results, dict)):
                elements.append(Paragraph("Profil de Coupe", subheading_style))
                slice_data = [['Paramètre', 'Valeur']]
                
                for key, value in detailed_results.items():
                    if 'slice_profile' in str(key).lower():
                        param_name = key.replace('slice_profile_nema_', '').replace('_', ' ').title()
                        slice_data.append([param_name, str(value) if value is not None else 'N/A'])
                
                if len(slice_data) > 1:
                    slice_table = create_detail_table(slice_data)
                    elements.append(slice_table)
                    elements.append(Spacer(1, 0.5*cm))
            
            # Spatial Resolution
            if any('spatial_resolution' in str(k).lower() for k in detailed_results if isinstance(detailed_results, dict)):
                elements.append(Paragraph("Résolution Spatiale", subheading_style))
                resolution_data = [['Paramètre', 'Valeur']]
                
                for key, value in detailed_results.items():
                    if 'spatial_resolution' in str(key).lower():
                        param_name = key.replace('spatial_resolution_nema_', '').replace('_', ' ').title()
                        resolution_data.append([param_name, str(value) if value is not None else 'N/A'])
                
                if len(resolution_data) > 1:
                    resolution_table = create_detail_table(resolution_data)
                    elements.append(resolution_table)
                    elements.append(Spacer(1, 0.5*cm))
                    
        except Exception as e:
            logger.error(f"[PDF-PIQT] Erreur lors de l'analyse des résultats détaillés: {e}")
    
    # Notes si disponibles
    notes = data.get('notes')
    if notes:
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("Notes", heading_style))
        elements.append(Paragraph(notes, styles['Normal']))
    
    # Construire le PDF
    doc.build(elements)
    
    # Récupérer les bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    logger.info(f"[PDF-PIQT] PDF généré avec {len(pdf_bytes)} bytes")
    return pdf_bytes


def create_detail_table(data: List[List[str]]) -> Table:
    """Crée un tableau formaté pour les résultats détaillés"""
    table = Table(data, colWidths=[10*cm, 5*cm])
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Corps
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        # Alternance de couleurs
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    return table


def generate_piqt_trend_pdf(data: Dict[str, Any]) -> bytes:
    """
    Génère un rapport PDF de tendances pour les tests PIQT
    
    Args:
        data: Dictionnaire contenant:
            - tests: Liste des tests PIQT
            - date_range: Plage de dates
            - summary: Statistiques résumées
    
    Returns:
        bytes: Contenu du fichier PDF
    """
    logger.info("[PDF-PIQT-TREND] Début de la génération du rapport de tendances PIQT")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Style de titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Titre
    elements.append(Paragraph("Rapport de Tendances PIQT", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Période
    date_range = data.get('date_range', {})
    date_text = f"<b>Période:</b> {date_range.get('start', 'N/A')} au {date_range.get('end', 'N/A')}"
    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Résumé
    summary = data.get('summary', {})
    elements.append(Paragraph("Résumé", heading_style))
    
    summary_data = [
        ['Métrique', 'Valeur'],
        ['Nombre total de tests', str(summary.get('total_tests', 0))],
        ['Tests réussis', str(summary.get('passed_tests', 0))],
        ['Tests échoués', str(summary.get('failed_tests', 0))],
        ['Taux de réussite', f"{summary.get('success_rate', 0):.1f}%"],
    ]
    
    summary_table = Table(summary_data, colWidths=[10*cm, 5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    # Liste des tests
    tests = data.get('tests', [])
    if tests:
        elements.append(Paragraph("Liste des Tests", heading_style))
        
        tests_data = [['Date', 'Opérateur', 'Résultat']]
        
        for test in tests:
            # Formater la date
            test_date_str = test.get('test_date', 'N/A')
            if isinstance(test_date_str, str) and test_date_str != 'N/A':
                try:
                    test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
                    test_date_str = test_date.strftime('%d/%m/%Y')
                except:
                    pass
            
            result = test.get('overall_result', 'N/A')
            
            tests_data.append([
                test_date_str,
                test.get('operator', 'N/A'),
                result
            ])
        
        tests_table = Table(tests_data, colWidths=[5*cm, 6*cm, 4*cm])
        tests_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(tests_table)
    
    # Construire le PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    logger.info(f"[PDF-PIQT-TREND] PDF de tendances généré avec {len(pdf_bytes)} bytes")
    return pdf_bytes
