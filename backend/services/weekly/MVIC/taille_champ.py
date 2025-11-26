"""
Field Size Validation (Taille Champ)

Validates that the detected radiation field size matches expected dimensions within tolerance.
Expected field sizes: 150x85, 85x85, 50x50 (multiple 50x50 fields possible)
Tolerance: ±1mm
"""
import cv2
import numpy as np
import pydicom
from pathlib import Path


class FieldSizeValidator:
    def __init__(self):
        # Detection parameters (from mlc_leaf_and_jaw scripts)
        self.tolerance_threshold = 255 * 0.5  # Binary threshold at 50%
        self.tolerance_kernel_size = 3  # Morphological operations kernel
        self.min_area = 200  # Minimum contour area in pixels
        self.merge_distance_px = 40  # Distance for merging nearby contours
        
        # Expected field sizes (width x height in mm at isocenter)
        self.expected_sizes = [
            {'width': 150, 'height': 85, 'name': '150x85'},
            {'width': 85, 'height': 85, 'name': '85x85'},
            {'width': 50, 'height': 50, 'name': '50x50'},
        ]
        
        # Size tolerance in mm
        self.size_tolerance = 1.0
        
    def load_dicom_image(self, filepath):
        """Load DICOM image and extract metadata"""
        try:
            ds = pydicom.dcmread(filepath)
            image_array = ds.pixel_array.astype(np.float32)
            
            # Extract geometric parameters
            SAD = float(ds.RadiationMachineSAD)  # Source to Axis Distance
            SID = float(ds.RTImageSID)  # Source to Image Distance
            scaling_factor = SAD / SID  # Geometric scaling factor
            
            # Extract pixel spacing
            pixel_spacing = ds.ImagePlanePixelSpacing
            pixel_spacing_x = float(pixel_spacing[0])  # mm per pixel (X direction)
            pixel_spacing_y = float(pixel_spacing[1])  # mm per pixel (Y direction)
            
            # Extract RT Image Position
            rt_image_position = ds.RTImagePosition
            rt_image_pos_x = float(rt_image_position[0])
            rt_image_pos_y = float(rt_image_position[1])
            
            # Extract acquisition date
            acquisition_date = getattr(ds, 'AcquisitionDate', getattr(ds, 'ContentDate', 'Unknown'))
            if acquisition_date != 'Unknown' and len(acquisition_date) == 8:
                # Format YYYYMMDD to YYYY-MM-DD
                acquisition_date = f"{acquisition_date[:4]}-{acquisition_date[4:6]}-{acquisition_date[6:]}"
            
            metadata = {
                'SAD': SAD,
                'SID': SID,
                'scaling_factor': scaling_factor,
                'pixel_spacing_x': pixel_spacing_x,
                'pixel_spacing_y': pixel_spacing_y,
                'rt_image_pos_x': rt_image_pos_x,
                'rt_image_pos_y': rt_image_pos_y,
                'acquisition_date': acquisition_date
            }
            
            return image_array, ds, metadata
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None, None
    
    def preprocess_image(self, image_array):
        """
        Preprocess image with normalization, CLAHE, and Laplacian sharpening.
        """
        # Normalize to 0-1 range
        normalized_img = (image_array - image_array.min()) / (image_array.max() - image_array.min())
        
        # Convert to 8-bit for OpenCV processing
        img_8bit = cv2.normalize(normalized_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Apply CLAHE for contrast enhancement
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
        """
        Detect field contours using thresholding and morphological operations.
        """
        # Store grayscale image for edge detection
        self.grayscale_image = clahe_img
        
        # Create binary image
        _, binary_image = cv2.threshold(clahe_img, self.tolerance_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations to clean up regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                          (self.tolerance_kernel_size, self.tolerance_kernel_size))
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
        
        # Store binary image for contour detection
        self.binary_image = binary_image
        
        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > self.min_area]
        
        return contours, binary_image
    
    def merge_nearby_contours(self, contours, binary_image):
        """
        Merge contours that are close to each other.
        """
        if len(contours) <= 1:
            return contours
        
        # Get bounding rectangles and centers for all contours
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
                    
                # Calculate distance between centers
                dx = data_i['center'][0] - data_j['center'][0]
                dy = data_i['center'][1] - data_j['center'][1]
                distance = np.sqrt(dx**2 + dy**2)
                
                # Check if vertically aligned (same row)
                vertical_alignment = abs(dy) < 15
                
                # Merge if close and aligned
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
    
    def calculate_field_dimensions(self, contours, metadata):
        """Calculate the dimensions of the radiation field at isocenter using midpoints of sides"""
        if not contours:
            return None
        
        # Merge all contours into a single contour
        if len(contours) == 1:
            merged_contour = contours[0]
        else:
            # Find overall bounding box
            all_x_min = min([cv2.boundingRect(c)[0] for c in contours])
            all_x_max = max([cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] for c in contours])
            all_y_min = min([cv2.boundingRect(c)[1] for c in contours])
            all_y_max = max([cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3] for c in contours])
            
            # Create mask and merge contours
            all_points = np.vstack(contours)
            x_min, y_min = all_points.min(axis=0)[0]
            x_max, y_max = all_points.max(axis=0)[0]
            pad = 50
            width = int(x_max - x_min + 2 * pad)
            height = int(y_max - y_min + 2 * pad)
            mask = np.zeros((height, width), dtype=np.uint8)
            
            shifted_contours = []
            for contour in contours:
                shifted = contour.copy()
                shifted[:, 0, 0] -= int(x_min - pad)
                shifted[:, 0, 1] -= int(y_min - pad)
                shifted_contours.append(shifted)
            
            cv2.fillPoly(mask, shifted_contours, 255)
            merged_contours_temp, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if merged_contours_temp:
                merged_contour = merged_contours_temp[0].copy()
                merged_contour[:, 0, 0] += int(x_min - pad)
                merged_contour[:, 0, 1] += int(y_min - pad)
            else:
                return None
        
        # Use binary threshold at 50% (127/255) to detect field edges
        # Pixels darker than 50% are considered part of the field
        _, binary_threshold = cv2.threshold(self.grayscale_image, self.tolerance_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Find bounding box from merged contour to determine scan area
        contour_points = merged_contour.reshape(-1, 2)
        x_coords = contour_points[:, 0]
        y_coords = contour_points[:, 1]
        all_x_min = int(x_coords.min())
        all_x_max = int(x_coords.max())
        all_y_min = int(y_coords.min())
        all_y_max = int(y_coords.max())
        
        # Extract the region of interest from binary image
        field_region = binary_threshold[all_y_min:all_y_max, all_x_min:all_x_max]
        
        # Find all black pixels (like in notebook cell 9)
        black_pixels = np.where(field_region > 0)
        
        if len(black_pixels[0]) > 0:
            # Get min and max positions of black pixels (relative to region)
            top_y_relative = np.min(black_pixels[0])
            bottom_y_relative = np.max(black_pixels[0])
            left_x_relative = np.min(black_pixels[1])
            right_x_relative = np.max(black_pixels[1])
            
            # Convert to absolute coordinates
            top_y_absolute = all_y_min + top_y_relative
            bottom_y_absolute = all_y_min + bottom_y_relative
            left_x_absolute = all_x_min + left_x_relative
            right_x_absolute = all_x_min + right_x_relative
            
            # Calculate dimensions in pixels
            field_width_px = right_x_absolute - left_x_absolute
            field_height_px = bottom_y_absolute - top_y_absolute
        else:
            field_width_px = 0
            field_height_px = 0
        
        # Convert to mm at isocenter (apply scaling factor)
        field_width_mm = field_width_px * metadata['pixel_spacing_x'] * metadata['scaling_factor']
        field_height_mm = field_height_px * metadata['pixel_spacing_y'] * metadata['scaling_factor']
        
        return {
            'width_mm': field_width_mm,
            'height_mm': field_height_mm,
            'width_px': field_width_px,
            'height_px': field_height_px
        }
    
    def validate_field_size(self, dimensions):
        """
        Validate if the detected field size matches any expected size within tolerance.
        Returns validation result with matched size or None if no match.
        """
        if not dimensions:
            return {
                'is_valid': False,
                'matched_size': None,
                'width_error': None,
                'height_error': None,
                'message': 'No field dimensions detected'
            }
        
        width = dimensions['width_mm']
        height = dimensions['height_mm']
        
        # Check against each expected size
        for expected in self.expected_sizes:
            # Check both orientations (width x height and height x width)
            # This handles cases where the field might be rotated
            width_error_1 = abs(width - expected['width'])
            height_error_1 = abs(height - expected['height'])
            
            width_error_2 = abs(width - expected['height'])
            height_error_2 = abs(height - expected['width'])
            
            # Check orientation 1: width matches expected width
            if width_error_1 <= self.size_tolerance and height_error_1 <= self.size_tolerance:
                return {
                    'is_valid': True,
                    'matched_size': expected['name'],
                    'expected_width': expected['width'],
                    'expected_height': expected['height'],
                    'detected_width': width,
                    'detected_height': height,
                    'width_error': width_error_1,
                    'height_error': height_error_1,
                    'message': f'Field size matches {expected["name"]} within tolerance'
                }
            
            # Check orientation 2: width matches expected height (rotated)
            if width_error_2 <= self.size_tolerance and height_error_2 <= self.size_tolerance:
                return {
                    'is_valid': True,
                    'matched_size': f'{expected["name"]} (rotated)',
                    'expected_width': expected['height'],
                    'expected_height': expected['width'],
                    'detected_width': width,
                    'detected_height': height,
                    'width_error': width_error_2,
                    'height_error': height_error_2,
                    'message': f'Field size matches {expected["name"]} (rotated) within tolerance'
                }
        
        # No match found
        return {
            'is_valid': False,
            'matched_size': None,
            'detected_width': width,
            'detected_height': height,
            'width_error': None,
            'height_error': None,
            'message': f'Field size {width:.2f}x{height:.2f}mm does not match any expected size (±{self.size_tolerance}mm tolerance)'
        }
    
    def process_image(self, filepath):
        """Process a single DICOM image to validate field size"""
        print(f"\n{'='*60}")
        print(f"Field Size Validation: {Path(filepath).name}")
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
        
        # Calculate field dimensions
        dimensions = self.calculate_field_dimensions(final_contours, metadata)
        
        if dimensions:
            print(f"\nDetected Field Size (at isocenter):")
            print(f"  Width:  {dimensions['width_mm']:.2f} mm")
            print(f"  Height: {dimensions['height_mm']:.2f} mm")
        
        # Validate against expected sizes
        validation = self.validate_field_size(dimensions)
        
        print(f"\nValidation Result:")
        if validation['is_valid']:
            print(f"  ✅ PASS: {validation['message']}")
            print(f"  Expected: {validation['expected_width']}x{validation['expected_height']}mm")
            print(f"  Detected: {validation['detected_width']:.2f}x{validation['detected_height']:.2f}mm")
            print(f"  Error: ±{validation['width_error']:.2f}mm (width), ±{validation['height_error']:.2f}mm (height)")
        else:
            print(f"  ❌ FAIL: {validation['message']}")
            print(f"  Expected sizes: {', '.join([s['name'] for s in self.expected_sizes])}")
            print(f"  Tolerance: ±{self.size_tolerance}mm")
        
        print(f"{'='*60}\n")
        
        return {
            'dimensions': dimensions,
            'validation': validation,
            'metadata': metadata
        }


def main():
    """Main entry point for standalone execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python taille_champ.py <dicom_file> [<dicom_file2> ...]")
        print("\nExpected field sizes:")
        print("  - 150x80 mm")
        print("  - 85x85 mm")
        print("  - 50x50 mm")
        print("\nTolerance: ±1mm")
        sys.exit(1)
    
    validator = FieldSizeValidator()
    
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
        print(f"Valid field sizes: {valid_count}")
        print(f"Invalid field sizes: {total_count - valid_count}")
        
        print("\nDetailed Results:")
        for r in results:
            status = "✅ PASS" if r['result']['validation']['is_valid'] else "❌ FAIL"
            matched = r['result']['validation']['matched_size'] if r['result']['validation']['is_valid'] else "No match"
            print(f"  {status} | {r['file']} | {matched}")


if __name__ == "__main__":
    main()
