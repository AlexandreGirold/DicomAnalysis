"""
PDF Report Generator with Trend Analysis
Generates PDF reports for quality control tests with graphs and statistics
"""
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import base64

# ReportLab imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Data processing
import pandas as pd
import numpy as np
from scipy import stats

# Visualization
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import database as db


class PDFReportGenerator:
    """Generate PDF reports for quality control tests"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_single_test_report(self, test_id: int, output_path: str = None) -> bytes:
        """
        Generate PDF report for a single test
        
        Args:
            test_id: ID of test from MLC analysis or generic test database
            output_path: Optional path to save PDF file
        
        Returns:
            PDF data as bytes
        """
        # Try to get test from both MLC and generic databases
        test_data = db.get_test_by_id(test_id)
        if not test_data:
            test_data = db.get_generic_test_by_id(test_id)
        
        if not test_data:
            raise ValueError(f"Test {test_id} not found")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               topMargin=0.75*inch, bottomMargin=0.75*inch,
                               leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        story = []
        
        # Title
        title = Paragraph("Quality Control Test Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Test information
        story.extend(self._add_test_info(test_data))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary
        story.extend(self._add_test_summary(test_data))
        story.append(Spacer(1, 0.2*inch))
        
        # Visualizations
        if test_data.get('visualization') or test_data.get('visualization_paths'):
            story.extend(self._add_visualizations(test_data))
            story.append(PageBreak())
        
        # Detailed results (if available)
        if test_data.get('results'):
            story.extend(self._add_detailed_results(test_data))
        
        # Build PDF
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
        
        return pdf_data
    
    def generate_trend_report(self, test_type: str, start_date: str = None, 
                             end_date: str = None, output_path: str = None) -> bytes:
        """
        Generate PDF report with trend analysis for a specific test type
        
        Args:
            test_type: Test type identifier (e.g., "mlc_leaf_jaw", "niveau_helium")
            start_date: Start date for trend analysis (ISO format)
            end_date: End date for trend analysis (ISO format)
            output_path: Optional path to save PDF file
        
        Returns:
            PDF data as bytes
        """
        # Get all tests of this type in date range
        tests = db.get_all_generic_tests(test_type=test_type, 
                                         start_date=start_date, 
                                         end_date=end_date,
                                         limit=1000)
        
        if not tests:
            raise ValueError(f"No tests found for type '{test_type}'")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               topMargin=0.75*inch, bottomMargin=0.75*inch,
                               leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        story = []
        
        # Title
        test_name = tests[0]['test_name'] if tests else test_type
        title = Paragraph(f"Trend Analysis Report<br/>{test_name}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Report metadata
        story.extend(self._add_report_metadata(tests, start_date, end_date))
        story.append(Spacer(1, 0.3*inch))
        
        # Overall statistics
        story.extend(self._add_overall_statistics(tests))
        story.append(Spacer(1, 0.3*inch))
        
        # Trend analysis and graphs
        story.extend(self._add_trend_analysis(tests, test_type))
        story.append(PageBreak())
        
        # Test history table
        story.extend(self._add_test_history_table(tests))
        
        # Build PDF
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
        
        return pdf_data
    
    def _add_test_info(self, test_data: Dict) -> List:
        """Add test information section"""
        elements = []
        
        heading = Paragraph("Test Information", self.styles['CustomHeading'])
        elements.append(heading)
        
        # Create info table
        data = [
            ['Test ID:', str(test_data.get('id', '-'))],
            ['Filename:', test_data.get('filename', test_data.get('test_name', '-'))],
            ['Test Date:', self._format_date(test_data.get('file_creation_date') or test_data.get('test_date'))],
            ['Upload Date:', self._format_date(test_data.get('upload_date'))],
        ]
        
        # Add operator if available
        if test_data.get('operator'):
            data.append(['Operator:', test_data['operator']])
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _add_test_summary(self, test_data: Dict) -> List:
        """Add test summary section"""
        elements = []
        
        heading = Paragraph("Summary", self.styles['CustomHeading'])
        elements.append(heading)
        
        summary = test_data.get('summary', test_data.get('summary_data', {}))
        
        if not summary:
            elements.append(Paragraph("No summary data available", self.styles['CustomBody']))
            return elements
        
        # Create summary table
        data = [['Metric', 'Value', 'Status']]
        
        if 'total_blades' in summary:
            # MLC test format
            data.append(['Total Blades', str(summary['total_blades']), ''])
            data.append(['OK Blades', str(summary['ok_blades']), '✓'])
            data.append(['Out of Tolerance', str(summary['out_of_tolerance']), 
                        '✗' if summary['out_of_tolerance'] > 0 else ''])
            data.append(['Closed Blades', str(summary['closed_blades']), ''])
        else:
            # Generic summary format
            for key, value in summary.items():
                data.append([key.replace('_', ' ').title(), str(value), ''])
        
        table = Table(data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _add_visualizations(self, test_data: Dict) -> List:
        """Add visualization images to report"""
        elements = []
        
        heading = Paragraph("Visualizations", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.1*inch))
        
        # Get visualization paths
        viz_paths = test_data.get('visualization')
        if not viz_paths:
            viz_paths = test_data.get('visualization_paths', [])
        
        if isinstance(viz_paths, str):
            viz_paths = [viz_paths]
        
        # Add each visualization
        for viz_path in viz_paths:
            try:
                # Check if it's a base64 data URI
                if viz_path.startswith('data:image'):
                    # Extract base64 data
                    base64_data = viz_path.split(',')[1]
                    img_data = base64.b64decode(base64_data)
                    img_buffer = io.BytesIO(img_data)
                    img = Image(img_buffer, width=6*inch, height=4.5*inch)
                else:
                    # Load from file path
                    img_path = Path('backend/uploads') / viz_path
                    if not img_path.exists():
                        img_path = Path(viz_path)
                    
                    if img_path.exists():
                        img = Image(str(img_path), width=6*inch, height=4.5*inch)
                    else:
                        continue
                
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
                
            except Exception as e:
                print(f"Error adding visualization: {e}")
                continue
        
        return elements
    
    def _add_detailed_results(self, test_data: Dict) -> List:
        """Add detailed results table"""
        elements = []
        
        heading = Paragraph("Detailed Results", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.1*inch))
        
        results = test_data.get('results', test_data.get('test_results', []))
        
        if not results:
            elements.append(Paragraph("No detailed results available", self.styles['CustomBody']))
            return elements
        
        # Create results table (MLC format)
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict):
            data = [['Blade Pair', 'Dist. Sup (mm)', 'Dist. Inf (mm)', 'Field Size (mm)', 'Status']]
            
            for r in results[:50]:  # Limit to first 50 for readability
                data.append([
                    str(r.get('blade_pair', '-')),
                    f"{r.get('distance_sup_mm', 0):.3f}" if r.get('distance_sup_mm') is not None else '-',
                    f"{r.get('distance_inf_mm', 0):.3f}" if r.get('distance_inf_mm') is not None else '-',
                    f"{r.get('field_size_mm', 0):.3f}" if r.get('field_size_mm') is not None else '-',
                    r.get('status', '-')
                ])
            
            table = Table(data, colWidths=[1.2*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            
            elements.append(table)
        
        return elements
    
    def _add_report_metadata(self, tests: List[Dict], start_date: str, end_date: str) -> List:
        """Add report metadata"""
        elements = []
        
        heading = Paragraph("Report Information", self.styles['CustomHeading'])
        elements.append(heading)
        
        data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Number of Tests:', str(len(tests))],
            ['Date Range:', f"{start_date or 'All'} to {end_date or 'All'}"],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _add_overall_statistics(self, tests: List[Dict]) -> List:
        """Add overall statistics section"""
        elements = []
        
        heading = Paragraph("Overall Statistics", self.styles['CustomHeading'])
        elements.append(heading)
        
        # Calculate statistics
        total_tests = len(tests)
        pass_count = sum(1 for t in tests if t['overall_result'] == 'PASS')
        fail_count = sum(1 for t in tests if t['overall_result'] == 'FAIL')
        warning_count = sum(1 for t in tests if t['overall_result'] == 'WARNING')
        
        pass_rate = (pass_count / total_tests * 100) if total_tests > 0 else 0
        
        data = [
            ['Total Tests', str(total_tests)],
            ['Passed', f"{pass_count} ({pass_rate:.1f}%)"],
            ['Failed', str(fail_count)],
            ['Warnings', str(warning_count)],
        ]
        
        # Extract operators
        operators = set(t['operator'] for t in tests if t.get('operator'))
        if operators:
            data.append(['Operators', ', '.join(sorted(operators))])
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _add_trend_analysis(self, tests: List[Dict], test_type: str) -> List:
        """Add trend analysis with graphs"""
        elements = []
        
        heading = Paragraph("Trend Analysis", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.1*inch))
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': datetime.fromisoformat(t['test_date']),
            'result': t['overall_result'],
            'operator': t['operator']
        } for t in tests])
        
        df = df.sort_values('date')
        
        # Create trend graph
        fig, axes = plt.subplots(2, 1, figsize=(8, 6))
        
        # Plot 1: Pass/Fail over time
        df['result_numeric'] = df['result'].map({'PASS': 1, 'WARNING': 0.5, 'FAIL': 0})
        axes[0].plot(df['date'], df['result_numeric'], marker='o', linestyle='-', linewidth=2, markersize=6)
        axes[0].axhline(y=1, color='green', linestyle='--', alpha=0.3, label='Pass')
        axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.3, label='Fail')
        axes[0].set_ylabel('Test Result')
        axes[0].set_title('Test Results Over Time')
        axes[0].set_yticks([0, 0.5, 1])
        axes[0].set_yticklabels(['FAIL', 'WARNING', 'PASS'])
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        
        # Plot 2: Test frequency over time
        df['month'] = df['date'].dt.to_period('M')
        test_counts = df.groupby('month').size()
        test_counts.index = test_counts.index.to_timestamp()
        
        axes[1].bar(test_counts.index, test_counts.values, width=20, alpha=0.7, color='steelblue')
        axes[1].set_ylabel('Number of Tests')
        axes[1].set_xlabel('Date')
        axes[1].set_title('Test Frequency')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Format x-axis
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        # Add to PDF
        img = Image(img_buffer, width=6.5*inch, height=5*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        # Add statistical analysis
        elements.append(Paragraph("Statistical Analysis", self.styles['CustomHeading']))
        
        # Calculate trend (if enough data points)
        if len(df) >= 3:
            # Linear regression on numeric results
            x = np.arange(len(df))
            y = df['result_numeric'].values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            trend_text = "Improving" if slope > 0.01 else "Declining" if slope < -0.01 else "Stable"
            
            stats_text = f"""
            <b>Trend Direction:</b> {trend_text}<br/>
            <b>Correlation (R²):</b> {r_value**2:.3f}<br/>
            <b>Statistical Significance:</b> {"Yes (p < 0.05)" if p_value < 0.05 else "No (p >= 0.05)"}<br/>
            """
            
            elements.append(Paragraph(stats_text, self.styles['CustomBody']))
        
        return elements
    
    def _add_test_history_table(self, tests: List[Dict]) -> List:
        """Add table of test history"""
        elements = []
        
        heading = Paragraph("Test History", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.1*inch))
        
        # Create table
        data = [['Date', 'Operator', 'Result']]
        
        for test in tests[:50]:  # Limit to 50 most recent
            data.append([
                datetime.fromisoformat(test['test_date']).strftime('%Y-%m-%d %H:%M'),
                test['operator'],
                test['overall_result']
            ])
        
        table = Table(data, colWidths=[2*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(table)
        
        if len(tests) > 50:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(f"<i>Showing 50 of {len(tests)} tests</i>", self.styles['CustomBody']))
        
        return elements
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if not date_str:
            return '-'
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(date_str)


# Convenience functions
def generate_test_report(test_id: int, output_path: str = None) -> bytes:
    """Generate PDF report for a single test"""
    generator = PDFReportGenerator()
    return generator.generate_single_test_report(test_id, output_path)


def generate_trend_report(test_type: str, start_date: str = None, 
                         end_date: str = None, output_path: str = None) -> bytes:
    """Generate PDF trend report for a test type"""
    generator = PDFReportGenerator()
    return generator.generate_trend_report(test_type, start_date, end_date, output_path)
