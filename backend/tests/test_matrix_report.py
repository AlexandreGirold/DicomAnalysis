import sys
sys.path.insert(0, 'c:\\Users\\agirold\\Desktop\\DicomAnalysis\\backend')

try:
    from services.mlc_blade_report_generator import generate_blade_report
    
    print("Generating report...")
    pdf_bytes = generate_blade_report([11, 12, 13, 14, 15], "all")
    
    print(f"✓ PDF generated: {len(pdf_bytes)} bytes")
    
    # Save to file
    with open('test_matrix_report.pdf', 'wb') as f:
        f.write(pdf_bytes)
    
    print("✓ Saved to test_matrix_report.pdf")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
