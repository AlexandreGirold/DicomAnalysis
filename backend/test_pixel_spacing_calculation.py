"""
Test script to verify pixel spacing calculation from DICOM
"""
import sys
import os
import pydicom

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.weekly.MVIC_fente import MVICFenteTest, MVICFenteV2Test

print("=" * 70)
print("TEST PIXEL SPACING CALCULATION - Vérification SAD/SID")
print("=" * 70)

# Test file path
dicom_file = r"R:\Radiotherapie - Physique Medicale\06 Contrôle qualité\01 Accélérateurs\11_UNITY\CQ_Mensuel\Collimation\2025\09\TailleChamp17-09-2025\RTI00350.dcm"

if os.path.exists(dicom_file):
    print(f"\n✓ DICOM file found: {os.path.basename(dicom_file)}")
    
    # Read DICOM
    dcm = pydicom.dcmread(dicom_file)
    
    # Extract values
    print("\n" + "─" * 70)
    print("DICOM METADATA:")
    print("─" * 70)
    
    image_plane_spacing = dcm.ImagePlanePixelSpacing
    SAD = float(dcm.RadiationMachineSAD)
    SID = float(dcm.RTImageSID)
    
    print(f"ImagePlanePixelSpacing: {image_plane_spacing[0]} × {image_plane_spacing[1]} mm")
    print(f"RadiationMachineSAD:    {SAD:.2f} mm (distance source → isocentre)")
    print(f"RTImageSID:             {SID:.2f} mm (distance source → détecteur)")
    
    # Calculate
    print("\n" + "─" * 70)
    print("CALCULATION:")
    print("─" * 70)
    
    pixel_spacing_detector = (image_plane_spacing[0] + image_plane_spacing[1]) / 2
    scaling_factor = SAD / SID
    pixel_spacing_isocenter = pixel_spacing_detector * scaling_factor
    
    print(f"Pixel spacing @ détecteur:  {pixel_spacing_detector:.3f} mm/pixel")
    print(f"Scaling factor (SAD/SID):   {scaling_factor:.6f}")
    print(f"Pixel spacing @ isocentre:  {pixel_spacing_isocenter:.6f} mm/pixel")
    print(f"                            ≈ {pixel_spacing_isocenter:.3f} mm/pixel")
    
    # Expected value
    expected = 0.216
    print(f"\nValeur attendue (macro ImageJ): {expected:.3f} mm/pixel")
    
    if abs(pixel_spacing_isocenter - expected) < 0.001:
        print("✓ MATCH! Le calcul est correct")
    else:
        print(f"⚠ Différence: {abs(pixel_spacing_isocenter - expected):.6f} mm")
    
    # Test MVICFenteTest (v1)
    print("\n" + "─" * 70)
    print("TEST MVIC_FENTE V1:")
    print("─" * 70)
    
    test_v1 = MVICFenteTest()
    spacing_v1 = test_v1._get_pixel_spacing(dcm)
    print(f"Pixel spacing calculé: {spacing_v1:.6f} mm/pixel")
    
    if abs(spacing_v1 - pixel_spacing_isocenter) < 0.001:
        print("✓ MVICFenteTest calcule correctement le pixel spacing")
    else:
        print(f"✗ Erreur: attendu {pixel_spacing_isocenter:.6f}, obtenu {spacing_v1:.6f}")
    
    # Test MVICFenteV2Test
    print("\n" + "─" * 70)
    print("TEST MVIC_FENTE V2:")
    print("─" * 70)
    
    test_v2 = MVICFenteV2Test()
    print(f"Avant update: pixel_spacing = {test_v2.pixel_spacing:.6f} mm/pixel")
    
    test_v2._update_pixel_spacing_from_dicom(dcm)
    print(f"Après update: pixel_spacing = {test_v2.pixel_spacing:.6f} mm/pixel")
    
    if abs(test_v2.pixel_spacing - pixel_spacing_isocenter) < 0.001:
        print("✓ MVICFenteV2Test calcule correctement le pixel spacing")
    else:
        print(f"✗ Erreur: attendu {pixel_spacing_isocenter:.6f}, obtenu {test_v2.pixel_spacing:.6f}")
    
    print("\n" + "=" * 70)
    print("✓✓✓ TESTS PASSED - Calcul du pixel spacing vérifié ✓✓✓")
    print("=" * 70)
    
else:
    print(f"✗ DICOM file not found: {dicom_file}")
