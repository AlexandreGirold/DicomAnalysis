"""
MVIC Fente Test - Analysis of black bands in MV images
Measures position (u, v), width between bands, and height of each band
"""
from ...monthly.base_test import BaseTest
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import pydicom
import numpy as np
from scipy import ndimage
from pathlib import Path
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
import base64
from database import SessionLocal, MVCenterConfig

logger = logging.getLogger(__name__)


class MVICFenteTest(BaseTest):
    """
    Test for analyzing black bands (slits) in MVIC images
    
    Measures:
    - Position of black bands (u, v coordinates)
    - Width between 2 black bands (using center of each band)
    - Height of each black band
    """
    
    def __init__(self):
        super().__init__(
            test_name="MVIC Fente",
            description="Analyse des bandes noires dans les images MV - Position, largeur, hauteur"
        )
        # Get MV center from database
        self.center_u, self.center_v = self._get_mv_center_from_db()
        # Detection thresholds
        self.band_detection_percentile = 5  # Pixels below this percentile are considered "dark" (very strict - only darkest pixels)
        self.min_band_height = 10  # Minimum height in pixels for a valid band
        self.min_band_width = 5   # Minimum width in pixels for a valid band
    
    def execute(self, files: List[str], operator: str, test_date: Optional[datetime] = None, notes: str = None):
        """
        Execute MVIC Fente test on one or multiple DICOM images
        
        Args:
            files: List of paths to DICOM files
            operator: Name of the operator
            test_date: Date of the test (defaults to current date)
            notes: Optional notes
        
        Returns:
            dict: Test results with band measurements
        """
        self.set_test_info(operator, test_date)
        
        if notes:
            self.notes = notes
        
        if not files:
            raise ValueError("At least one DICOM file is required")
        
        all_results = []
        visualization_files = []
        
        # Process each file
        for idx, file_path in enumerate(files, 1):
            logger.info(f"[MVIC-FENTE] Processing file {idx}/{len(files)}: {file_path}")
            
            try:
                # Load DICOM
                dcm = pydicom.dcmread(file_path)
                image = dcm.pixel_array.astype(np.float32)
                
                # Get pixel spacing if available
                pixel_spacing = self._get_pixel_spacing(dcm)
                
                # Detect black bands
                bands = self._detect_black_bands(image, pixel_spacing)
                
                if not bands:
                    logger.warning(f"[MVIC-FENTE] No bands detected in {Path(file_path).name}")
                    self.add_result(
                        name=f"image_{idx}_bands",
                        value=0,
                        status="WARNING",
                        unit="bands",
                        tolerance="N/A"
                    )
                    continue
                
                # Generate visualization
                viz_data_url = self._generate_visualization(
                    image, bands, Path(file_path).name, idx, pixel_spacing
                )
                
                if viz_data_url:
                    # Format for frontend display
                    viz_obj = {
                        'name': f'Image {idx}: {Path(file_path).name}',
                        'type': 'image',
                        'data': viz_data_url,
                        'filename': Path(file_path).name,
                        'index': idx,
                        'statistics': {
                            'status': 'COMPLETE',
                            'total_blades': len(bands),
                            'ok_blades': len(bands),
                            'out_of_tolerance': 0,
                            'closed_blades': 0,
                            'pixel_spacing': f"{pixel_spacing:.3f} mm/px" if pixel_spacing else "N/A"
                        }
                    }
                    visualization_files.append(viz_obj)
                
                # Store results for this image
                image_result = {
                    'file': Path(file_path).name,
                    'bands': bands,
                    'num_bands': len(bands),
                    'pixel_spacing_mm': pixel_spacing,
                    'visualization': viz_data_url if viz_data_url else None
                }
                
                all_results.append(image_result)
                
                # Add individual band results
                for band_idx, band in enumerate(bands, 1):
                    self.add_result(
                        name=f"image_{idx}_band_{band_idx}_position",
                        value=f"({band['center_u']:.1f}, {band['center_v']:.1f})",
                        status="INFO",
                        unit="pixels",
                        tolerance="N/A"
                    )
                    
                    self.add_result(
                        name=f"image_{idx}_band_{band_idx}_height",
                        value=band['height_pixels'],
                        status="INFO",
                        unit="pixels" if pixel_spacing is None else "mm",
                        tolerance="N/A"
                    )
                    
                    if 'height_mm' in band:
                        self.add_result(
                            name=f"image_{idx}_band_{band_idx}_height_mm",
                            value=band['height_mm'],
                            status="INFO",
                            unit="mm",
                            tolerance="N/A"
                        )
                
                # Calculate spacing between consecutive bands (aligned edges)
                if len(bands) > 1:
                    for i in range(len(bands) - 1):
                        # Use aligned edge spacing instead of center-to-center
                        spacing_pixels = self._calculate_band_spacing(bands[i], bands[i+1])
                        
                        self.add_result(
                            name=f"image_{idx}_spacing_band_{i+1}_to_{i+2}",
                            value=spacing_pixels,
                            status="INFO",
                            unit="pixels",
                            tolerance="N/A"
                        )
                        
                        if pixel_spacing:
                            spacing_mm = spacing_pixels * pixel_spacing
                            self.add_result(
                                name=f"image_{idx}_spacing_band_{i+1}_to_{i+2}_mm",
                                value=spacing_mm,
                                status="INFO",
                                unit="mm",
                                tolerance="N/A"
                            )
                
                logger.info(f"[MVIC-FENTE] Found {len(bands)} bands in {Path(file_path).name}")
                
            except Exception as e:
                logger.error(f"[MVIC-FENTE] Error processing {file_path}: {e}")
                self.add_result(
                    name=f"image_{idx}_error",
                    value=str(e),
                    status="ERROR",
                    unit="",
                    tolerance="N/A"
                )
        
        # No pass/fail criteria - just informational
        self.overall_result = "COMPLETE"
        
        # Add summary to the result
        result = self.to_dict()
        result['detailed_results'] = all_results
        result['total_images'] = len(files)
        result['total_bands_detected'] = sum(r['num_bands'] for r in all_results)
        result['visualizations'] = visualization_files
        
        return result
    
    def _get_mv_center_from_db(self) -> Tuple[float, float]:
        """Retrieve MV center coordinates from database"""
        try:
            db = SessionLocal()
            config = db.query(MVCenterConfig).first()
            if config:
                logger.info(f"[MVIC-FENTE] MV center from database: u={config.u}, v={config.v}")
                return config.u, config.v
            else:
                # Create default config if not exists
                default_config = MVCenterConfig(u=511.03, v=652.75)
                db.add(default_config)
                db.commit()
                logger.info(f"[MVIC-FENTE] Created default MV center: u=511.03, v=652.75")
                return 511.03, 652.75
        except Exception as e:
            logger.error(f"[MVIC-FENTE] Error retrieving MV center from database: {e}")
            # Fallback to default
            return 511.03, 652.75
        finally:
            if 'db' in locals():
                db.close()
    
    def _get_pixel_spacing(self, dcm) -> Optional[float]:
        """
        Extract pixel spacing from DICOM metadata and correct for isocenter
        Returns spacing in mm/pixel at isocenter or None if not available
        """
        try:
            # Extract geometric parameters for RT images
            if hasattr(dcm, 'ImagePlanePixelSpacing') and hasattr(dcm, 'RadiationMachineSAD') and hasattr(dcm, 'RTImageSID'):
                # Get pixel spacing at detector plane
                spacing = dcm.ImagePlanePixelSpacing
                pixel_spacing_detector = float((spacing[0] + spacing[1]) / 2)
                
                # Get geometric scaling factor
                SAD = float(dcm.RadiationMachineSAD)  # Source to Axis Distance (isocenter)
                SID = float(dcm.RTImageSID)           # Source to Image Distance (detector)
                scaling_factor = SAD / SID
                
                # Calculate pixel spacing at isocenter
                pixel_spacing_isocenter = pixel_spacing_detector * scaling_factor
                
                logger.info(f"[MVIC-FENTE] Pixel spacing: {pixel_spacing_detector:.3f} mm @ detector → {pixel_spacing_isocenter:.3f} mm @ isocenter (SAD/SID = {scaling_factor:.4f})")
                return pixel_spacing_isocenter
            elif hasattr(dcm, 'PixelSpacing'):
                spacing = dcm.PixelSpacing
                return float((spacing[0] + spacing[1]) / 2)
        except Exception as e:
            logger.warning(f"[MVIC-FENTE] Could not extract pixel spacing: {e}")
        return None
    
    def _detect_black_bands(self, image: np.ndarray, pixel_spacing: Optional[float]) -> List[Dict[str, Any]]:
        """
        Detect black bands (slits) in the image
        
        Returns list of bands with:
        - center_u, center_v: Center position
        - width_pixels: Width in pixels
        - height_pixels: Height in pixels
        - bounds: (u_min, u_max, v_min, v_max)
        """
        # Normalize image
        image_norm = (image - image.min()) / (image.max() - image.min())
        
        # Threshold to detect dark regions
        threshold = np.percentile(image_norm, self.band_detection_percentile)
        dark_mask = image_norm < threshold
        
        # Label connected components
        labeled, num_features = ndimage.label(dark_mask)
        
        bands = []
        
        for label_id in range(1, num_features + 1):
            # Get pixels for this component
            component_mask = labeled == label_id
            
            # Find bounds
            v_coords, u_coords = np.where(component_mask)
            
            if len(v_coords) == 0:
                continue
            
            u_min, u_max = u_coords.min(), u_coords.max()
            v_min, v_max = v_coords.min(), v_coords.max()
            
            width = u_max - u_min + 1
            height = v_max - v_min + 1
            
            # Filter out small regions
            if height < self.min_band_height or width < self.min_band_width:
                continue
            
            # Calculate center
            center_u = float(u_coords.mean())
            center_v = float(v_coords.mean())
            
            band = {
                'center_u': round(center_u, 2),
                'center_v': round(center_v, 2),
                'width_pixels': int(width),
                'height_pixels': int(height),
                'bounds': {
                    'u_min': int(u_min),
                    'u_max': int(u_max),
                    'v_min': int(v_min),
                    'v_max': int(v_max)
                }
            }
            
            # Add mm measurements if pixel spacing is available
            if pixel_spacing:
                band['width_mm'] = round(width * pixel_spacing, 2)
                band['height_mm'] = round(height * pixel_spacing, 2)
            
            bands.append(band)
        
        # Sort bands by vertical position (v coordinate)
        bands.sort(key=lambda b: b['center_v'])
        
        return bands
    
    def _calculate_distance(self, u1: float, v1: float, u2: float, v2: float) -> float:
        """Calculate Euclidean distance between two points"""
        return round(np.sqrt((u2 - u1)**2 + (v2 - v1)**2), 2)
    
    def _calculate_band_spacing(self, band1: Dict[str, Any], band2: Dict[str, Any]) -> float:
        """
        Calculate spacing between two bands using aligned edges
        Uses vertical distance between the bottom of band1 and top of band2
        
        Args:
            band1: First band (upper)
            band2: Second band (lower)
        
        Returns:
            Vertical spacing in pixels
        """
        # Get the bottom edge of band1 and top edge of band2
        band1_bottom = band1['bounds']['v_max']
        band2_top = band2['bounds']['v_min']
        
        # Calculate vertical spacing
        spacing = band2_top - band1_bottom
        
        return round(max(0, spacing), 2)  # Ensure non-negative
    
    def _generate_visualization(self, image: np.ndarray, bands: List[Dict[str, Any]], 
                               filename: str, idx: int, pixel_spacing: Optional[float]) -> Optional[str]:
        """
        Generate visualization with detected bands and measurements
        
        Args:
            image: Original image array
            bands: List of detected bands
            filename: Original filename
            idx: Image index
            pixel_spacing: Pixel spacing in mm
        
        Returns:
            Filename of generated visualization or None
        """
        try:
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Display image
            ax.imshow(image, cmap='gray', aspect='auto')
            
            # Draw rectangles around each band
            colors = plt.cm.rainbow(np.linspace(0, 1, len(bands)))
            
            for band_idx, (band, color) in enumerate(zip(bands, colors), 1):
                bounds = band['bounds']
                u_min, u_max = bounds['u_min'], bounds['u_max']
                v_min, v_max = bounds['v_min'], bounds['v_max']
                
                # Draw rectangle
                rect = Rectangle(
                    (u_min, v_min),
                    u_max - u_min,
                    v_max - v_min,
                    linewidth=2,
                    edgecolor=color,
                    facecolor='none',
                    label=f'Band {band_idx}'
                )
                ax.add_patch(rect)
                
                # Draw center point
                ax.plot(band['center_u'], band['center_v'], 'o', 
                       color=color, markersize=8, markeredgewidth=2, 
                       markeredgecolor='white')
                
                # Add text annotation with measurements
                text_x = u_max + 10
                text_y = band['center_v']
                
                if pixel_spacing and 'width_mm' in band:
                    text = (f"Band {band_idx}\n"
                           f"Position: ({band['center_u']:.1f}, {band['center_v']:.1f})\n"
                           f"Size: {band['width_mm']:.1f} × {band['height_mm']:.1f} mm\n"
                           f"({band['width_pixels']} × {band['height_pixels']} px)")
                else:
                    text = (f"Band {band_idx}\n"
                           f"Position: ({band['center_u']:.1f}, {band['center_v']:.1f})\n"
                           f"Size: {band['width_pixels']} × {band['height_pixels']} px")
                
                ax.text(text_x, text_y, text,
                       color='white',
                       fontsize=9,
                       verticalalignment='center',
                       bbox=dict(boxstyle='round', facecolor=color, alpha=0.7, edgecolor='white'))
            
            # Draw spacing lines between consecutive bands (vertical aligned)
            if len(bands) > 1:
                for i in range(len(bands) - 1):
                    # Get edges for spacing calculation
                    band1_bottom = bands[i]['bounds']['v_max']
                    band2_top = bands[i+1]['bounds']['v_min']
                    
                    # Calculate spacing (vertical distance)
                    spacing_px = self._calculate_band_spacing(bands[i], bands[i+1])
                    
                    # Draw vertical line at center U position (average of both bands)
                    mid_u = (bands[i]['center_u'] + bands[i+1]['center_u']) / 2
                    
                    # Draw line from bottom of band1 to top of band2
                    ax.plot([mid_u, mid_u], [band1_bottom, band2_top], 'y-', linewidth=3, alpha=0.8)
                    
                    # Add arrow markers
                    ax.plot(mid_u, band1_bottom, 'yv', markersize=10, alpha=0.8)  # Down arrow
                    ax.plot(mid_u, band2_top, 'y^', markersize=10, alpha=0.8)  # Up arrow
                    
                    # Calculate middle position for text
                    mid_v = (band1_bottom + band2_top) / 2
                    
                    if pixel_spacing:
                        spacing_mm = spacing_px * pixel_spacing
                        spacing_text = f"Spacing:\n{spacing_mm:.1f} mm\n({spacing_px:.1f} px)"
                    else:
                        spacing_text = f"Spacing:\n{spacing_px:.1f} px"
                    
                    ax.text(mid_u + 20, mid_v, spacing_text,
                           color='yellow',
                           fontsize=10,
                           fontweight='bold',
                           verticalalignment='center',
                           horizontalalignment='left',
                           bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
            
            # Title and labels
            title = f"MVIC Fente - {filename}\n{len(bands)} band(s) detected"
            if pixel_spacing:
                title += f" | Pixel spacing: {pixel_spacing:.3f} mm/px"
            ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
            ax.set_xlabel('U (pixels)', fontsize=10)
            ax.set_ylabel('V (pixels)', fontsize=10)
            
            # Add legend
            if bands:
                ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
            
            # Grid
            ax.grid(True, alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            
            # Save to bytes buffer and encode as base64
            from io import BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            
            # Encode to base64
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            img_data_url = f"data:image/png;base64,{img_base64}"
            
            plt.close()
            buffer.close()
            
            logger.info(f"[MVIC-FENTE] Generated visualization for {filename}")
            return img_data_url
            
        except Exception as e:
            logger.error(f"[MVIC-FENTE] Error generating visualization: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_form_data(self):
        """
        Get the form structure for frontend implementation
        
        Returns:
            dict: Form configuration
        """
        return {
            'title': 'MVIC Fente - Analyse des bandes noires',
            'description': 'Mesure la position, largeur entre bandes, et hauteur de chaque bande noire',
            'file_upload': True,
            'fields': [
                {
                    'name': 'test_date',
                    'label': 'Date:',
                    'type': 'date',
                    'required': True,
                    'default': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'name': 'operator',
                    'label': 'Opérateur:',
                    'type': 'text',
                    'required': True,
                    'placeholder': 'Nom de l\'opérateur'
                },
                {
                    'name': 'dicom_files',
                    'label': 'Images DICOM:',
                    'type': 'file',
                    'required': True,
                    'accept': '.dcm',
                    'multiple': True,
                    'description': 'Sélectionner une ou plusieurs images DICOM à analyser'
                },
                {
                    'name': 'notes',
                    'label': 'Notes (optionnel):',
                    'type': 'textarea',
                    'required': False,
                    'placeholder': 'Commentaires ou observations',
                    'rows': 3
                }
            ],
            'tolerance': 'Pas de critères PASS/FAIL - Test informatif uniquement'
        }


# Convenience function for standalone use
def test_mvic_fente(files: List[str], operator: str, test_date: Optional[datetime] = None, notes: str = None):
    """
    Standalone function to test MVIC fente
    
    Args:
        files: List of DICOM file paths
        operator: Name of the operator
        test_date: Date of the test (defaults to current date)
        notes: Optional notes
    
    Returns:
        dict: Test results
    """
    test = MVICFenteTest()
    return test.execute(files, operator, test_date, notes)
