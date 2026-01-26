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
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, PageTemplate, Frame, BaseDocTemplate
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
    
    # Create story elements
    portrait_elements = []
    landscape_elements = []
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
        # Portrait Section: Title and Summary
        portrait_elements.append(Paragraph("Rapport d'Analyse de Tendances", title_style))
        portrait_elements.append(Paragraph("Position des Lames", styles['Heading2']))
        portrait_elements.append(Spacer(1, 0.75*cm))
        
        # Date range
        date_range = data['summary']['date_range']
        date_text = f"<b>Période:</b> {date_range['start']} au {date_range['end']}"
        portrait_elements.append(Paragraph(date_text, styles['Normal']))
        portrait_elements.append(Spacer(1, 0.5*cm))
        
        # Summary statistics table
        portrait_elements.append(Paragraph("Résumé de l'Analyse", heading_style))
        logger.info("[PDF-GENERATOR] Adding summary table")
        portrait_elements = add_summary_table(portrait_elements, data, styles)
        portrait_elements.append(Spacer(1, 0.75*cm))
        
        # Build portrait section
        portrait_doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        portrait_doc.build(portrait_elements)
        
        # Now create landscape section for table
        landscape_buffer = BytesIO()
        landscape_doc = SimpleDocTemplate(
            landscape_buffer,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        # Matrix table with image averages - LANDSCAPE
        landscape_elements.append(Paragraph("Tableau Matriciel des Moyennes par Image", heading_style))
        logger.info("[PDF-GENERATOR] Adding image averages matrix table in landscape")
        landscape_elements = add_test_list_table(landscape_elements, data)
        
        # Build landscape section
        landscape_doc.build(landscape_elements)
        
        # Merge PDFs (portrait + landscape)
        from PyPDF2 import PdfMerger, PdfReader
        
        merger = PdfMerger()
        
        # Add portrait pages
        buffer.seek(0)
        merger.append(PdfReader(buffer))
        
        # Add images page showing the 6 positions BEFORE tables
        images_buffer = add_images_page(data)
        if images_buffer:
            merger.append(PdfReader(images_buffer))
        
        # Add landscape page
        landscape_buffer.seek(0)
        merger.append(PdfReader(landscape_buffer))
        
        # Write merged PDF
        final_buffer = BytesIO()
        merger.write(final_buffer)
        merger.close()
        
        buffer.close()
        landscape_buffer.close()
        
        pdf_bytes = final_buffer.getvalue()
        final_buffer.close()
        
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
    ]
    
    table = Table(summary_data, colWidths=[10*cm, 5*cm])
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
    Add two matrix tables showing 6 positions with Y2/Y1 averages per test date
    - Top table: Y2 (top) values
    - Bottom table: Y1 (bottom) values
    Rows: Position 1-6 with reference ranges
    Columns: Test dates
    Values: blade_top_average (Y2) and blade_bottom_average (Y1)
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
    
    # Define position reference ranges
    position_ranges_y2 = [
        "40mm",
        "30mm",
        "20mm",
        "0mm",
        "−10mm",
        "−20mm"
    ]

    position_ranges_y1 = [
        "20mm",
        "10mm",
        "0mm",
        "−20mm",
        "−30mm",
        "−40mm"
    ]
    
    elements.append(Paragraph("Y2 (Lame Supérieure)", getSampleStyleSheet()['Heading3']))
    elements.append(Spacer(1, 0.3*cm))
    
    y2_header = ['Position', 'Référence']
    for test in sorted_tests:
        test_date = datetime.fromisoformat(test['test_date']).strftime('%d/%m')
        y2_header.append(test_date)
    
    y2_table_data = [y2_header]
    
    for img_num in range(1, 7):
        row = [f'Position {img_num}', position_ranges_y2[img_num - 1]]
        
        for test in sorted_tests:
            test_id = test['test_id']
            
            if test_id in image_data and img_num in image_data[test_id]:
                top_val = image_data[test_id][img_num]['top']
                row.append(f'{top_val:.2f}' if top_val is not None else '-')
            else:
                row.append('-')
        
        y2_table_data.append(row)
    
    # Calculate column widths for Y2 table
    num_tests = len(sorted_tests)
    position_col_width = 2.0 * cm
    reference_col_width = 2.5 * cm
    value_col_width = 1.8 * cm
    
    y2_col_widths = [position_col_width, reference_col_width] + [value_col_width] * num_tests
    
    # Create Y2 table
    y2_table = Table(y2_table_data, colWidths=y2_col_widths)
    
    y2_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Data rows styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Bold position numbers
    ])
    
    y2_table.setStyle(y2_style)
    elements.append(y2_table)
    elements.append(Spacer(1, 1*cm))
    
    # Build Y1 (Bottom) Table
    elements.append(Paragraph("Y1 (Lame Inférieure)", getSampleStyleSheet()['Heading3']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Y1 Table header
    y1_header = ['Position', 'Référence']
    for test in sorted_tests:
        test_date = datetime.fromisoformat(test['test_date']).strftime('%d/%m')
        y1_header.append(test_date)
    
    y1_table_data = [y1_header]
    
    # Add rows for each of the 6 positions (Y1 values)
    for img_num in range(1, 7):
        row = [f'Position {img_num}', position_ranges_y1[img_num - 1]]
        
        for test in sorted_tests:
            test_id = test['test_id']
            
            if test_id in image_data and img_num in image_data[test_id]:
                bottom_val = image_data[test_id][img_num]['bottom']
                row.append(f'{bottom_val:.2f}' if bottom_val is not None else '-')
            else:
                row.append('-')
        
        y1_table_data.append(row)
    
    # Create Y1 table with same column widths
    y1_table = Table(y1_table_data, colWidths=y2_col_widths)
    
    y1_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Data rows styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Bold position numbers
    ])
    
    y1_table.setStyle(y1_style)
    elements.append(y1_table)
    
    return elements


def add_images_page(data: Dict[str, Any]) -> BytesIO:
    """
    Create a page showing the 6 DICOM images from the 13-11-2025 folder
    
    Returns:
        BytesIO: PDF buffer with the images page
    """
    import pydicom
    import os
    
    # Hardcoded path to the images folder (TODO: change)
    images_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        'uploads', 
        'AQUA-Exactitude', 
        '13-11-2025'
    )
    
    logger.info(f"[PDF-IMAGES] Loading images from: {images_dir}")
    
    if not os.path.exists(images_dir):
        logger.warning(f"[PDF-IMAGES] Directory not found: {images_dir}")
        return None
    
    # Get all DICOM files and sort them
    dcm_files = sorted([f for f in os.listdir(images_dir) if f.endswith('.dcm')])
    
    if len(dcm_files) < 6:
        logger.warning(f"[PDF-IMAGES] Not enough DICOM files found: {len(dcm_files)}")
        return None
    
    logger.info(f"[PDF-IMAGES] Found {len(dcm_files)} DICOM files")
    
    # Create matplotlib figure with 3x2 grid
    fig, axes = plt.subplots(3, 2, figsize=(11, 8.5))
    axes = axes.flatten()
    
    # Load and display the first 6 DICOM images
    for idx in range(6):
        ax = axes[idx]
        dcm_path = os.path.join(images_dir, dcm_files[idx])
        
        logger.info(f"[PDF-IMAGES] Loading image {idx + 1}: {dcm_files[idx]}")
        
        try:
            # Load DICOM image
            ds = pydicom.dcmread(dcm_path)
            image = ds.pixel_array
            
            # Display image without inversion
            ax.imshow(image, cmap='gray')
            ax.set_title(f'Position {idx + 1}', fontsize=12, fontweight='bold')
            ax.axis('off')
            
            logger.info(f"[PDF-IMAGES] Successfully loaded image {idx + 1}")
        except Exception as e:
            logger.error(f"[PDF-IMAGES] Error loading image {idx + 1} from {dcm_path}: {e}")
            ax.text(0.5, 0.5, 'Erreur de chargement', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Position {idx + 1}', fontsize=12, fontweight='bold')
            ax.axis('off')
    
    plt.suptitle('Images DICOM - 13-11-2025', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # Save figure to buffer
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    
    # Create PDF page with the images
    images_pdf_buffer = BytesIO()
    images_doc = SimpleDocTemplate(
        images_pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    images_elements = []
    images_img = Image(img_buffer, width=26*cm, height=18*cm)
    images_elements.append(images_img)
    
    images_doc.build(images_elements)
    images_pdf_buffer.seek(0)
    
    logger.info("[PDF-IMAGES] Images page created successfully")
    return images_pdf_buffer


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
        img = Image(img_buffer, width=17.5*cm, height=24*cm)
        elements.append(img)
        elements.append(Spacer(1, 0.5*cm))
        
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
        
        table = Table(chunk_data, colWidths=[2*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        
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
