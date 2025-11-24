"""
Field Shape Validation (Forme Champ)

Validates that the detected radiation field has rectangular shape (all angles are 90°).
Uses the same preprocessing and detection as taille_champ.py.
Tolerance: ±1°
Provides visual recap similar to mlc_leaf_and_jaw scripts.
"""
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pydicom
from pathlib import Path


class FieldShapeValidator:
    def __init__(self):
        # Detection parameters (from mlc_leaf_and_jaw scripts)
        self.tolerance_threshold = 127  # Binary threshold at 50%
        self.tolerance_kernel_size = 3  # Morphological operations kernel
        self.min_area = 200  # Minimum contour area in pixels
        self.merge_distance_px = 40  # Distance for merging nearby contours
        
        # Angle validation
        self.expected_angle = 90.0  # Expected corner angle in degrees
        self.angle_tolerance = 1.0  # Tolerance in degrees
        
    def load_dicom_image(self, filepath):
        """Load DICOM image and extract metadata"""
        try:
            ds = pydicom.dcmread(filepath)
            image_array = ds.pixel_array.astype(np.float32)
            
            # Extract geometric parameters
            SAD = float(ds.RadiationMachineSAD)
            SID = float(ds.RTImageSID)
            scaling_factor = SAD / SID
            
            # Extract pixel spacing
            pixel_spacing = ds.ImagePlanePixelSpacing
            pixel_spacing_x = float(pixel_spacing[0])
            pixel_spacing_y = float(pixel_spacing[1])
            
            # Extract RT Image Position
            rt_image_position = ds.RTImagePosition
            rt_image_pos_x = float(rt_image_position[0])
            rt_image_pos_y = float(rt_image_position[1])
            
            metadata = {
                'SAD': SAD,
                'SID': SID,
                'scaling_factor': scaling_factor,
                'pixel_spacing_x': pixel_spacing_x,
                'pixel_spacing_y': pixel_spacing_y,
                'rt_image_pos_x': rt_image_pos_x,
                'rt_image_pos_y': rt_image_pos_y
            }
            
            return image_array, ds, metadata
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None, None
    
    def preprocess_image(self, image_array):
        """Preprocess image with normalization, CLAHE, and Laplacian sharpening."""
        # Normalize to 0-1 range
        normalized_img = (image_array - image_array.min()) / (image_array.max() - image_array.min())
        
        # Convert to 8-bit
        img_8bit = cv2.normalize(normalized_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(img_8bit)
        
        # Apply Laplacian sharpening
        laplacian_kernel = np.array([[0, -1, 0],
                                     [-1, 5, -1],
                                     [0, -1, 0]], dtype=np.float32)
        laplacian_sharpened = cv2.filter2D(clahe_img, -1, laplacian_kernel)
        laplacian_sharpened = np.clip(laplacian_sharpened, 0, 255).astype(np.uint8)
        
        return img_8bit, clahe_img, laplacian_sharpened
    
    def detect_field_contours(self, clahe_img):
        """Detect field contours using thresholding and morphological operations."""
        # Create binary image
        _, binary_image = cv2.threshold(clahe_img, self.tolerance_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                          (self.tolerance_kernel_size, self.tolerance_kernel_size))
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > self.min_area]
        
        return contours, binary_image
    
    def merge_nearby_contours(self, contours, binary_image):
        """Merge contours that are close to each other."""
        if len(contours) <= 1:
            return contours
        
        # Get bounding rectangles and centers
        contour_data = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            cx = x + w / 2
            cy = y + h / 2
            contour_data.append({
                'index': i,
                'contour': contour,
                'bbox': (x, y, w, h),
                'center': (cx, cy),
                'merged': False
            })
        
        merged_contours = []
        
        for i, data_i in enumerate(contour_data):
            if data_i['merged']:
                continue
                
            close_contours = [data_i['contour']]
            data_i['merged'] = True
            
            for j, data_j in enumerate(contour_data):
                if i == j or data_j['merged']:
                    continue
                    
                dx = data_i['center'][0] - data_j['center'][0]
                dy = data_i['center'][1] - data_j['center'][1]
                distance = np.sqrt(dx**2 + dy**2)
                
                vertical_alignment = abs(dy) < 15
                
                if distance < self.merge_distance_px and vertical_alignment:
                    close_contours.append(data_j['contour'])
                    data_j['merged'] = True
            
            # Merge multiple close contours
            if len(close_contours) > 1:
                mask = np.zeros(binary_image.shape, dtype=np.uint8)
                for contour in close_contours:
                    cv2.fillPoly(mask, [contour], 255)
                
                merged_contours_temp, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if merged_contours_temp:
                    merged_contours.append(merged_contours_temp[0])
            else:
                merged_contours.append(close_contours[0])
        
        return merged_contours
    
    def detect_field_edges_canny(self, clahe_img):
        """
        Detect field edges using Canny edge detection (first derivative method).
        Similar to the approach in leaf_alignement.py for better edge detection.
        """
        # Apply Canny edge detection
        edges = cv2.Canny(clahe_img, 50, 150)
        
        return edges
    
    def get_merged_contour(self, contours):
        """Get the single merged contour from all detected contours"""
        if not contours:
            return None
        
        if len(contours) == 1:
            return contours[0]
        
        # Create mask with all contours filled
        # Find image dimensions from contour bounds
        all_points = np.vstack(contours)
        x_min, y_min = all_points.min(axis=0)[0]
        x_max, y_max = all_points.max(axis=0)[0]
        
        # Add padding
        pad = 50
        width = int(x_max - x_min + 2 * pad)
        height = int(y_max - y_min + 2 * pad)
        
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Shift contours to fit in mask
        shifted_contours = []
        for contour in contours:
            shifted = contour.copy()
            shifted[:, 0, 0] -= int(x_min - pad)
            shifted[:, 0, 1] -= int(y_min - pad)
            shifted_contours.append(shifted)
        
        cv2.fillPoly(mask, shifted_contours, 255)
        
        # Find merged contour
        merged_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if merged_contours:
            # Shift back to original coordinates
            merged = merged_contours[0].copy()
            merged[:, 0, 0] += int(x_min - pad)
            merged[:, 0, 1] += int(y_min - pad)
            return merged
        
        return None
    
    def detect_field_edges_canny(self, clahe_img):
        """
        Detect field edges using Canny edge detection (first derivative method).
        Similar to the approach in leaf_alignement.py for better edge detection.
        """
        # Apply Canny edge detection
        edges = cv2.Canny(clahe_img, 50, 150)
        
        return edges
    
    def calculate_corner_angles(self, contour):
        """
        Calculate angles at the corners of the field contour.
        Uses simple polygon approximation from binary threshold detection.
        """
        if contour is None or len(contour) < 3:
            return None
        
        # Approximate contour to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Need at least 3 points for angles
        if len(approx) < 3:
            return None
        
        corners = approx.reshape(-1, 2)
        angles = []
        
        # Calculate angle at each corner
        n = len(corners)
        for i in range(n):
            # Get three consecutive points
            p1 = corners[(i - 1) % n]
            p2 = corners[i]
            p3 = corners[(i + 1) % n]
            
            # Calculate vectors
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Calculate angle using dot product
            dot = np.dot(v1, v2)
            mag1 = np.linalg.norm(v1)
            mag2 = np.linalg.norm(v2)
            
            if mag1 > 0 and mag2 > 0:
                cos_angle = dot / (mag1 * mag2)
                # Clamp to avoid numerical errors
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle_rad = np.arccos(cos_angle)
                angle_deg = np.degrees(angle_rad)
                
                angles.append({
                    'corner': p2.tolist(),
                    'angle': angle_deg,
                    'index': i
                })
        
        return {
            'corners': corners,
            'angles': angles,
            'approx_polygon': approx
        }
    
    def validate_angles(self, angle_data):
        """
        Validate that all corner angles are 90° within tolerance.
        """
        if not angle_data or not angle_data['angles']:
            return {
                'is_valid': False,
                'angles': [],
                'invalid_angles': [],
                'message': 'No corner angles detected'
            }
        
        angles = angle_data['angles']
        invalid_angles = []
        
        for angle_info in angles:
            angle = angle_info['angle']
            error = abs(angle - self.expected_angle)
            
            angle_info['error'] = error
            angle_info['is_valid'] = error <= self.angle_tolerance
            
            if not angle_info['is_valid']:
                invalid_angles.append(angle_info)
        
        is_valid = len(invalid_angles) == 0
        
        if is_valid:
            message = f'All {len(angles)} corner angles are 90° within ±{self.angle_tolerance}° tolerance'
        else:
            message = f'{len(invalid_angles)} out of {len(angles)} corner angles exceed tolerance'
        
        return {
            'is_valid': is_valid,
            'angles': angles,
            'invalid_angles': invalid_angles,
            'num_corners': len(angles),
            'message': message
        }
    
    def visualize_shape_validation(self, original_img, clahe_img, binary_image, 
                                   contour, angle_data, validation, filename, dimensions_mm=None):
        """
        Create 4-panel visualization showing:
        1. CLAHE Enhanced
        2. Binary Threshold
        3. Detected Field with corners marked and side lengths
        4. Summary statistics
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Panel 1: CLAHE Enhanced
        axes[0, 0].imshow(clahe_img, cmap='gray')
        axes[0, 0].set_title('CLAHE Enhanced', fontweight='bold')
        axes[0, 0].axis('off')
        
        # Panel 2: Binary Threshold (50%)
        axes[0, 1].imshow(binary_image, cmap='gray')
        axes[0, 1].set_title('Binary Threshold (50%)', fontweight='bold')
        axes[0, 1].axis('off')
        
        # Panel 3: Detected Field with corners, angles, and side lengths
        axes[1, 0].imshow(clahe_img, cmap='gray')
        
        if contour is not None:
            # Draw the contour
            contour_img = clahe_img.copy()
            contour_img = cv2.cvtColor(contour_img, cv2.COLOR_GRAY2RGB)
            cv2.drawContours(contour_img, [contour], -1, (0, 255, 0), 2)
            
            # Draw approximated polygon
            if angle_data and 'approx_polygon' in angle_data:
                cv2.drawContours(contour_img, [angle_data['approx_polygon']], -1, (255, 255, 0), 2)
            
            axes[1, 0].imshow(contour_img)
            
            # Mark corners with angles
            if angle_data and 'angles' in angle_data:
                corners = []
                for angle_info in angle_data['angles']:
                    corner = angle_info['corner']
                    angle = angle_info['angle']
                    is_valid = angle_info['is_valid']
                    corners.append(corner)
                    
                    # Color: green if valid, red if invalid
                    color = 'lime' if is_valid else 'red'
                    
                    # Draw corner marker
                    axes[1, 0].plot(corner[0], corner[1], 'o', color=color, markersize=10)
                    
                    # Add angle label
                    offset = 15
                    axes[1, 0].text(corner[0] + offset, corner[1] + offset, 
                                   f'{angle:.1f}°',
                                   color=color, fontsize=10, fontweight='bold',
                                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
                
                # Add side lengths if dimensions provided
                if dimensions_mm and len(corners) >= 4:
                    # Calculate side lengths and add labels at midpoints
                    for i in range(len(corners)):
                        p1 = corners[i]
                        p2 = corners[(i + 1) % len(corners)]
                        
                        # Calculate midpoint
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
                            mm_dist = dimensions_mm.get('width_mm', 0)
                        else:
                            # Vertical side - this is the height
                            mm_dist = dimensions_mm.get('height_mm', 0)
                        
                        # Add length label on the side
                        axes[1, 0].text(mid_x, mid_y, 
                                       f'{mm_dist:.1f}mm',
                                       color='cyan', fontsize=11, fontweight='bold',
                                       ha='center', va='center',
                                       bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.8))
        
        axes[1, 0].set_title('Detected Field with Corner Angles & Side Lengths', fontweight='bold')
        axes[1, 0].axis('off')
        
        # Panel 4: Summary Statistics
        axes[1, 1].axis('off')
        
        if validation:
            status_symbol = '✅' if validation['is_valid'] else '❌'
            status_text = 'PASS' if validation['is_valid'] else 'FAIL'
            
            summary_lines = [
                f"FIELD SHAPE VALIDATION RESULTS:",
                f"",
                f"Status: {status_symbol} {status_text}",
                f"{validation['message']}",
                f"",
                f"Expected Angle: {self.expected_angle}°",
                f"Tolerance: ±{self.angle_tolerance}°",
                f"Total Corners: {validation['num_corners']}",
                f"",
                f"Corner Angles:",
            ]
            
            if validation['angles']:
                for i, angle_info in enumerate(validation['angles'], 1):
                    angle = angle_info['angle']
                    error = angle_info['error']
                    is_valid = angle_info['is_valid']
                    status = '✅' if is_valid else '❌'
                    summary_lines.append(
                        f"  {status} Corner {i}: {angle:.2f}° (error: {error:.2f}°)"
                    )
            
            summary_text = '\n'.join(summary_lines)
        else:
            summary_text = "No validation results available"
        
        axes[1, 1].text(0.05, 0.95, summary_text, transform=axes[1, 1].transAxes,
                       fontsize=10, verticalalignment='top', fontfamily='monospace')
        axes[1, 1].set_title('Summary', fontweight='bold')
        
        plt.tight_layout()
        
        # Save figure
        output_filename = f"field_shape_{Path(filename).stem}.png"
        plt.savefig(output_filename, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {output_filename}")
        plt.close()
        
        return output_filename
    
    def process_image(self, filepath):
        """Process a single DICOM image to validate field shape"""
        print(f"\n{'='*60}")
        print(f"Field Shape Validation: {Path(filepath).name}")
        print(f"{'='*60}")
        
        # Load image and metadata
        image_array, ds, metadata = self.load_dicom_image(filepath)
        if image_array is None:
            return None
        
        # Preprocess image
        img_8bit, clahe_img, laplacian_sharpened = self.preprocess_image(image_array)
        print("✓ Preprocessing: Normalization → CLAHE → Laplacian Sharpening")
        
        # Detect contours
        contours, binary_image = self.detect_field_contours(clahe_img)
        print(f"✓ Initial contours found: {len(contours)}")
        
        # Merge nearby contours
        merged_contours = self.merge_nearby_contours(contours, binary_image)
        final_contours = [c for c in merged_contours if cv2.contourArea(c) > self.min_area]
        print(f"✓ After merging: {len(final_contours)} contours")
        
        # Get single merged contour for angle analysis
        field_contour = self.get_merged_contour(final_contours)
        
        if field_contour is None:
            print("❌ Could not detect field contour")
            return None
        
        # Calculate corner angles using polygon approximation from binary threshold
        angle_data = self.calculate_corner_angles(field_contour)
        
        if angle_data:
            print(f"✓ Detected {len(angle_data['angles'])} corners")
        else:
            print("❌ Could not calculate corner angles")
            return None
        
        # Validate angles
        validation = self.validate_angles(angle_data)
        
        print(f"\nCorner Angles:")
        for i, angle_info in enumerate(validation['angles'], 1):
            status = '✅' if angle_info['is_valid'] else '❌'
            print(f"  {status} Corner {i}: {angle_info['angle']:.2f}° (error: {angle_info['error']:.2f}°)")
        
        print(f"\nValidation Result:")
        if validation['is_valid']:
            print(f"  ✅ PASS: {validation['message']}")
        else:
            print(f"  ❌ FAIL: {validation['message']}")
            print(f"  Invalid corners: {len(validation['invalid_angles'])}")
        
        # Create visualization (without dimensions for now, will be added by caller)
        viz_filename = self.visualize_shape_validation(
            img_8bit, clahe_img, binary_image, 
            field_contour, angle_data, validation, 
            Path(filepath).name,
            dimensions_mm=None  # Will be provided by MVIC test
        )
        
        print(f"{'='*60}\n")
        
        return {
            'angle_data': angle_data,
            'validation': validation,
            'metadata': metadata,
            'visualization': viz_filename
        }


def main():
    """Main entry point for standalone execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python forme_champ.py <dicom_file> [<dicom_file2> ...]")
        print("\nValidates that all corner angles are 90° ±1°")
        print("Generates visual recap with corner angle annotations")
        sys.exit(1)
    
    validator = FieldShapeValidator()
    
    # Process all provided DICOM files
    results = []
    for filepath in sys.argv[1:]:
        result = validator.process_image(filepath)
        if result:
            results.append({
                'file': Path(filepath).name,
                'result': result
            })
    
    # Summary
    if results:
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        valid_count = sum(1 for r in results if r['result']['validation']['is_valid'])
        total_count = len(results)
        print(f"Total files processed: {total_count}")
        print(f"Valid field shapes: {valid_count}")
        print(f"Invalid field shapes: {total_count - valid_count}")
        
        print("\nDetailed Results:")
        for r in results:
            status = "✅ PASS" if r['result']['validation']['is_valid'] else "❌ FAIL"
            num_corners = r['result']['validation']['num_corners']
            print(f"  {status} | {r['file']} | {num_corners} corners detected")


if __name__ == "__main__":
    main()
