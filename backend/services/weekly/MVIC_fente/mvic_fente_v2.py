"""
MVIC Fente V2 Test - Analysis of MLC slits in MV images
Based on ImageJ macro - Measures slit width and spacing between slits
Supports multiple DICOM files with visualization
"""
from ...monthly.base_test import BaseTest
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import pydicom
import numpy as np
from scipy import ndimage, signal
from pathlib import Path
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import base64
from io import BytesIO
import sys
import os
# Add backend root to path for mv_center_utils import
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_root)

from mv_center_utils import get_mv_center

logger = logging.getLogger(__name__)


class MVICFenteTest(BaseTest):
    """
    Test for analyzing MLC slits (fentes) in MVIC images
    
    Measures:
    - Slit width for each detected slit
    - Spacing between consecutive slits
    
    NO PASS/FAIL criteria - informational test only
    """
    
    def __init__(self):
        super().__init__(
            test_name="MVIC Fente",
            description="Analyse des fentes MLC - Largeur et espacement entre fentes"
        )
        # MV center coordinates (retrieved from database)
        self.center_u, self.center_v = get_mv_center()
        
        # Detection parameters
        self.pixel_size_mm = 0.216  # mm/pixel (default, will be updated from DICOM)
        self.blade_width_pixels = 29  # Approximate width of one blade in pixels
        self.min_spacing_pixels = 24  # Minimum 5mm spacing between opposing blades
        self.analysis_height_pixels = 220  # Analyze ±220 pixels around center
        
        # Scan range
        self.u_start = 48
        self.u_end = 970
        self.v_scan_range = 220  # ±220 pixels from center
        self.profile_width = 30  # Pixels to average for profile
        self.min_edge_separation = 24  # Minimum 5mm spacing (24 pixels)
        self.pixel_spacing = 0.216  # mm/pixel (default, will be updated from DICOM)
    
    def execute(self, files: List[str], operator: str, test_date: Optional[datetime] = None, notes: str = None):
        """
        Execute MVIC Fente V2 test on DICOM images
        
        Args:
            files: List of paths to DICOM files
            operator: Name of the operator
            test_date: Date of the test
            notes: Optional notes
        
        Returns:
            dict: Test results with slit measurements
        """
        self.set_test_info(operator, test_date)
        
        # Store filenames for database
        self.dicom_files = files
        
        # Initialize file_results for image-to-result mapping
        self.file_results = []
        
        if notes:
            self.notes = notes
        
        if not files:
            raise ValueError("At least one DICOM file is required")
        
        all_results = []
        visualization_files = []
        
        for idx, file_path in enumerate(files, 1):
            logger.info(f"[MVIC-FENTE-V2] Processing file {idx}/{len(files)}: {file_path}")
            
            try:
                # Load DICOM
                dcm = pydicom.dcmread(file_path)
                image = dcm.pixel_array.astype(np.float32)
                logger.info(f"[MVIC-FENTE-V2] Loaded image shape: {image.shape}")
                
                # Calculate pixel spacing at isocenter from DICOM metadata
                self._update_pixel_spacing_from_dicom(dcm)
                
                # Invert image (like ImageJ)
                image = image.max() - image
                
                # Detect slits using edge detection
                slits_data = self._detect_slits_v2(image)
                logger.info(f"[MVIC-FENTE-V2] Detection complete: {slits_data['num_slits']} slits found")
                
                if not slits_data['slits']:
                    logger.warning(f"[MVIC-FENTE-V2] No slits detected in {Path(file_path).name}")
                    # Still generate visualization for no-slit case
                    viz_data_url = self._generate_visualization_v2(
                        image, slits_data, Path(file_path).name, idx
                    )
                    if viz_data_url:
                        viz_obj = {
                            'name': f'Image {idx}: {Path(file_path).name}',
                            'type': 'image',
                            'data': viz_data_url,
                            'filename': Path(file_path).name,
                            'index': idx,
                            'statistics': {
                                'status': 'COMPLETE',
                                'total_blades': 0,
                                'ok_blades': 0,
                                'out_of_tolerance': 0,
                                'closed_blades': 0
                            }
                        }
                        visualization_files.append(viz_obj)
                    
                    # Get acquisition datetime for file_results
                    acquisition_date = None
                    if hasattr(dcm, 'AcquisitionDate') and hasattr(dcm, 'AcquisitionTime'):
                        try:
                            date_str = str(dcm.AcquisitionDate)
                            time_str = str(dcm.AcquisitionTime).split('.')[0]
                            acquisition_date = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S").strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            acquisition_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Add to file_results for image-to-result mapping
                    self.file_results.append({
                        'filename': Path(file_path).name,
                        'filepath': file_path,
                        'image_number': idx,
                        'acquisition_date': acquisition_date,
                        'analysis_type': 'MLC Slit Analysis (Edge Detection)',
                        'num_slits': 0,
                        'slits': [],
                        'pixel_spacing': getattr(self, 'pixel_spacing', None),
                        'status': 'WARNING'
                    })
                    
                    # Add empty result for this image
                    image_result = {
                        'file': Path(file_path).name,
                        'num_slits': 0,
                        'slits': [],
                        'visualization': viz_data_url
                    }
                    all_results.append(image_result)
                    continue
                
                # Generate visualization
                viz_data_url = self._generate_visualization_v2(
                    image, slits_data, Path(file_path).name, idx
                )
                logger.info(f"[MVIC-FENTE-V2] Visualization generated: {bool(viz_data_url)}")
                
                if viz_data_url:
                    viz_obj = {
                        'name': f'Image {idx}: {Path(file_path).name}',
                        'type': 'image',
                        'data': viz_data_url,
                        'filename': Path(file_path).name,
                        'index': idx,
                        'statistics': {
                            'status': 'COMPLETE',
                            'total_blades': slits_data['num_slits'],
                            'ok_blades': slits_data['num_slits'],
                            'out_of_tolerance': 0,
                            'closed_blades': 0
                        }
                    }
                    visualization_files.append(viz_obj)
                    logger.info(f"[MVIC-FENTE-V2] Added visualization {idx} to list. Total: {len(visualization_files)}")
                
                # Get acquisition datetime for file_results
                acquisition_date = None
                if hasattr(dcm, 'AcquisitionDate') and hasattr(dcm, 'AcquisitionTime'):
                    try:
                        date_str = str(dcm.AcquisitionDate)
                        time_str = str(dcm.AcquisitionTime).split('.')[0]
                        acquisition_date = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S").strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        acquisition_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Add to file_results for image-to-result mapping
                self.file_results.append({
                    'filename': Path(file_path).name,
                    'filepath': file_path,
                    'image_number': idx,
                    'acquisition_date': acquisition_date,
                    'analysis_type': 'MLC Slit Analysis (Edge Detection)',
                    'num_slits': slits_data['num_slits'],
                    'slits': slits_data['slits'],
                    'pixel_spacing': getattr(self, 'pixel_spacing', None),
                    'status': 'PASS'
                })
                
                # Store results
                image_result = {
                    'file': Path(file_path).name,
                    'num_slits': slits_data['num_slits'],
                    'slits': slits_data['slits'],
                    'visualization': viz_data_url
                }
                all_results.append(image_result)
                
                # Add results for each slit
                for slit_idx, slit in enumerate(slits_data['slits'], 1):
                    self.add_result(
                        name=f"image_{idx}_slit_{slit_idx}_position",
                        value=f"({slit['center_u']:.1f}, {slit['center_v']:.1f})",
                        status="INFO",
                        unit="pixels",
                        tolerance="N/A"
                    )
                    
                    self.add_result(
                        name=f"image_{idx}_slit_{slit_idx}_width",
                        value=slit['width_mm'],
                        status="INFO",
                        unit="mm",
                        tolerance="N/A"
                    )
                
                logger.info(f"[MVIC-FENTE-V2] Found {slits_data['num_slits']} slits")
                
            except Exception as e:
                logger.error(f"[MVIC-FENTE-V2] Error processing {file_path}: {e}")
                import traceback
                traceback.print_exc()
        
        # Overall result
        self.overall_result = "COMPLETE"
        
        result = self.to_dict()
        result['detailed_results'] = all_results
        result['total_images'] = len(files)
        result['visualizations'] = visualization_files
        
        logger.info(f"[MVIC-FENTE-V2] Test complete. Total visualizations: {len(visualization_files)}")
        logger.info(f"[MVIC-FENTE-V2] Total detailed results: {len(all_results)}")
        
        return result
    
    def _update_pixel_spacing_from_dicom(self, dcm) -> None:
        """Calculate pixel spacing at isocenter from DICOM metadata"""
        try:
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
                
                # Update instance variables
                self.pixel_spacing = pixel_spacing_isocenter
                self.pixel_size_mm = pixel_spacing_isocenter
                
                logger.info(f"[MVIC-FENTE-V2] Pixel spacing: {pixel_spacing_detector:.3f} mm @ detector → {pixel_spacing_isocenter:.3f} mm @ isocenter (SAD={SAD:.1f}, SID={SID:.1f})")
            else:
                # Fallback to default value
                logger.warning("[MVIC-FENTE-V2] Missing DICOM tags for pixel spacing calculation, using default 0.216 mm")
                self.pixel_spacing = 0.216
                self.pixel_size_mm = 0.216
        except Exception as e:
            logger.error(f"[MVIC-FENTE-V2] Error calculating pixel spacing: {e}")
            self.pixel_spacing = 0.216
            self.pixel_size_mm = 0.216
    
    def _detect_slits_v2(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect slits using edge detection and local maxima approach
        Similar to ImageJ macro logic
        """
        # Apply edge detection (Find Edges in ImageJ)
        edges = self._find_edges(image)
        
        # Define scan area
        v_min = int(self.center_v - self.v_scan_range)
        v_max = int(self.center_v + self.v_scan_range)
        
        all_edges = []
        
        # Scan horizontally at blade intervals
        blade_pair = 25  # Starting blade pair number
        for u in range(self.u_start, self.u_end, self.blade_width_pixels):
            # Extract vertical profile (averaged over profile_width)
            u_end_profile = min(u + self.profile_width, edges.shape[1])
            profile = edges[v_min:v_max, u:u_end_profile].mean(axis=1)
            
            # Find local maxima in the profile
            median_val = np.median(profile)
            edge_positions = self._find_local_maxima(profile, median_val, v_min)
            
            # Store edge positions with their u coordinate
            for v_pos in edge_positions:
                all_edges.append({
                    'u': u,
                    'v': v_pos,
                    'blade_pair': blade_pair
                })
            
            blade_pair += 1
        
        # Group edges into slits (pairs of edges)
        slits = self._group_edges_into_slits(all_edges)
        
        # Ignore the first slit (it's height only reference)
        if len(slits) > 0:
            slits = slits[1:]
        
        # No spacing calculation - slits are touching each other
        spacings = []
        avg_spacing_mm = None
        
        return {
            'slits': slits,
            'num_slits': len(slits),
            'spacings': spacings,
            'avg_spacing_mm': avg_spacing_mm
        }
    
    def _find_edges(self, image: np.ndarray) -> np.ndarray:
        """Apply edge detection (similar to ImageJ Find Edges)"""
        # Sobel operator for edge detection
        edges_x = ndimage.sobel(image, axis=1)
        edges_y = ndimage.sobel(image, axis=0)
        edges = np.hypot(edges_x, edges_y)
        return edges
    
    def _find_local_maxima(self, profile: np.ndarray, threshold: float, v_offset: int) -> List[int]:
        """
        Find local maxima in profile that are above threshold
        With minimum separation constraint
        """
        maxima_positions = []
        prev_value = 0
        stop_max = 0
        
        for i, value in enumerate(profile):
            # Case 1: Value increasing (max not reached)
            if value > prev_value and value > threshold:
                stop_max = 2
            
            # Case 2: Value decreasing (local max reached)
            if value < prev_value and value > threshold and stop_max > 1:
                v_pos = i - 1 + v_offset
                
                # Check minimum separation from previous maximum
                if len(maxima_positions) > 0:
                    delta = v_pos - maxima_positions[-1]
                    if delta > self.min_edge_separation:
                        maxima_positions.append(v_pos)
                        stop_max = 1
                    elif value > profile[maxima_positions[-1] - v_offset]:
                        # Replace previous max if this one is higher
                        maxima_positions[-1] = v_pos
                        stop_max = 1
                else:
                    maxima_positions.append(v_pos)
                    stop_max = 1
            
            prev_value = value
        
        return maxima_positions
    
    def _group_edges_into_slits(self, edges: List[Dict]) -> List[Dict]:
        """
        Group detected edges into slits (pairs of edges forming a slit)
        """
        # Sort edges by v position
        edges_sorted = sorted(edges, key=lambda e: e['v'])
        
        slits = []
        i = 0
        while i < len(edges_sorted) - 1:
            edge1 = edges_sorted[i]
            edge2 = edges_sorted[i + 1]
            
            # Check if these two edges form a slit
            width_px = edge2['v'] - edge1['v']
            
            # Slits should be reasonably sized
            if 10 < width_px < 200:  # Between ~2mm and ~40mm
                slit = {
                    'top_edge': edge1,
                    'bottom_edge': edge2,
                    'center_u': (edge1['u'] + edge2['u']) / 2,
                    'center_v': (edge1['v'] + edge2['v']) / 2,
                    'width_px': width_px,
                    'width_mm': round(width_px * self.pixel_spacing, 2)
                }
                slits.append(slit)
                i += 2  # Skip both edges
            else:
                i += 1
        
        return slits
    
    def _generate_visualization_v2(self, image: np.ndarray, slits_data: Dict, 
                                   filename: str, idx: int) -> Optional[str]:
        """Generate visualization with detected slits"""
        try:
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Display inverted image
            ax.imshow(image, cmap='gray', aspect='auto')
            
            slits = slits_data['slits']
            colors = plt.cm.rainbow(np.linspace(0, 1, len(slits)))
            
            # Draw each slit
            for slit_idx, (slit, color) in enumerate(zip(slits, colors), 1):
                top = slit['top_edge']
                bottom = slit['bottom_edge']
                
                # Draw horizontal lines for edges
                u_min = min(top['u'], bottom['u']) - 15
                u_max = max(top['u'], bottom['u']) + 15
                
                ax.plot([u_min, u_max], [top['v'], top['v']], 
                       color=color, linewidth=2, label=f'Slit {slit_idx}')
                ax.plot([u_min, u_max], [bottom['v'], bottom['v']], 
                       color=color, linewidth=2)
                
                # Draw vertical line connecting edges
                ax.plot([slit['center_u'], slit['center_u']], 
                       [top['v'], bottom['v']], 
                       color=color, linewidth=2, linestyle='--')
                
                # Add text annotation
                text = f"Slit {slit_idx}\nWidth: {slit['width_mm']:.2f} mm"
                ax.text(u_max + 10, slit['center_v'], text,
                       color='white', fontsize=9, verticalalignment='center',
                       bbox=dict(boxstyle='round', facecolor=color, alpha=0.7))
            
            # Title
            title = f"MVIC Fente V2 - {filename}\n{len(slits)} slit(s) detected"
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel('U (pixels)', fontsize=10)
            ax.set_ylabel('V (pixels)', fontsize=10)
            ax.legend(loc='upper right', fontsize=8)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            buffer.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"[MVIC-FENTE-V2] Error generating visualization: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_to_database(self, filenames: Optional[List[str]] = None):
        """
        Save MVIC Fente V2 test results to database
        
        Args:
            filenames: Optional list of source DICOM filenames
        
        Returns:
            int: Test ID from database
        """
        try:
            from database_helpers import save_mvic_fente_v2_to_database
            
            # Get detailed results from the test
            detailed_results = []
            if hasattr(self, 'results'):
                # Parse results to extract slit data per image
                for idx, result_key in enumerate(sorted(self.results.keys()), 1):
                    result_data = self.results[result_key]
                    if isinstance(result_data, dict) and 'value' in result_data:
                        # This is a summary result with slit info
                        image_result = {
                            'slits': []
                        }
                        # Extract slit data from result value
                        value = result_data.get('value', '')
                        if 'slits' in value.lower():
                            # Try to parse slit count
                            try:
                                num_slits = int(value.split()[0])
                                # Create placeholder slit entries
                                for slit_num in range(1, num_slits + 1):
                                    image_result['slits'].append({
                                        'width_mm': 0,  # Would need actual data
                                        'height_pixels': 0,
                                        'center_u': None,
                                        'center_v': None
                                    })
                            except:
                                pass
                        detailed_results.append(image_result)
            
            test_id = save_mvic_fente_v2_to_database(
                operator=self.operator,
                test_date=self.test_date,
                overall_result=self.overall_result,
                results=detailed_results,
                notes=self.notes,
                filenames=filenames
            )
            
            self.test_id = test_id
            return test_id
            
        except Exception as e:
            logger.error(f"Error saving MVIC Fente V2 test to database: {e}")
            raise
    
    def to_dict(self):
        """Override to_dict to include filenames and file_results"""
        result = super().to_dict()
        
        # Add filenames at top level for easy database storage
        if hasattr(self, 'dicom_files') and self.dicom_files:
            result['filenames'] = [os.path.basename(f) for f in self.dicom_files]
        
        # Add file_results for image-to-result mapping
        if hasattr(self, 'file_results') and self.file_results:
            result['file_results'] = self.file_results
        
        return result
    
    def get_form_data(self):
        """Get form structure for frontend"""
        return {
            'title': 'MVIC Fente V2 - Détection par contours',
            'description': 'Analyse des fentes par détection de maxima locaux (méthode ImageJ) - Largeur de chaque fente',
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
                    'description': 'Sélectionner une ou plusieurs images DICOM'
                },
                {
                    'name': 'notes',
                    'label': 'Notes (optionnel):',
                    'type': 'textarea',
                    'required': False,
                    'placeholder': 'Commentaires',
                    'rows': 3
                }
            ],
            'tolerance': 'Test informatif - Basé sur la méthode ImageJ'
        }


def test_mvic_fente_v2(files: List[str], operator: str, test_date: Optional[datetime] = None, notes: str = None):
    """Standalone function for MVIC Fente"""
    test = MVICFenteTest()
    return test.execute(files, operator, test_date, notes)
