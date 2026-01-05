import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from services.mlc_blade_report_generator import MLCBladeReportGenerator

# Test with Test ID 1, blade size = all
try:
    generator = MLCBladeReportGenerator()
    print("Generating report for test_ids=[1], blade_size='all'...")
    
    pdf_bytes = generator.generate_blade_compliance_report(
        test_ids=[1],
        blade_size='all'
    )
    
    print(f"✅ Success! Generated PDF with {len(pdf_bytes)} bytes")
    
    # Save to file
    output_path = 'test_report_output.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    print(f"Saved to: {output_path}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
