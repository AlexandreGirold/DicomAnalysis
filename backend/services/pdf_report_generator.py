"""
PDF Report Generator for Trend Analysis
Generates professional PDF reports with graphs and statistics for quality control tests

For the Leaf Position analysis (not the others)
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from io import BytesIO

logger = logging.getLogger(__name__)


def generate_leaf_position_pdf(data: Dict[str, Any]) -> bytes:
    """
    Generate a comprehensive PDF report for Leaf Position trend analysis using ReportLab
    
    Args:
        data: Dictionary containing:
            - tests: List of test metadata
            - blade_trends: Dict of blade measurements over time
            - summary: Overall statistics
    
    Returns:
        bytes: PDF file content
    """
    logger.info("[PDF-GENERATOR] Starting PDF generation for Leaf Position trend report")
    
    # Create PDF in memory
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#007bff'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    try:
        # Title Page
        elements.append(Paragraph("Rapport d'Analyse de Tendances", title_style))
        elements.append(Paragraph("Position des Lames", styles['Heading2']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Date range
        date_range = data['summary']['date_range']
        date_text = f"<b>Période:</b> {date_range['start']} au {date_range['end']}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary statistics table
        elements.append(Paragraph("Résumé de l'Analyse", heading_style))
        logger.info("[PDF-GENERATOR] Adding summary table")
        elements = add_summary_table(elements, data, styles)
        elements.append(Spacer(1, 0.3*inch))
        
        # Test list table
        elements.append(Paragraph("Liste des Tests Analysés", heading_style))
        logger.info("[PDF-GENERATOR] Adding test list table")
        elements = add_test_list_table(elements, data)
        elements.append(PageBreak())
        
        # Blade trend graphs
        elements.append(Paragraph("Graphiques d'Évolution des Lames", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        logger.info("[PDF-GENERATOR] Adding blade trend graphs")
        elements = add_blade_trend_graphs(elements, data)
        
        # Statistical analysis table
        elements.append(PageBreak())
        elements.append(Paragraph("Analyse Statistique par Lame", heading_style))
        logger.info("[PDF-GENERATOR] Adding statistics table")
        elements = add_statistics_table(elements, data)
        
        # Build PDF
        logger.info(f"[PDF-GENERATOR] Building PDF with {len(elements)} elements")
        doc.build(elements)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"[PDF-GENERATOR] Generated PDF with {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"[PDF-GENERATOR] Error generating PDF: {e}", exc_info=True)
        buffer.close()
        raise


def add_summary_table(elements, data: Dict[str, Any], styles):
    """Add summary statistics table"""
    tests = data['tests']
    blade_trends = data['blade_trends']
    
    total_tests = len(tests)
    passed_tests = sum(1 for t in tests if t['overall_result'] == 'PASS')
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    total_blades = len(blade_trends)
    total_measurements = sum(len(measurements) for measurements in blade_trends.values())
    avg_measurements = (total_measurements / total_blades) if total_blades > 0 else 0
    
    # Create summary table
    summary_data = [
        ['Métrique', 'Valeur'],
        ['Nombre total de tests', str(total_tests)],
        ['Tests réussis', str(passed_tests)],
        ['Tests échoués', str(failed_tests)],
        ['Taux de réussite', f'{pass_rate:.1f}%'],
        ['', ''],
        ['Nombre de lames analysées', str(total_blades)],
        ['Mesures totales', str(total_measurements)],
        ['Mesures moyennes par lame', f'{avg_measurements:.1f}'],
    ]
    
    table = Table(summary_data, colWidths=[4*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    return elements


def add_test_list_table(elements, data: Dict[str, Any]):
    """Add chronological test list table"""
    tests = data['tests']
    
    # Sort tests by date
    sorted_tests = sorted(tests, key=lambda x: x['test_date'])
    
    # Create table data
    table_data = [['ID', 'Date', 'Opérateur', 'Résultat', 'Commentaires']]
    
    for test in sorted_tests:
        test_date = datetime.fromisoformat(test['test_date']).strftime('%Y-%m-%d')
        operator = test['operator'] or 'N/A'
        result = test['overall_result']
        notes = (test['notes'][:30] + '...') if test['notes'] and len(test['notes']) > 30 else (test['notes'] or '-')
        
        table_data.append([
            f"#{test['test_id']}",
            test_date,
            operator,
            result,
            notes
        ])
    
    # Create table
    table = Table(table_data, colWidths=[0.6*inch, 1.2*inch, 1.5*inch, 1.2*inch, 2.5*inch])
    
    # Style table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ])
    
    # Color-code results
    for i, test in enumerate(sorted_tests, start=1):
        if test['overall_result'] == 'PASS':
            style.add('BACKGROUND', (3, i), (3, i), colors.HexColor('#d4edda'))
            style.add('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#155724'))
        elif test['overall_result'] == 'FAIL':
            style.add('BACKGROUND', (3, i), (3, i), colors.HexColor('#f8d7da'))
            style.add('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#721c24'))
    
    table.setStyle(style)
    elements.append(table)
    
    return elements


def add_blade_trend_graphs(elements, data: Dict[str, Any]):
    """Add trend graphs for blades (grouped, 6 per page)"""
    blade_trends = data['blade_trends']
    blade_pairs = sorted(blade_trends.keys())
    
    logger.info(f"[PDF-GRAPHS] Generating graphs for {len(blade_pairs)} blade pairs")
    
    if not blade_pairs:
        elements.append(Paragraph("Aucune donnée de lame disponible", getSampleStyleSheet()['Normal']))
        return elements
    
    graphs_added = 0
    
    for i in range(0, len(blade_pairs), 6):
        blade_group = blade_pairs[i:i+6]
        
        # Create matplotlib figure
        fig, axes = plt.subplots(3, 2, figsize=(7.5, 10))
        axes = axes.flatten()
        
        for idx, blade_pair in enumerate(blade_group):
            if idx >= 6:
                break
            
            ax = axes[idx]
            measurements = blade_trends[blade_pair]
            
            # Extract data
            dates = []
            lengths = []
            field_sizes = []
            statuses = []
            
            for m in measurements:
                if m['test_date'] and m['length_mm'] is not None:
                    dates.append(datetime.fromisoformat(m['test_date']))
                    lengths.append(m['length_mm'])
                    field_sizes.append(m['field_size_mm'] or 0)
                    statuses.append(m['is_valid'])
            
            logger.info(f"[PDF-GRAPHS] Blade {blade_pair}: {len(dates)} data points")
            
            if dates:
                # Plot line
                ax.plot(dates, lengths, marker='o', linestyle='-', linewidth=2, markersize=6, color='#007bff', alpha=0.7)
                
                # Add tolerance bands
                if field_sizes:
                    avg_field_size = np.mean([f for f in field_sizes if f > 0])
                    if avg_field_size > 0:
                        ax.axhspan(avg_field_size - 1, avg_field_size + 1, alpha=0.2, color='orange', label='Tolérance ±1mm')
                        ax.axhline(y=avg_field_size, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Valeur cible')
                
                # Color markers by status
                for j, (date, length, status) in enumerate(zip(dates, lengths, statuses)):
                    if status == 'OK':
                        color = 'green'
                    elif status == 'OUT_OF_TOLERANCE':
                        color = 'orange'
                    else:
                        color = 'gray'
                    ax.plot(date, length, marker='o', color=color, markersize=8, zorder=5)
                
                ax.set_title(f'Lame {blade_pair}', fontsize=11, fontweight='bold')
                ax.set_xlabel('Date', fontsize=9)
                ax.set_ylabel('Longueur (mm)', fontsize=9)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.tick_params(labelsize=8)
                
                # Format dates
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                
                # Add legend (only on first subplot)
                if idx == 0 and i == 0:
                    ax.legend(fontsize=7, loc='upper left')
            else:
                ax.text(0.5, 0.5, 'Pas de données', ha='center', va='center', fontsize=10, transform=ax.transAxes)
                ax.set_title(f'Lame {blade_pair}', fontsize=11, fontweight='bold')
        
        # Hide unused subplots
        for idx in range(len(blade_group), 6):
            axes[idx].axis('off')
        
        plt.tight_layout()
        
        # Save figure to buffer
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Add image to PDF
        img = Image(img_buffer, width=7*inch, height=9.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        if i + 6 < len(blade_pairs):  # Add page break if more blades to come
            elements.append(PageBreak())
        
        plt.close(fig)
        graphs_added += 1
        logger.info(f"[PDF-GRAPHS] Added graph page {graphs_added}")
    
    logger.info(f"[PDF-GRAPHS] Total graph pages added: {graphs_added}")
    return elements


def add_statistics_table(elements, data: Dict[str, Any]):
    """Add statistical analysis table"""
    blade_trends = data['blade_trends']
    
    # Create table data
    table_data = [['Lame', 'Min (mm)', 'Max (mm)', 'Moyenne (mm)', 'Écart-type', 'OK', 'Hors Tolérance']]
    
    for blade_pair in sorted(blade_trends.keys()):
        measurements = blade_trends[blade_pair]
        
        lengths = [m['length_mm'] for m in measurements if m['length_mm'] is not None]
        ok_count = sum(1 for m in measurements if m['is_valid'] == 'OK')
        out_count = sum(1 for m in measurements if m['is_valid'] == 'OUT_OF_TOLERANCE')
        
        if lengths:
            min_len = min(lengths)
            max_len = max(lengths)
            avg_len = np.mean(lengths)
            std_len = np.std(lengths)
            
            table_data.append([
                str(blade_pair),
                f'{min_len:.2f}',
                f'{max_len:.2f}',
                f'{avg_len:.2f}',
                f'{std_len:.3f}',
                str(ok_count),
                str(out_count)
            ])
    
    # Create table (split if too many rows)
    max_rows_per_table = 40
    
    for chunk_start in range(0, len(table_data) - 1, max_rows_per_table):
        chunk_end = min(chunk_start + max_rows_per_table, len(table_data) - 1) + 1
        
        # Include header in each chunk
        if chunk_start == 0:
            chunk_data = table_data[0:chunk_end]
        else:
            chunk_data = [table_data[0]] + table_data[chunk_start + 1:chunk_end]
        
        table = Table(chunk_data, colWidths=[0.8*inch, 1*inch, 1*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        if chunk_end < len(table_data):
            elements.append(PageBreak())
    
    return elements
