"""
MVIC (MV Imaging Check) - Test hebdomadaire
Validation de la taille et de la forme du champ de radiation

Ce test vérifie:
1. Taille du champ: doit correspondre à 150x80, 85x85, ou 50x50 mm (tolérance ±1mm)
2. Forme du champ: tous les angles doivent être à 90° (tolérance ±1°)
"""
import sys
import os
import cv2
import numpy as np
import pydicom
import logging
import base64
from io import BytesIO

# Setup logging
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
services_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if services_dir not in sys.path:
    sys.path.insert(0, services_dir)

from basic_tests.base_test import BaseTest
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# Import the validation classes
from .taille_champ import FieldSizeValidator
from .forme_champ import FieldShapeValidator


class MVICChampTest(BaseTest):
    """
    Test MVIC-Champ - Validation de la taille et de la forme du champ de radiation
    Traite 5 images DICOM et extrait automatiquement les informations
    """
    
    def __init__(self):
        super().__init__(
            test_name="MVIC-Champ - MV Imaging Check",
            description="Validation de la taille et de la forme du champ de radiation (5 images, taille ±1mm, angles 90° ±1°)"
        )
        self.size_validator = FieldSizeValidator()
        self.shape_validator = FieldShapeValidator()
        self.visualizations = []  # Store visualization paths
    
    def _get_dicom_datetime(self, ds):
        """Extraire la date et l'heure d'acquisition du DICOM"""
        try:
            # Try AcquisitionDate + AcquisitionTime
            if hasattr(ds, 'AcquisitionDate') and hasattr(ds, 'AcquisitionTime'):
                date_str = str(ds.AcquisitionDate)
                time_str = str(ds.AcquisitionTime).split('.')[0]  # Remove microseconds
                datetime_str = date_str + time_str
                return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
            
            # Try ContentDate + ContentTime
            if hasattr(ds, 'ContentDate') and hasattr(ds, 'ContentTime'):
                date_str = str(ds.ContentDate)
                time_str = str(ds.ContentTime).split('.')[0]
                datetime_str = date_str + time_str
                return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
            
            # Try StudyDate + StudyTime
            if hasattr(ds, 'StudyDate') and hasattr(ds, 'StudyTime'):
                date_str = str(ds.StudyDate)
                time_str = str(ds.StudyTime).split('.')[0]
                datetime_str = date_str + time_str
                return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
                
        except Exception as e:
            logger.warning(f"Could not parse DICOM datetime: {e}")
        
        return None
    
    def _read_dicom_header(self, filepath):
        """Lire uniquement l'en-tête DICOM"""
        try:
            return pydicom.dcmread(filepath, stop_before_pixels=True)
        except Exception as e:
            logger.error(f"Error reading DICOM header from {filepath}: {e}")
            return None
    
    def _generate_visualization_with_dimensions(self, filepath, dimensions, size_validation, image_index):
        """Generate visualization with side lengths and convert to base64"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Load and preprocess image
            image_array, ds, metadata = self.shape_validator.load_dicom_image(filepath)
            if image_array is None:
                return None
            
            img_8bit, clahe_img, laplacian_sharpened = self.shape_validator.preprocess_image(image_array)
            
            # Detect contours and edges
            contours, binary_image = self.shape_validator.detect_field_contours(clahe_img)
            merged_contours = self.shape_validator.merge_nearby_contours(contours, binary_image)
            final_contours = [c for c in merged_contours if cv2.contourArea(c) > self.shape_validator.min_area]
            field_contour = self.shape_validator.get_merged_contour(final_contours)
            
            if field_contour is None:
                return None
            
            angle_data = self.shape_validator.calculate_corner_angles(field_contour)
            
            if not angle_data:
                return None
            
            validation = self.shape_validator.validate_angles(angle_data)
            
            # Create visualization with dimensions (2 panels only)
            fig, axes = plt.subplots(1, 2, figsize=(16, 6))
            
            # Panel 1: Detected Field with annotations
            contour_img = clahe_img.copy()
            contour_img = cv2.cvtColor(contour_img, cv2.COLOR_GRAY2RGB)
            cv2.drawContours(contour_img, [field_contour], -1, (0, 255, 0), 2)
            
            if angle_data and 'approx_polygon' in angle_data:
                # Convert back to numpy array if it was serialized to list
                approx_poly = angle_data['approx_polygon']
                if isinstance(approx_poly, list):
                    approx_poly = np.array(approx_poly, dtype=np.int32)
                cv2.drawContours(contour_img, [approx_poly], -1, (255, 255, 0), 2)
            
            axes[0].imshow(contour_img)
            
            # Mark corners with angles
            corners = []
            if angle_data and 'angles' in angle_data:
                # Calculate field center from contour
                M = cv2.moments(field_contour)
                if M['m00'] != 0:
                    field_center_x = M['m10'] / M['m00']
                    field_center_y = M['m01'] / M['m00']
                else:
                    # Fallback to bounding box center
                    x, y, w, h = cv2.boundingRect(field_contour)
                    field_center_x = x + w / 2
                    field_center_y = y + h / 2
                
                for angle_info in angle_data['angles']:
                    corner = angle_info['corner']
                    angle = angle_info['angle']
                    is_valid = angle_info['is_valid']
                    corners.append(corner)
                    
                    color = 'lime' if is_valid else 'red'
                    axes[0].plot(corner[0], corner[1], 'o', color=color, markersize=12)
                    
                    offset = 20
                    # Position based on corner location relative to field center
                    if corner[0] < field_center_x:
                        # Left side - place label to the left
                        text_x = corner[0] - offset
                        ha = 'right'
                    else:
                        # Right side - place label to the right
                        text_x = corner[0] + offset
                        ha = 'left'
                    
                    # Adjust vertical position based on corner location
                    if corner[1] < field_center_y:
                        # Top - place above
                        text_y = corner[1] - offset
                    else:
                        # Bottom - place below
                        text_y = corner[1] + offset
                    
                    axes[0].text(text_x, text_y, 
                                   f'{angle:.2f}°',
                                   color=color, fontsize=8, fontweight='bold',
                                   ha=ha, va='center',
                                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8))
                
                # Add side lengths
                if dimensions and len(corners) >= 4:
                    detected_width = dimensions.get('width_mm', 0)
                    detected_height = dimensions.get('height_mm', 0)
                    
                    # Get expected dimensions - need to find closest match if validation failed
                    if size_validation and 'expected_width' in size_validation:
                        expected_width = size_validation.get('expected_width', 0)
                        expected_height = size_validation.get('expected_height', 0)
                    else:
                        # Find closest expected size from the validator
                        expected_sizes = [
                            {'width': 150, 'height': 85},
                            {'width': 85, 'height': 85},
                            {'width': 50, 'height': 50}
                        ]
                        # Find closest match (try both orientations)
                        min_error = float('inf')
                        expected_width = 0
                        expected_height = 0
                        for size in expected_sizes:
                            error1 = abs(size['width'] - detected_width) + abs(size['height'] - detected_height)
                            error2 = abs(size['height'] - detected_width) + abs(size['width'] - detected_height)
                            if error1 < min_error:
                                min_error = error1
                                expected_width = size['width']
                                expected_height = size['height']
                            if error2 < min_error:
                                min_error = error2
                                expected_width = size['height']
                                expected_height = size['width']
                    
                    # Calculate errors
                    width_error = abs(detected_width - expected_width) if expected_width > 0 else 0
                    height_error = abs(detected_height - expected_height) if expected_height > 0 else 0
                    
                    for i in range(len(corners)):
                        p1 = corners[i]
                        p2 = corners[(i + 1) % len(corners)]
                        
                        mid_x = (p1[0] + p2[0]) / 2
                        mid_y = (p1[1] + p2[1]) / 2
                        
                        # Calculate pixel deltas
                        dx = abs(p2[0] - p1[0])
                        dy = abs(p2[1] - p1[1])
                        
                        # Determine if side is more horizontal or vertical
                        # Horizontal side (larger dx) = width dimension
                        # Vertical side (larger dy) = height dimension
                        if dx > dy:
                            # Horizontal side - this is the width
                            mm_dist = detected_width
                            error = width_error
                        else:
                            # Vertical side - this is the height
                            mm_dist = detected_height
                            error = height_error
                        
                        # Color: red if error > 1mm, cyan if within tolerance
                        text_color = 'red' if error > 1.0 else 'cyan'
                        
                        axes[0].text(mid_x, mid_y, 
                                       f'{mm_dist:.2f}mm',
                                       color=text_color, fontsize=9, fontweight='bold',
                                       ha='center', va='center',
                                       bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.9))
            
            axes[0].set_title('Field with Angles & Side Lengths', fontweight='bold', fontsize=14)
            axes[0].axis('off')
            
            # Panel 2: Summary
            axes[1].axis('off')
            # Overall status: PASS only if both size and shape are valid
            overall_valid = validation['is_valid'] and (size_validation and size_validation.get('is_valid', False))
            status_symbol = '✅' if overall_valid else '❌'
            status_text = 'PASS' if overall_valid else 'FAIL'
            
            # Get acquisition date from metadata
            acquisition_date = metadata.get('acquisition_date', 'Unknown')
            
            summary_lines = [
                f"IMAGE {image_index}",
                f"Date: {acquisition_date}",
                f"",
                f"Status: {status_symbol} {status_text}",
                f"",
                f"FIELD SIZE:",
            ]
            
            if dimensions:
                summary_lines.append(f"  Width:  {dimensions['width_mm']:.2f} mm")
                summary_lines.append(f"  Height: {dimensions['height_mm']:.2f} mm")
            
            summary_lines.extend([
                f"",
                f"CORNER ANGLES:",
                f"  Expected: 90° ± 1°",
                f"  Total Corners: {len(validation['angles'])}",
                f""
            ])
            
            if validation['angles']:
                for i, angle_info in enumerate(validation['angles'], 1):
                    status = '✅' if angle_info['is_valid'] else '❌'
                    summary_lines.append(
                        f"  {status} Corner {i}: {angle_info['angle']:.2f}° (Δ{angle_info['error']:.2f}°)"
                    )
            
            summary_text = '\n'.join(summary_lines)
            axes[1].text(0.05, 0.95, summary_text, transform=axes[1].transAxes,
                           fontsize=11, verticalalignment='top', fontfamily='monospace')
            axes[1].set_title('Summary', fontweight='bold', fontsize=14)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            
            # Close figure and clear buffer to free memory
            plt.close(fig)
            buffer.close()
            
            return f'data:image/png;base64,{image_base64}'
            
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def execute(self, files: List[str], operator: str, 
                test_date: Optional[datetime] = None, notes: Optional[str] = None):
        """
        Exécuter le test MVIC sur 5 fichiers DICOM
        
        Args:
            files: Liste de 5 fichiers DICOM
            operator: Nom de l'opérateur
            test_date: Date du test (par défaut: maintenant)
            notes: Notes additionnelles
        
        Returns:
            dict: Résultats du test
        """
        self.set_test_info(operator, test_date)
        
        # Initialize file_results array to link each file to its analysis
        self.file_results = []
        
        # Validation du nombre de fichiers
        if len(files) != 5:
            raise ValueError(f"Le test MVIC nécessite exactement 5 images DICOM. Reçu: {len(files)}")
        
        # Ajouter les paramètres d'entrée
        self.add_input("operator", operator, "text")
        self.add_input("nombre_images", len(files), "count")
        if notes:
            self.add_input("notes", notes, "text")
        
        # Trier les fichiers par date d'acquisition
        logger.info("Sorting files by acquisition datetime...")
        files_with_datetime = []
        for filepath in files:
            ds = self._read_dicom_header(filepath)
            if ds:
                dt = self._get_dicom_datetime(ds)
                if dt:
                    files_with_datetime.append((filepath, dt))
                else:
                    # Fallback to file modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    files_with_datetime.append((filepath, mod_time))
                    logger.warning(f"Using file modification time for {os.path.basename(filepath)}")
            else:
                raise ValueError(f"Impossible de lire l'en-tête DICOM: {filepath}")
        
        # Sort by datetime
        files_with_datetime.sort(key=lambda x: x[1])
        
        # Store filenames for database
        self.dicom_files = [f[0] for f in files_with_datetime]
        
        # Log chronological order
        logger.info("Ordre chronologique des fichiers:")
        for i, (filepath, dt) in enumerate(files_with_datetime, 1):
            logger.info(f"  {i}. {os.path.basename(filepath)} - {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Store database info for each image
        image_db_data = []
        
        # Traiter chaque fichier
        for i, (filepath, acquisition_date) in enumerate(files_with_datetime, 1):
            filename = os.path.basename(filepath)
            
            try:
                # Add image info result (like MLC does)
                self.add_result(
                    name=f"Image {i}: {filename}",
                    value=f"Acquisition: {acquisition_date.strftime('%Y-%m-%d %H:%M:%S')}",
                    status="INFO",
                    details="Analysis Type: Field Size and Shape Validation"
                )
                
                # ========== VALIDATION DE LA TAILLE ==========
                size_result = self.size_validator.process_image(filepath)
                
                dimensions = None
                size_validation = None
                if size_result and size_result['dimensions']:
                    dimensions = size_result['dimensions']
                    size_validation = size_result['validation']
                
                # ========== VALIDATION DE LA FORME ==========
                # Generate visualization with dimensions from size validation
                # Note: Visualization is generated as base64 (no physical file created)
                logger.info(f"Generating visualization for image {i}: {filename}")
                viz_base64 = self._generate_visualization_with_dimensions(
                    filepath, 
                    dimensions,
                    size_validation,
                    i
                )
                logger.info(f"Visualization generated: {bool(viz_base64)}, length: {len(viz_base64) if viz_base64 else 0}")
                
                # Process without saving PNG files (visualization is generated as base64)
                shape_result = self.shape_validator.process_image(filepath, save_visualization=False)
                
                angle_validation = None
                angle_data = None
                if shape_result and shape_result['validation']:
                    angle_validation = shape_result['validation']
                    angle_data = shape_result['angle_data']
                
                # Always add visualization if it was generated (even without angle validation)
                if viz_base64:
                    viz_stats = {
                        'status': 'PASS' if (angle_validation and angle_validation['is_valid'] and 
                                           size_validation and size_validation['is_valid']) else 'FAIL',
                        'field_size': f"{dimensions['width_mm']:.2f}x{dimensions['height_mm']:.2f}mm" if dimensions else 'N/A'
                    }
                    
                    # Add angle stats if available
                    if angle_validation and 'angles' in angle_validation:
                        viz_stats['angles_valid'] = f"{len([a for a in angle_validation['angles'] if a['is_valid']])}/{len(angle_validation['angles'])}"
                    
                    self.visualizations.append({
                        'name': f'Image {i}: {filename}',
                        'type': 'image',
                        'data': viz_base64,
                        'filename': filename,
                        'index': int(i),
                        'acquisition_date': acquisition_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'statistics': viz_stats
                    })
                    logger.info(f"Added visualization for image {i}")
                else:
                    logger.warning(f"No visualization generated for image {i}: {filename}")
                
                # Collect data for database
                if dimensions and angle_data and 'angles' in angle_data:
                    angles_list = [a['angle'] for a in angle_data['angles']]
                    
                    # Extract individual corner angles
                    # Angles are ordered: top-left, top-right, bottom-left, bottom-right
                    corner_angles = {
                        'top_left_angle': float(angles_list[0]) if len(angles_list) > 0 else 90.0,
                        'top_right_angle': float(angles_list[1]) if len(angles_list) > 1 else 90.0,
                        'bottom_left_angle': float(angles_list[2]) if len(angles_list) > 2 else 90.0,
                        'bottom_right_angle': float(angles_list[3]) if len(angles_list) > 3 else 90.0
                    }
                    
                    # Calculate average and std dev from corner angles
                    corner_angles_list = [corner_angles['top_left_angle'], corner_angles['top_right_angle'], 
                                         corner_angles['bottom_left_angle'], corner_angles['bottom_right_angle']]
                    avg_angle = float(np.mean(corner_angles_list))
                    std_angle = float(np.std(corner_angles_list))
                    
                    image_data = {
                        'width_mm': float(dimensions['width_mm']) if dimensions['width_mm'] is not None else None,
                        'height_mm': float(dimensions['height_mm']) if dimensions['height_mm'] is not None else None,
                        'avg_angle': avg_angle,
                        'angle_std_dev': std_angle,
                        **corner_angles  # Add individual corner angles
                    }
                    image_db_data.append(image_data)
                    
                    # Add to file_results for image-to-result mapping
                    self.file_results.append({
                        'filename': filename,
                        'filepath': filepath,
                        'image_number': i,
                        'acquisition_date': acquisition_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'analysis_type': 'Field Size and Shape Validation',
                        'dimensions': dimensions,
                        'size_validation': size_validation,
                        'angle_validation': angle_validation,
                        'measurements': image_data,
                        'status': 'PASS' if (size_validation and size_validation['is_valid'] and 
                                           angle_validation and angle_validation['is_valid']) else 'FAIL'
                    })
                else:
                    # Store None values if data is missing
                    image_db_data.append({
                        'width_mm': None,
                        'height_mm': None,
                        'avg_angle': None,
                        'angle_std_dev': None
                    })
                    
                    # Add to file_results even on failure
                    self.file_results.append({
                        'filename': filename,
                        'filepath': filepath,
                        'image_number': i,
                        'acquisition_date': acquisition_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'analysis_type': 'Field Size and Shape Validation',
                        'status': 'ERROR',
                        'error': 'Missing dimensions or angle data'
                    })
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                # Store None values on error
                image_db_data.append({
                    'width_mm': None,
                    'height_mm': None,
                    'avg_angle': None,
                    'angle_std_dev': None
                })
        
        # Calculer le résultat global
        self.calculate_overall_result()
        
        # Note: Database saving is handled by the frontend via API endpoint
        # The test execution just returns results
        
        return self.to_dict()
    
    def to_dict(self):
        """Override to_dict to include visualizations, test_id, filenames, and file_results"""
        result = super().to_dict()
        
        # Add filenames at top level for easy database storage
        if hasattr(self, 'dicom_files') and self.dicom_files:
            result['filenames'] = [os.path.basename(f) for f in self.dicom_files]
        
        # Add file_results for image-to-result mapping
        if hasattr(self, 'file_results') and self.file_results:
            result['file_results'] = self.file_results
        
        # Add visualizations to the output
        if self.visualizations:
            result['visualizations'] = self.visualizations
            logger.info(f"[MVIC-TO-DICT] Including {len(self.visualizations)} visualizations")
        else:
            logger.warning("[MVIC-TO-DICT] No visualizations to include")
        
        # Add test_id if saved to database
        if hasattr(self, 'test_id'):
            result['test_id'] = self.test_id
        
        logger.info(f"[MVIC-TO-DICT] Result keys: {list(result.keys())}")
        return result
    
    def save_to_database(self, filenames: Optional[List[str]] = None):
        """
        Save MVIC test results to database
        
        Args:
            filenames: Optional list of source DICOM filenames
        
        Returns:
            int: Test ID from database
        """
        try:
            from database_helpers import save_mvic_to_database
            
            # Prepare results list - one entry per image
            results_list = []
            for i in range(1, 6):  # 5 images
                image_key = f"Image {i}"
                if image_key in self.results:
                    img_result = self.results[image_key]
                    results_list.append({
                        'top_left_angle': img_result.get('top_left_angle', 0),
                        'top_right_angle': img_result.get('top_right_angle', 0),
                        'bottom_left_angle': img_result.get('bottom_left_angle', 0),
                        'bottom_right_angle': img_result.get('bottom_right_angle', 0),
                        'height': img_result.get('height', 0),
                        'width': img_result.get('width', 0)
                    })
            
            test_id = save_mvic_to_database(
                operator=self.operator,
                test_date=self.test_date,
                overall_result=self.overall_result,
                results=results_list,
                notes=self.notes,
                filenames=filenames or self.dicom_files
            )
            
            self.test_id = test_id
            return test_id
            
        except Exception as e:
            logger.error(f"Error saving MVIC test to database: {e}")
            raise
    
    def get_form_data(self):
        """
        Retourner les données du formulaire pour le frontend
        
        Returns:
            dict: Configuration du formulaire
        """
        return {
            'title': 'MVIC - MV Imaging Check',
            'description': 'Validation de la taille et de la forme du champ de radiation (5 images requises)',
            'fields': [
                {
                    'name': 'test_date',
                    'label': 'Date du test:',
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
                    'label': 'Fichiers DICOM:',
                    'type': 'file',
                    'required': True,
                    'accept': '.dcm',
                    'multiple': True,
                    'description': 'Sélectionner exactement 5 fichiers DICOM (taille et angles détectés automatiquement)'
                },
                {
                    'name': 'notes',
                    'label': 'Notes:',
                    'type': 'textarea',
                    'required': False,
                    'placeholder': 'Notes additionnelles (optionnel)'
                }
            ],
            'tolerance': 'Taille: ±1mm, Angles: ±1°',
            'file_upload': True  # Special flag for file upload handling
        }


def test_mvic(operator: str, files: List[str],
              test_date: Optional[datetime] = None, notes: Optional[str] = None):
    """
    Fonction utilitaire pour exécuter le test MVIC-Champ
    
    Args:
        operator: Nom de l'opérateur
        files: Liste de 5 fichiers DICOM
        test_date: Date du test (par défaut: maintenant)
        notes: Notes additionnelles
    
    Returns:
        dict: Résultats du test
    """
    test = MVICChampTest()
    return test.execute(
        files=files,
        operator=operator,
        test_date=test_date,
        notes=notes
    )


if __name__ == "__main__":
    # Exemple d'utilisation
    import sys
    
    if len(sys.argv) < 7:
        print("Usage: python mvic_test.py <operator> <file1> <file2> <file3> <file4> <file5>")
        print("Example: python mvic_test.py 'Jean Dupont' image1.dcm image2.dcm image3.dcm image4.dcm image5.dcm")
        sys.exit(1)
    
    operator = sys.argv[1]
    files = sys.argv[2:7]  # 5 files
    
    result = test_mvic(operator, files)
    
    print("\n" + "="*60)
    print("RÉSULTATS DU TEST MVIC")
    print("="*60)
    print(f"Test: {result['test_name']}")
    print(f"Opérateur: {result['operator']}")
    print(f"Date: {result['test_date']}")
    print(f"\nRésultat global: {result['overall_result']}")
    print("\nDétails:")
    for name, data in result['results'].items():
        print(f"  {name}: {data['value']} [{data['status']}]")
        if data.get('details'):
            print(f"    → {data['details']}")
