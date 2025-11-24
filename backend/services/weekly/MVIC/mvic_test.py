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


class MVICTest(BaseTest):
    """
    Test MVIC - Validation de la taille et de la forme du champ de radiation
    Traite 5 images DICOM et extrait automatiquement les informations
    """
    
    def __init__(self):
        super().__init__(
            test_name="MVIC - MV Imaging Check",
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
    
    def _generate_visualization_with_dimensions(self, filepath, dimensions, image_index):
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
            
            # Create visualization with dimensions
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            
            # Panel 1: CLAHE Enhanced
            axes[0, 0].imshow(clahe_img, cmap='gray')
            axes[0, 0].set_title('CLAHE Enhanced', fontweight='bold', fontsize=14)
            axes[0, 0].axis('off')
            
            # Panel 2: Binary Threshold (50%)
            axes[0, 1].imshow(binary_image, cmap='gray')
            axes[0, 1].set_title('Binary Threshold (50%)', fontweight='bold', fontsize=14)
            axes[0, 1].axis('off')
            
            # Panel 3: Detected Field with annotations
            contour_img = clahe_img.copy()
            contour_img = cv2.cvtColor(contour_img, cv2.COLOR_GRAY2RGB)
            cv2.drawContours(contour_img, [field_contour], -1, (0, 255, 0), 2)
            
            if angle_data and 'approx_polygon' in angle_data:
                cv2.drawContours(contour_img, [angle_data['approx_polygon']], -1, (255, 255, 0), 2)
            
            axes[1, 0].imshow(contour_img)
            
            # Mark corners with angles
            corners = []
            if angle_data and 'angles' in angle_data:
                for angle_info in angle_data['angles']:
                    corner = angle_info['corner']
                    angle = angle_info['angle']
                    is_valid = angle_info['is_valid']
                    corners.append(corner)
                    
                    color = 'lime' if is_valid else 'red'
                    axes[1, 0].plot(corner[0], corner[1], 'o', color=color, markersize=12)
                    
                    offset = 20
                    axes[1, 0].text(corner[0] + offset, corner[1] + offset, 
                                   f'{angle:.1f}°',
                                   color=color, fontsize=12, fontweight='bold',
                                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8))
                
                # Add side lengths
                if dimensions and len(corners) >= 4:
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
                            mm_dist = dimensions.get('width_mm', 0)
                        else:
                            # Vertical side - this is the height
                            mm_dist = dimensions.get('height_mm', 0)
                        
                        axes[1, 0].text(mid_x, mid_y, 
                                       f'{mm_dist:.1f}mm',
                                       color='cyan', fontsize=13, fontweight='bold',
                                       ha='center', va='center',
                                       bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.9))
            
            axes[1, 0].set_title('Field with Angles & Side Lengths', fontweight='bold', fontsize=14)
            axes[1, 0].axis('off')
            
            # Panel 4: Summary
            axes[1, 1].axis('off')
            status_symbol = '✅' if validation['is_valid'] else '❌'
            status_text = 'PASS' if validation['is_valid'] else 'FAIL'
            
            summary_lines = [
                f"FIELD VALIDATION - IMAGE {image_index}",
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
            axes[1, 1].text(0.05, 0.95, summary_text, transform=axes[1, 1].transAxes,
                           fontsize=11, verticalalignment='top', fontfamily='monospace')
            axes[1, 1].set_title('Summary', fontweight='bold', fontsize=14)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
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
        
        # Log chronological order
        logger.info("Ordre chronologique des fichiers:")
        for i, (filepath, dt) in enumerate(files_with_datetime, 1):
            logger.info(f"  {i}. {os.path.basename(filepath)} - {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Traiter chaque fichier
        for i, (filepath, acquisition_date) in enumerate(files_with_datetime, 1):
            filename = os.path.basename(filepath)
            
            try:
                # Ajouter l'information du fichier
                self.add_result(
                    name=f"image_{i}_fichier",
                    value=filename,
                    status="INFO",
                    details=f"Date d'acquisition: {acquisition_date.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # ========== VALIDATION DE LA TAILLE ==========
                size_result = self.size_validator.process_image(filepath)
                
                if size_result and size_result['dimensions']:
                    dimensions = size_result['dimensions']
                    validation = size_result['validation']
                    
                    # Résultat: Taille détectée
                    self.add_result(
                        name=f"image_{i}_taille_detectee",
                        value=f"{dimensions['width_mm']:.2f} × {dimensions['height_mm']:.2f}",
                        status="INFO",
                        unit="mm",
                        details=f"Dimensions du champ détectées (Image {i})"
                    )
                    
                    # Résultat: Validation de la taille
                    if validation['is_valid']:
                        self.add_result(
                            name=f"image_{i}_validation_taille",
                            value=validation['matched_size'],
                            status="PASS",
                            unit="mm",
                            tolerance="±1mm",
                            details=f"Erreur: ±{validation['width_error']:.2f}mm (largeur), ±{validation['height_error']:.2f}mm (hauteur)"
                        )
                    else:
                        self.add_result(
                            name=f"image_{i}_validation_taille",
                            value=f"{dimensions['width_mm']:.2f}×{dimensions['height_mm']:.2f}",
                            status="FAIL",
                            unit="mm",
                            tolerance="±1mm",
                            details=validation['message']
                        )
                else:
                    self.add_result(
                        name=f"image_{i}_validation_taille",
                        value="Erreur",
                        status="FAIL",
                        details=f"Impossible de détecter les dimensions du champ (Image {i})"
                    )
                
                # ========== VALIDATION DE LA FORME ==========
                # Generate visualization with dimensions from size validation
                viz_base64 = self._generate_visualization_with_dimensions(
                    filepath, 
                    dimensions if size_result and size_result.get('dimensions') else None,
                    i
                )
                
                shape_result = self.shape_validator.process_image(filepath)
                
                if shape_result and shape_result['validation']:
                    validation = shape_result['validation']
                    angle_data = shape_result['angle_data']
                    
                    # Résultat: Angles des coins
                    if validation['angles']:
                        angles_str = ", ".join([f"{a['angle']:.2f}°" for a in validation['angles']])
                        self.add_result(
                            name=f"image_{i}_angles_coins",
                            value=angles_str,
                            status="INFO",
                            unit="°",
                            details=f"Angles mesurés (Image {i})"
                        )
                    
                    # Résultat: Validation de la forme
                    if validation['is_valid']:
                        self.add_result(
                            name=f"image_{i}_validation_forme",
                            value="Tous les angles à 90°",
                            status="PASS",
                            unit="°",
                            tolerance="±1°",
                            details=validation['message']
                        )
                    else:
                        invalid_count = len(validation['invalid_angles'])
                        self.add_result(
                            name=f"image_{i}_validation_forme",
                            value=f"{invalid_count} angle(s) hors tolérance",
                            status="FAIL",
                            unit="°",
                            tolerance="±1°",
                            details=validation['message']
                        )
                    
                    # Add visualization with base64 encoding (like mlc_leaf_jaw)
                    if viz_base64:
                        self.visualizations.append({
                            'name': f'Image {i}: {filename}',
                            'type': 'image',
                            'data': viz_base64,
                            'filename': filename,
                            'index': i,
                            'acquisition_date': acquisition_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'statistics': {
                                'status': 'PASS' if validation['is_valid'] and (size_result and size_result['validation']['is_valid']) else 'FAIL',
                                'field_size': f"{dimensions['width_mm']:.1f}x{dimensions['height_mm']:.1f}mm" if dimensions else 'N/A',
                                'angles_valid': f"{len([a for a in validation['angles'] if a['is_valid']])}/{len(validation['angles'])}"
                            }
                        })
                else:
                    self.add_result(
                        name=f"image_{i}_validation_forme",
                        value="Erreur",
                        status="FAIL",
                        details=f"Impossible de détecter les angles du champ (Image {i})"
                    )
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                self.add_result(
                    name=f"image_{i}_erreur",
                    value=str(e),
                    status="FAIL",
                    details=f"Erreur lors du traitement de l'image {i}: {str(e)}"
                )
        
        # Calculer le résultat global
        self.calculate_overall_result()
        
        return self.to_dict()
    
    def to_dict(self):
        """Override to_dict to include visualizations"""
        result = super().to_dict()
        
        # Add visualizations to the output
        if self.visualizations:
            result['visualizations'] = self.visualizations
        
        return result
    
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
                }
            ],
            'tolerance': 'Taille: ±1mm, Angles: ±1°',
            'file_upload': True  # Special flag for file upload handling
        }


def test_mvic(operator: str, files: List[str],
              test_date: Optional[datetime] = None, notes: Optional[str] = None):
    """
    Fonction utilitaire pour exécuter le test MVIC
    
    Args:
        operator: Nom de l'opérateur
        files: Liste de 5 fichiers DICOM
        test_date: Date du test (par défaut: maintenant)
        notes: Notes additionnelles
    
    Returns:
        dict: Résultats du test
    """
    test = MVICTest()
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
