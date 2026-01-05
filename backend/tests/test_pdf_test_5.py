import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

from services.mlc_blade_report_generator import MLCBladeReportGenerator

try:
    gen = MLCBladeReportGenerator()
    print("Generating PDF for test ID 5 (2 images)...")
    pdf = gen.generate_blade_compliance_report([5], 'all')
    
    with open('test_5_with_avg.pdf', 'wb') as f:
        f.write(pdf)
    
    print(f"✅ PDF generated: {len(pdf)} bytes")
    print(f"Saved to: test_5_with_avg.pdf")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
