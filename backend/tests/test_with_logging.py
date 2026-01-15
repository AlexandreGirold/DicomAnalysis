import sys
import logging
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

# Enable logging
logging.basicConfig(level=logging.INFO)

from services.mlc_blade_report_generator import MLCBladeReportGenerator

# Test with Test ID 1
try:
    generator = MLCBladeReportGenerator()
    print("=" * 60)
    print("Generating report for test_ids=[1], blade_size='all'...")
    print("=" * 60)
    
    pdf_bytes = generator.generate_blade_compliance_report(
        test_ids=[1],
        blade_size='all'
    )
    
    print(f"\n✅ Success! Generated PDF with {len(pdf_bytes)} bytes")
    
    # Save to file
    output_path = 'test_report_debug.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    print(f"Saved to: {output_path}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
