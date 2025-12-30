"""
Enhanced MLC Blade Report Generator
Generates detailed PDF reports with blade analysis, graphs, and compliance tables
"""
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import base64

logger = logging.getLogger(__name__)

# ReportLab imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Data processing
import pandas as pd
import numpy as np

# Visualization
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

import sys
sys.path.append('..')
from database import SessionLocal, MLCLeafJawTest, LeafPositionTest, LeafPositionResult
from database.queries import get_mlc_test_session_by_id, get_leaf_position_test_by_id


class MLCBladeReportGenerator:
    """Generate comprehensive MLC blade analysis reports"""
    
    # Tolerance thresholds (in mm)
    TOLERANCE_20MM = 1.0
    TOLERANCE_30MM = 1.0
    TOLERANCE_40MM = 1.0
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional reports"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            spaceBefore=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#3182ce'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        ))
        
        # Summary box style
        self.styles.add(ParagraphStyle(
            name='SummaryText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2d3748'),
            leading=16,
            fontName='Helvetica-Bold'
        ))
    
    def generate_blade_compliance_report(
        self,
        test_ids: List[int],
        blade_size: str = "all",  # "20mm", "30mm", "40mm", or "all"
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate comprehensive blade compliance report
        
        Args:
            test_ids: List of test IDs to include in report
            blade_size: Size filter ("20mm", "30mm", "40mm", or "all")
            output_path: Optional path to save PDF
        
        Returns:
            PDF data as bytes
        """
        # Collect test data
        tests_data = []
        session = SessionLocal()
        
        try:
            for test_id in test_ids:
                # Try Leaf Position tests FIRST (they have blade_results)
                test_dict = get_leaf_position_test_by_id(test_id)
                
                # If not found, try MLC Leaf Jaw tests
                if not test_dict:
                    test_dict = get_mlc_test_session_by_id(test_id)
                
                if test_dict:
                    tests_data.append(test_dict)
            
            if not tests_data:
                raise ValueError("No valid tests found")
            
            # Sort by date
            tests_data.sort(key=lambda x: x.get('test_date', ''))
            
        finally:
            session.close()
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            topMargin=0.75*inch, 
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch, 
            rightMargin=0.75*inch
        )
        
        story = []
        
        # Add cover page
        story.extend(self._create_cover_page(tests_data, blade_size))
        story.append(PageBreak())
        
        # Add executive summary
        story.extend(self._create_executive_summary(tests_data, blade_size))
        story.append(PageBreak())
        
        # Add single comprehensive graph (all blades together)
        story.extend(self._create_comprehensive_blade_graph(tests_data, blade_size))
        story.append(PageBreak())
        
        # Add matrix table (dates as columns, blade numbers as rows)
        story.extend(self._create_matrix_table(tests_data, blade_size))
        
        # Add methodology annex
        story.append(PageBreak())
        story.extend(self._create_methodology_annex())
        
        # Build PDF
        doc.build(story)
        
        # Save if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_cover_page(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create report cover page"""
        elements = []
        
        # Title
        title_text = "Rapport de Conformité des Lames MLC"
        title = Paragraph(title_text, self.styles['ReportTitle'])
        elements.append(Spacer(1, 1.5*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        if blade_size != "all":
            subtitle = Paragraph(
                f"<b>Analyse des lames {blade_size.upper()}</b>",
                self.styles['SectionHeading']
            )
            elements.append(subtitle)
            elements.append(Spacer(1, 0.3*inch))
        
        # Date range
        start_date = datetime.fromisoformat(tests_data[0]['test_date']).strftime('%d/%m/%Y')
        end_date = datetime.fromisoformat(tests_data[-1]['test_date']).strftime('%d/%m/%Y')
        
        date_info = Paragraph(
            f"<b>Période d'analyse :</b> {start_date} - {end_date}",
            self.styles['ReportBody']
        )
        elements.append(date_info)
        elements.append(Spacer(1, 0.2*inch))
        
        # Generation info
        gen_date = datetime.now().strftime('%d/%m/%Y %H:%M')
        gen_info = Paragraph(
            f"<b>Date de génération :</b> {gen_date}",
            self.styles['ReportBody']
        )
        elements.append(gen_info)
        elements.append(Spacer(1, 0.2*inch))
        
        # Number of tests
        test_count = Paragraph(
            f"<b>Nombre de tests analysés :</b> {len(tests_data)}",
            self.styles['ReportBody']
        )
        elements.append(test_count)
        
        return elements
    
    def _create_executive_summary(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create executive summary with key statistics"""
        elements = []
        
        # Section title
        title = Paragraph("Résumé Exécutif", self.styles['SectionHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Extract blade data from all tests
        all_blades = []
        for test in tests_data:
            blade_results = test.get('blade_results', [])
            for blade in blade_results:
                if blade_size == "all" or self._get_blade_size_category(blade) == blade_size:
                    all_blades.append(blade)
        
        if not all_blades:
            elements.append(Paragraph("Aucune donnée de lame disponible.", self.styles['ReportBody']))
            return elements
        
        # Calculate statistics
        total_blades = len(all_blades)
        compliant_blades = sum(1 for b in all_blades if b.get('is_valid') == 'OK')
        non_compliant_blades = sum(1 for b in all_blades if b.get('is_valid') == 'OUT_OF_TOLERANCE')
        closed_blades = sum(1 for b in all_blades if b.get('is_valid') == 'CLOSED')
        
        compliance_rate = (compliant_blades / total_blades * 100) if total_blades > 0 else 0
        
        # Summary statistics table
        summary_data = [
            ['<b>Métrique</b>', '<b>Valeur</b>'],
            ['Nombre total de lames testées', str(total_blades)],
            ['Lames conformes', f"{compliant_blades} ({compliance_rate:.1f}%)"],
            ['Lames hors tolérance', f"{non_compliant_blades} ({non_compliant_blades/total_blades*100:.1f}%)"],
            ['Lames fermées', f"{closed_blades} ({closed_blades/total_blades*100:.1f}%)"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3182ce')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Major anomalies
        anomalies = self._identify_major_anomalies(all_blades)
        if anomalies:
            elements.append(Paragraph("Anomalies Majeures Identifiées", self.styles['SubsectionHeading']))
            elements.append(Spacer(1, 0.1*inch))
            
            for anomaly in anomalies[:5]:  # Top 5 anomalies
                anomaly_text = Paragraph(
                    f"• Lame {anomaly['blade_id']}: {anomaly['description']}",
                    self.styles['ReportBody']
                )
                elements.append(anomaly_text)
        
        return elements
    
    def _create_trend_graphs(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create trend graphs for blade measurements over time"""
        elements = []
        
        # Section title
        title = Paragraph(
            f"Graphiques de Tendance - Lames {blade_size.upper()}",
            self.styles['SectionHeading']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Extract blade data over time
        dates = []
        blade_sizes = {}
        
        for test in tests_data:
            test_date = datetime.fromisoformat(test['test_date'])
            blade_results = test.get('blade_results', [])
            
            for blade in blade_results:
                if self._get_blade_size_category(blade) == blade_size:
                    blade_id = blade.get('blade_pair', blade.get('blade_id', 'unknown'))
                    if blade_id not in blade_sizes:
                        blade_sizes[blade_id] = {'dates': [], 'sizes': [], 'status': []}
                    
                    blade_sizes[blade_id]['dates'].append(test_date)
                    blade_sizes[blade_id]['sizes'].append(blade.get('field_size_mm', 0))
                    blade_sizes[blade_id]['status'].append(blade.get('is_valid', 'UNKNOWN'))
        
        if not blade_sizes:
            elements.append(Paragraph("Aucune donnée disponible pour cette taille.", self.styles['ReportBody']))
            return elements
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get tolerance based on size
        tolerance = self._get_tolerance(blade_size)
        target_size = float(blade_size.replace('mm', ''))
        
        # Plot tolerance bands
        ax.axhline(y=target_size + tolerance, color='red', linestyle='--', 
                   alpha=0.3, label=f'Tolérance ±{tolerance}mm', linewidth=2)
        ax.axhline(y=target_size - tolerance, color='red', linestyle='--', 
                   alpha=0.3, linewidth=2)
        ax.axhline(y=target_size, color='green', linestyle='-', 
                   alpha=0.5, label='Valeur cible', linewidth=2)
        
        # Extract blade numbers and sort them
        blade_numbers = {}
        for blade_id, data in blade_sizes.items():
            # Extract numeric blade number from blade_pair
            try:
                if isinstance(blade_id, int):
                    blade_num = blade_id
                elif isinstance(blade_id, str) and blade_id.isdigit():
                    blade_num = int(blade_id)
                else:
                    blade_num = int(''.join(filter(str.isdigit, str(blade_id).split('-')[0])))
            except:
                blade_num = 0
            blade_numbers[blade_num] = (blade_id, data)
        
        # Plot each blade by number
        for blade_num in sorted(blade_numbers.keys()):
            blade_id, data = blade_numbers[blade_num]
            dates = data['dates']
            sizes = data['sizes']
            status_list = data['status']
            
            # Use average size for this blade across all tests
            avg_size = sum(sizes) / len(sizes) if sizes else target_size
            
            # Color by overall status
            has_ok = 'OK' in status_list
            has_oot = 'OUT_OF_TOLERANCE' in status_list
            
            if has_oot:
                color = 'red'
                marker = 'x'
            elif has_ok:
                color = 'green'
                marker = 'o'
            else:
                color = 'black'
                marker = 'x'
            
            # Plot single point at blade number with average size
            ax.scatter(blade_num, avg_size, c=color, marker=marker, s=80, alpha=0.8, zorder=3)
        
        # Format plot
        ax.set_xlabel('Numéro de Lame', fontsize=12, fontweight='bold')
        ax.set_ylabel('Taille Mesurée (mm)', fontsize=12, fontweight='bold')
        ax.set_title(f'Résultats des Lames {blade_size.upper()}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper right', fontsize=10)
        
        # Set X axis to show blade numbers
        if blade_numbers:
            min_blade = min(blade_numbers.keys())
            max_blade = max(blade_numbers.keys())
            ax.set_xlim(min_blade - 1, max_blade + 1)
            ax.set_xticks(sorted(blade_numbers.keys()))
        
        plt.tight_layout()
        
        # Save plot to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        # Add to PDF
        img = Image(img_buffer, width=7*inch, height=4.2*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        # Add legend explanation
        legend_text = """
        <b>Légende :</b><br/>
        • <font color="green">Vert (○)</font> : Lame conforme (dans la tolérance)<br/>
        • <font color="red">Rouge (×)</font> : Lame hors tolérance<br/>
        • Noir (×) : Lame fermée
        """
        elements.append(Paragraph(legend_text, self.styles['ReportBody']))
        
        return elements
    
    def _create_detailed_tables(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create detailed tables with all blade measurements"""
        elements = []
        
        # Section title
        title = Paragraph("Tableaux Récapitulatifs Détaillés", self.styles['SectionHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Group by blade size
        if blade_size == "all":
            sizes_to_process = ["20mm", "30mm", "40mm"]
        else:
            sizes_to_process = [blade_size]
        
        for size in sizes_to_process:
            elements.extend(self._create_size_specific_table(tests_data, size))
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_size_specific_table(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create table for specific blade size"""
        elements = []
        
        # Subsection title
        subtitle = Paragraph(f"Lames {blade_size.upper()} – Résultats des Tests", 
                            self.styles['SubsectionHeading'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.1*inch))
        
        # Collect blade data
        blade_rows = []
        
        for test in tests_data:
            test_date = datetime.fromisoformat(test['test_date']).strftime('%d/%m')
            blade_results = test.get('blade_results', [])
            
            for blade in blade_results:
                if self._get_blade_size_category(blade) == blade_size:
                    blade_id = blade.get('blade_pair', blade.get('blade_id', '-'))
                    
                    # Extract numeric blade number
                    try:
                        if isinstance(blade_id, int):
                            blade_num = blade_id
                        elif isinstance(blade_id, str) and blade_id.isdigit():
                            blade_num = int(blade_id)
                        else:
                            blade_num = int(''.join(filter(str.isdigit, str(blade_id).split('-')[0])))
                    except:
                        blade_num = blade_id
                    
                    v_sup = blade.get('v_sup_px', blade.get('distance_sup_mm', '-'))
                    v_inf = blade.get('v_inf_px', blade.get('distance_inf_mm', '-'))
                    top = blade.get('top_mm', '-')
                    bottom = blade.get('bottom_mm', '-')
                    size = blade.get('field_size_mm', '-')
                    status = blade.get('is_valid', 'UNKNOWN')
                    
                    # Format values
                    v_sup_str = f"{v_sup:.0f}" if isinstance(v_sup, (int, float)) else str(v_sup)
                    v_inf_str = f"{v_inf:.0f}" if isinstance(v_inf, (int, float)) else str(v_inf)
                    top_str = f"{top:.2f}" if isinstance(top, (int, float)) else str(top)
                    bottom_str = f"{bottom:.2f}" if isinstance(bottom, (int, float)) else str(bottom)
                    size_str = f"{size:.2f}" if isinstance(size, (int, float)) else str(size)
                    
                    # Determine compliance icon
                    compliance = "✓" if status == 'OK' else "✗" if status == 'OUT_OF_TOLERANCE' else "×"
                    
                    # Calculate deviation
                    target = float(blade_size.replace('mm', ''))
                    deviation = ""
                    if isinstance(size, (int, float)):
                        dev = size - target
                        deviation = f"+{dev:.2f}mm" if dev > 0 else f"{dev:.2f}mm"
                    
                    blade_rows.append([
                        str(blade_num),
                        v_sup_str,
                        v_inf_str,
                        top_str,
                        bottom_str,
                        size_str,
                        compliance,
                        deviation if deviation else "-"
                    ])
        
        if not blade_rows:
            elements.append(Paragraph("Aucune donnée disponible.", self.styles['ReportBody']))
            return elements
        
        # Create table
        header = [['Lame', 'V_sup (px)', 'V_inf (px)', 'Top (mm)', 
                  'Bottom (mm)', 'Size (mm)', 'Conformité', 'Commentaires']]
        table_data = header + blade_rows[:100]  # Limit to 100 rows
        
        col_widths = [0.6*inch, 0.9*inch, 0.9*inch, 0.9*inch, 
                     0.9*inch, 0.9*inch, 0.9*inch, 1.2*inch]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor('#f7fafc')]),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(table)
        
        if len(blade_rows) > 100:
            note = Paragraph(
                f"<i>Affichage de 100 sur {len(blade_rows)} mesures</i>",
                self.styles['ReportBody']
            )
            elements.append(Spacer(1, 0.05*inch))
            elements.append(note)
        
        return elements
    
    def _create_methodology_annex(self) -> List:
        """Create methodology and technical notes annex"""
        elements = []
        
        # Title
        title = Paragraph("Annexe : Méthodologie et Notes Techniques", 
                         self.styles['SectionHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Tolerance section
        elements.append(Paragraph("Tolérances Appliquées", self.styles['SubsectionHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        tolerance_text = f"""
        Les tolérances suivantes sont appliquées pour déterminer la conformité des lames :<br/>
        <br/>
        • <b>Lames 20mm :</b> ±{self.TOLERANCE_20MM} mm<br/>
        • <b>Lames 30mm :</b> ±{self.TOLERANCE_30MM} mm<br/>
        • <b>Lames 40mm :</b> ±{self.TOLERANCE_40MM} mm<br/>
        <br/>
        Une lame est considérée comme <b>conforme</b> si sa taille mesurée se situe 
        dans la plage de tolérance par rapport à la valeur cible.
        """
        elements.append(Paragraph(tolerance_text, self.styles['ReportBody']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Measurement method
        elements.append(Paragraph("Méthode de Mesure", self.styles['SubsectionHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        method_text = """
        Les mesures sont effectuées par analyse d'images DICOM à l'aide d'algorithmes 
        de détection de contours et de traitement d'images. Les paramètres mesurés incluent :<br/>
        <br/>
        • <b>V_sup et V_inf :</b> Coordonnées en pixels des bords supérieur et inférieur<br/>
        • <b>Top et Bottom :</b> Distances en millimètres depuis les bords de référence<br/>
        • <b>Size :</b> Taille effective de l'ouverture de la lame en millimètres<br/>
        <br/>
        Les conversions pixel-millimètre sont basées sur les métadonnées DICOM 
        et calibrations du système d'imagerie.
        """
        elements.append(Paragraph(method_text, self.styles['ReportBody']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Status codes
        elements.append(Paragraph("Codes de Statut", self.styles['SubsectionHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        status_data = [
            ['<b>Statut</b>', '<b>Symbole</b>', '<b>Description</b>'],
            ['OK', '✅', 'Lame conforme, dans la tolérance'],
            ['OUT_OF_TOLERANCE', '❌', 'Lame hors tolérance, nécessite attention'],
            ['CLOSED', '⚫', 'Lame fermée (non applicable)'],
        ]
        
        status_table = Table(status_data, colWidths=[1.8*inch, 1.0*inch, 3.7*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(status_table)
        
        return elements
    
    # Helper methods
    
    def _get_blade_size_category(self, blade: Dict) -> str:
        """Determine blade size category from blade data"""
        size = blade.get('field_size_mm', 0)
        if isinstance(size, (int, float)):
            if 18 <= size <= 22:
                return "20mm"
            elif 28 <= size <= 32:
                return "30mm"
            elif 38 <= size <= 42:
                return "40mm"
        return "unknown"
    
    def _get_tolerance(self, blade_size: str) -> float:
        """Get tolerance value for blade size"""
        tolerance_map = {
            "20mm": self.TOLERANCE_20MM,
            "30mm": self.TOLERANCE_30MM,
            "40mm": self.TOLERANCE_40MM
        }
        return tolerance_map.get(blade_size, 1.0)
    
    def _identify_major_anomalies(self, blades: List[Dict]) -> List[Dict]:
        """Identify major anomalies in blade measurements"""
        anomalies = []
        
        for blade in blades:
            if blade.get('is_valid') == 'OUT_OF_TOLERANCE':
                blade_id = blade.get('blade_pair', blade.get('blade_id', 'unknown'))
                size = blade.get('field_size_mm', 0)
                size_category = self._get_blade_size_category(blade)
                
                if size_category != "unknown":
                    target = float(size_category.replace('mm', ''))
                    deviation = size - target
                    tolerance = self._get_tolerance(size_category)
                    
                    if abs(deviation) > tolerance:
                        anomalies.append({
                            'blade_id': blade_id,
                            'description': f"Taille hors tolérance de {deviation:+.2f}mm (cible: {target}mm)",
                            'severity': abs(deviation) - tolerance
                        })
        
        
        # Sort by severity
        anomalies.sort(key=lambda x: x['severity'], reverse=True)
        
        return anomalies
    
    def _create_comprehensive_blade_graph(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create single graph with all blades (27-54) on X-axis"""
        elements = []
        
        # Section title
        title = Paragraph("Graphique de Conformité des Lames MLC", self.styles['SectionHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Collect all blade data
        blade_data_dict = {}  # {blade_num: {'sizes': [], 'statuses': [], 'target': float}}
        
        for test in tests_data:
            blade_results = test.get('blade_results', [])
            
            for blade in blade_results:
                # Skip if filtering by size and doesn't match
                if blade_size != "all" and self._get_blade_size_category(blade) != blade_size:
                    continue
                
                blade_id = blade.get('blade_pair', 'unknown')
                try:
                    # Handle both string and int blade_pair values
                    if isinstance(blade_id, int):
                        blade_num = blade_id
                    elif isinstance(blade_id, str) and blade_id.isdigit():
                        blade_num = int(blade_id)
                    else:
                        # Extract number from format like "A1-B1" or "27"
                        blade_num = int(''.join(filter(str.isdigit, str(blade_id).split('-')[0])))
                except:
                    continue
                
                if blade_num not in blade_data_dict:
                    blade_data_dict[blade_num] = {
                        'sizes': [],
                        'statuses': [],
                        'target': blade.get('field_size_mm', 20.0)  # Will be averaged
                    }
                
                blade_data_dict[blade_num]['sizes'].append(blade.get('field_size_mm', 0))
                blade_data_dict[blade_num]['statuses'].append(blade.get('is_valid', 'UNKNOWN'))
        
        if not blade_data_dict:
            elements.append(Paragraph("Aucune donnée disponible.", self.styles['ReportBody']))
            return elements
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot each blade
        blade_numbers = sorted(blade_data_dict.keys())
        for blade_num in blade_numbers:
            data = blade_data_dict[blade_num]
            
            # Filter out CLOSED blades from average calculation
            valid_sizes = [size for i, size in enumerate(data['sizes']) 
                          if data['statuses'][i] != 'CLOSED']
            
            if not valid_sizes:
                # All blades are closed, skip this blade
                continue
            
            avg_size = sum(valid_sizes) / len(valid_sizes)
            
            # Determine target based on blade size category
            size_cat = self._get_blade_size_category({'field_size_mm': avg_size})
            target = float(size_cat.replace('mm', '')) if size_cat != 'unknown' else avg_size
            tolerance = self._get_tolerance(size_cat)
            
            # Color by status (ignore CLOSED when determining color)
            non_closed_statuses = [s for s in data['statuses'] if s != 'CLOSED']
            has_oot = 'OUT_OF_TOLERANCE' in non_closed_statuses
            color = 'red' if has_oot else 'green'
            marker = 'x' if has_oot else 'o'
            
            # Plot point
            ax.scatter(blade_num, avg_size, c=color, marker=marker, s=80, alpha=0.8, zorder=3)
        
        # Add target lines and tolerance bands for each size category
        # 20mm zone
        if any(27 <= b <= 32 for b in blade_numbers):
            ax.axhline(y=20.0, xmin=0, xmax=0.2, color='green', linestyle='-', alpha=0.5, linewidth=2)
            ax.axhspan(19.0, 21.0, xmin=0, xmax=0.22, alpha=0.1, color='green')
        # 30mm zone
        if any(33 <= b <= 42 for b in blade_numbers):
            ax.axhline(y=30.0, xmin=0.22, xmax=0.58, color='green', linestyle='-', alpha=0.5, linewidth=2)
            ax.axhspan(29.0, 31.0, xmin=0.22, xmax=0.58, alpha=0.1, color='green')
        # 40mm zone
        if any(43 <= b <= 54 for b in blade_numbers):
            ax.axhline(y=40.0, xmin=0.58, xmax=1.0, color='green', linestyle='-', alpha=0.5, linewidth=2)
            ax.axhspan(39.0, 41.0, xmin=0.58, xmax=1.0, alpha=0.1, color='green')
        
        # Format plot
        ax.set_xlabel('Numéro de Lame', fontsize=12, fontweight='bold')
        ax.set_ylabel('Taille Mesurée (mm)', fontsize=12, fontweight='bold')
        ax.set_title('Résultats de Conformité pour Toutes les Lames', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlim(26, 55)
        ax.set_xticks(blade_numbers)
        ax.set_ylim(15, 45)
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Conforme'),
            Line2D([0], [0], marker='x', color='w', markerfacecolor='red', markersize=10, label='Hors tolérance')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        # Add to PDF
        img = Image(img_buffer, width=7.5*inch, height=3.75*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_matrix_table(self, tests_data: List[Dict], blade_size: str) -> List:
        """Create matrix table: rows=blade numbers, columns=test dates"""
        elements = []
        
        # Section title
        title = Paragraph("Tableau Matriciel des Écarts de Tolérance", self.styles['SectionHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Collect data organized by blade and date
        blade_date_matrix = {}  # {blade_num: {date_str: deviation}}
        test_dates = []
        
        for test in tests_data:
            test_date = datetime.fromisoformat(test['test_date']).strftime('%d/%m')
            if test_date not in test_dates:
                test_dates.append(test_date)
            
            blade_results = test.get('blade_results', [])
            
            for blade in blade_results:
                if blade_size != "all" and self._get_blade_size_category(blade) != blade_size:
                    continue
                
                blade_id = blade.get('blade_pair', 'unknown')
                try:
                    if isinstance(blade_id, int):
                        blade_num = blade_id
                    elif isinstance(blade_id, str) and blade_id.isdigit():
                        blade_num = int(blade_id)
                    else:
                        blade_num = int(''.join(filter(str.isdigit, str(blade_id).split('-')[0])))
                except:
                    continue
                
                if blade_num not in blade_date_matrix:
                    blade_date_matrix[blade_num] = {}
                
                # Calculate deviation
                size = blade.get('field_size_mm', 0)
                size_cat = self._get_blade_size_category(blade)
                target = float(size_cat.replace('mm', '')) if size_cat != 'unknown' else size
                tolerance = self._get_tolerance(size_cat)
                deviation = size - target
                status = blade.get('is_valid', 'UNKNOWN')
                
                # Store deviation value with status indicator
                if status == 'CLOSED':
                    blade_date_matrix[blade_num][test_date] = ('CLOSED', status)
                elif status == 'OUT_OF_TOLERANCE' or abs(deviation) > tolerance:
                    blade_date_matrix[blade_num][test_date] = (f"{deviation:+.2f}", 'OUT_OF_TOLERANCE')
                else:
                    blade_date_matrix[blade_num][test_date] = (f"{deviation:+.2f}", 'OK')
        
        if not blade_date_matrix:
            elements.append(Paragraph("Aucune donnée disponible.", self.styles['ReportBody']))
            return elements
        
        # Build table
        table_data = [['Lame'] + test_dates]  # Header row
        
        for blade_num in sorted(blade_date_matrix.keys()):
            row = [str(blade_num)]
            for date in test_dates:
                cell_data = blade_date_matrix[blade_num].get(date, ('-', 'NONE'))
                # Extract just the value for display (first element of tuple)
                value = cell_data[0] if isinstance(cell_data, tuple) else cell_data
                row.append(value)
            table_data.append(row)
        
        # Create table
        col_widths = [0.6*inch] + [1.0*inch] * len(test_dates)
        table = Table(table_data, colWidths=col_widths)
        
        # Style table
        table_style = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # First column (blade numbers)
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            
            # Data cells
            ('FONTSIZE', (1, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]
        
        # Color code cells based on status
        for row_idx in range(1, len(table_data)):
            blade_num = int(table_data[row_idx][0])
            for col_idx in range(1, len(table_data[row_idx])):
                date_str = test_dates[col_idx - 1]
                cell_data = blade_date_matrix.get(blade_num, {}).get(date_str, ('-', 'NONE'))
                
                if isinstance(cell_data, tuple):
                    cell_value, status = cell_data
                else:
                    cell_value = cell_data
                    status = 'NONE'
                
                if status == 'OUT_OF_TOLERANCE':
                    # Out of tolerance - red background with dark red text
                    table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#fee2e2')))
                    table_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#991b1b')))
                    table_style.append(('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold'))
                elif status == 'OK':
                    # Within tolerance - green text
                    table_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#15803d')))
                elif status == 'CLOSED':
                    # Closed - gray background with dark text
                    table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#f3f4f6')))
                    table_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#6b7280')))
                    table_style.append(('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold'))
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add legend
        legend_text = """
        <b>Légende du tableau :</b><br/>
        • <font color="#15803d"><b>±X.XX</b></font> : Écart en mm - Lame conforme (dans la tolérance)<br/>
        • <font color="#991b1b"><b>±X.XX</b></font> : Écart en mm - Lame hors tolérance<br/>
        • <font color="#6b7280"><b>CLOSED</b></font> : Lame fermée<br/>
        • <b>-</b> : Pas de données pour ce test
        """
        elements.append(Paragraph(legend_text, self.styles['ReportBody']))
        
        return elements


# Convenience functions
def generate_blade_report(test_ids: List[int], blade_size: str = "all", 
                         output_path: Optional[str] = None) -> bytes:
    """
    Generate MLC blade compliance report
    
    Args:
        test_ids: List of test IDs to analyze
        blade_size: "20mm", "30mm", "40mm", or "all"
        output_path: Optional path to save PDF
    
    Returns:
        PDF data as bytes
    """
    generator = MLCBladeReportGenerator()
    return generator.generate_blade_compliance_report(test_ids, blade_size, output_path)

