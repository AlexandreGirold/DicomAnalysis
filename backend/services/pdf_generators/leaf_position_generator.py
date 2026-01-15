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
        
        # Matrix table with image averages - ONLY TABLE NEEDED
        elements.append(Paragraph("Tableau Matriciel des Moyennes par Image", heading_style))
        logger.info("[PDF-GENERATOR] Adding image averages matrix table")
        elements = add_test_list_table(elements, data)
        
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
    images_by_test = data.get('images_by_test', {})
    
    total_tests = len(tests)
    passed_tests = sum(1 for t in tests if t['overall_result'] == 'PASS')
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    total_images = sum(len(images) for images in images_by_test.values())
    avg_images_per_test = (total_images / total_tests) if total_tests > 0 else 0
    
    # Create summary table
    summary_data = [
        ['Métrique', 'Valeur'],
        ['Nombre total de tests', str(total_tests)],
        ['Tests réussis', str(passed_tests)],
        ['Tests échoués', str(failed_tests)],
        ['Taux de réussite', f'{pass_rate:.1f}%'],
        ['Nombre d\'images analysées', str(total_images)],
        ['Images moyennes par test', f'{avg_images_per_test:.1f}']
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
    """
    Add matrix table showing 6 identified images with Top/Bottom averages per test date
    Rows: Image 1-6 (identified_image_number)
    Columns: Test dates with Top/Bottom sub-columns
    Values: blade_top_average and blade_bottom_average
    """
    tests = data['tests']
    images_by_test = data.get('images_by_test', {})
    
    # Sort tests by date
    sorted_tests = sorted(tests, key=lambda x: x['test_date'])
    
    if not sorted_tests:
        elements.append(Paragraph("Aucun test disponible", getSampleStyleSheet()['Normal']))
        return elements
    
    logger.info(f"[PDF-TABLE] Processing {len(sorted_tests)} tests")
    logger.info(f"[PDF-TABLE] Images by test: {len(images_by_test)} test entries")
    
    # Build data structure: image_data[test_id][image_num] = {'top': x, 'bottom': y}
    image_data = {}
    
    for test_id, images in images_by_test.items():
        logger.info(f"[PDF-TABLE] Test {test_id} has {len(images)} images")
        image_data[test_id] = {}
        
        for img in images:
            img_num = img.get('image_number') or img.get('identified_image_number')
            top = img.get('top_average')
            bottom = img.get('bottom_average')
            
            logger.info(f"[PDF-TABLE] Test {test_id}, Image {img_num}: top={top}, bottom={bottom}")
            
            if img_num is not None:
                image_data[test_id][img_num] = {
                    'top': top,
                    'bottom': bottom
                }
    
    logger.info(f"[PDF-TABLE] Final image_data: {image_data}")
    
    # Build table header
    # Row 1: Test dates (spanning 2 columns each)
    # Row 2: "Top" and "Bottom" sub-columns
    header_row1 = ['Image']
    header_row2 = ['#']
    
    for test in sorted_tests:
        test_date = datetime.fromisoformat(test['test_date']).strftime('%d/%m')
        header_row1.append(test_date)
        header_row1.append('')  # Will be spanned
        header_row2.append('Top')
        header_row2.append('Bottom')
    
    table_data = [header_row1, header_row2]
    
    # Add rows for each of the 6 identified images
    for img_num in range(1, 7):
        row = [f'Image {img_num}']
        
        for test in sorted_tests:
            test_id = test['test_id']
            
            if test_id in image_data and img_num in image_data[test_id]:
                top_val = image_data[test_id][img_num]['top']
                bottom_val = image_data[test_id][img_num]['bottom']
                row.append(f'{top_val:.2f}' if top_val is not None else '-')
                row.append(f'{bottom_val:.2f}' if bottom_val is not None else '-')
            else:
                row.append('-')
                row.append('-')
        
        table_data.append(row)
    
    # Calculate column widths
    num_tests = len(sorted_tests)
    image_col_width = 0.8 * inch
    value_col_width = 0.65 * inch  # Width for each Top/Bottom value
    
    col_widths = [image_col_width] + [value_col_width] * (num_tests * 2)
    
    # Create table
    table = Table(table_data, colWidths=col_widths)
    
    # Build table style
    style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 8),
        ('TOPPADDING', (0, 0), (-1, 1), 8),
        # Data rows styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 2), (-1, -1), 7),
        ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),  # Bold image numbers
    ])
    
    # Span date cells across Top/Bottom columns in first header row
    for i, test in enumerate(sorted_tests):
        col_start = 1 + (i * 2)
        col_end = col_start + 1
        style.add('SPAN', (col_start, 0), (col_end, 0))
    
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
