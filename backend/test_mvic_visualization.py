"""
Test MVIC_fente visualization
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / 'services'))

from services.weekly.MVIC_fente import test_mvic_fente

# Test with real DICOM file
test_dicom = r"R:\Radiotherapie - Physique Medicale\06 Contrôle qualité\01 Accélérateurs\11_UNITY\CQ_Mensuel\Collimation\2025\09\TailleChamp17-09-2025\RTI00348.dcm"

print("Testing MVIC_fente with visualization...")
print(f"File: {test_dicom}")

result = test_mvic_fente(
    files=[test_dicom],
    operator="Test Visualization",
    notes="Testing visualization feature"
)

print(f"\n✓ Test completed: {result['overall_result']}")
print(f"  Bands detected: {result['total_bands_detected']}")
print(f"  Visualizations: {result.get('visualizations', [])}")

if result.get('visualizations'):
    print(f"\n✓✓ Visualization generated successfully!")
    print(f"   File: {result['visualizations'][0]}")
else:
    print("\n⚠ No visualization generated")
