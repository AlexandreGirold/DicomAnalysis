"""
Générateur de Rapport PDF pour le Test Niveau Helium
Génère un rapport PDF professionnel pour le test Niveau d'Hélium
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


def generate_niveau_helium_pdf(data: Dict[str, Any]) -> bytes:
    """
    Génère un rapport PDF pour un test Niveau Helium individuel
    
    Args:
        data: Dictionnaire contenant les données du test
            - test_date: Date du test
            - operator: Opérateur
            - overall_result: Résultat global (PASS/FAIL)
            - helium_level: Niveau d'hélium en %
            - notes: Notes optionnelles
    
    Returns:
        bytes: Contenu du fichier PDF
    """
    logger.info("[PDF-HELIUM] Début de la génération du rapport PDF Niveau Helium")
    
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
    elements.append(Paragraph("Rapport de Test Niveau d'Hélium", title_style))
    elements.append(Paragraph("ANSM - Contrôle Hebdomadaire", styles['Normal']))
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
    
    # Résultats détaillés
    elements.append(Paragraph("Résultats Détaillés", heading_style))
    
    # Récupérer la valeur mesurée
    helium_level = data.get('helium_level', 'N/A')
    helium_level_str = f"{helium_level:.1f}" if isinstance(helium_level, (int, float)) else str(helium_level)
    
    # Déterminer la couleur en fonction du niveau
    if isinstance(helium_level, (int, float)):
        if helium_level > 65:
            level_color = colors.green
            status_text = "✓ CONFORME"
            status_color = colors.green
        else:
            level_color = colors.red
            status_text = "✗ NON CONFORME"
            status_color = colors.red
    else:
        level_color = colors.black
        status_text = "? INCONNU"
        status_color = colors.orange
    
    # Créer le tableau de résultats détaillés
    results_data = [['Paramètre', 'Valeur Mesurée', 'Limite d\'Acceptation', 'Statut']]
    results_data.append(['Niveau d\'Hélium', f"{helium_level_str} %", '> 65 %', status_text])
    
    results_table = Table(results_data, colWidths=[5*cm, 4*cm, 4*cm, 4*cm])
    results_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Corps
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        # Coloration de la valeur mesurée
        ('TEXTCOLOR', (1, 1), (1, 1), level_color),
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 1), (1, 1), 13),
        # Coloration du statut
        ('TEXTCOLOR', (3, 1), (3, 1), status_color),
        ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        # Alternance de couleurs
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(results_table)
    elements.append(Spacer(1, 0.75*cm))
    
    # Critères d'acceptation
    elements.append(Paragraph("Critères d'Acceptation", heading_style))
    
    criteria_data = [
        ['Critère', 'Description'],
        ['Seuil Minimal', 'Le niveau d\'hélium doit être strictement supérieur à 65%'],
        ['Action si Échec', 'Contacter immédiatement le service technique pour planifier un remplissage du réservoir d\'hélium'],
        ['Fréquence', 'Contrôle hebdomadaire selon recommandations ANSM'],
        ['Impact', 'Un niveau d\'hélium insuffisant peut affecter la qualité des images IRM'],
    ]
    
    criteria_table = Table(criteria_data, colWidths=[4*cm, 11*cm])
    criteria_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Corps
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        # Alternance de couleurs
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(criteria_table)
    elements.append(Spacer(1, 0.5*cm))
    
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
    
    logger.info(f"[PDF-HELIUM] PDF généré avec {len(pdf_bytes)} bytes")
    return pdf_bytes


def generate_niveau_helium_trend_pdf(data: Dict[str, Any]) -> bytes:
    """
    Génère un rapport PDF de tendances pour les tests Niveau Helium
    
    Args:
        data: Dictionnaire contenant:
            - tests: Liste des tests
            - date_range: Plage de dates
            - summary: Statistiques résumées
    
    Returns:
        bytes: Contenu du fichier PDF
    """
    logger.info("[PDF-HELIUM-TREND] Début de la génération du rapport de tendances")
    
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
    elements.append(Paragraph("Rapport de Tendances - Niveau d'Hélium", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Plage de dates
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
    elements.append(Paragraph("Liste des Tests", heading_style))
    
    tests = data.get('tests', [])
    if tests:
        # Tableau des tests
        test_data = [['Date', 'Opérateur', 'Niveau (%)', 'Résultat']]
        
        for test in tests:
            test_date_str = test.get('test_date', 'N/A')
            if isinstance(test_date_str, str) and test_date_str != 'N/A':
                try:
                    test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
                    test_date_str = test_date.strftime('%d/%m/%Y')
                except:
                    pass
            
            helium_level = test.get('helium_level', 'N/A')
            level_str = f"{helium_level:.1f}" if isinstance(helium_level, (int, float)) else str(helium_level)
            
            test_data.append([
                test_date_str,
                test.get('operator', 'N/A'),
                level_str,
                test.get('overall_result', 'N/A')
            ])
        
        test_table = Table(test_data, colWidths=[4*cm, 5*cm, 3*cm, 3*cm])
        test_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Corps
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            # Alternance de couleurs
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(test_table)
    else:
        elements.append(Paragraph("Aucun test disponible.", styles['Normal']))
    
    # Construire le PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    logger.info(f"[PDF-HELIUM-TREND] PDF généré avec {len(pdf_bytes)} bytes")
    return pdf_bytes
