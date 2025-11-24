"""
Field Center Detection

Detects the center of the radiation field from a DICOM image.
Based on dicom_analysis_V2.ipynb Section 3 & 4: Image Preprocessing and Contour Detection.
"""
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web server
import matplotlib.pyplot as plt
import pydicom
import sys
from pathlib import Path


class FieldCenterDetector:
    def __init__(self):
        # Detection parameters (from notebook Section 4)
        self.tolerance_threshold = 127  # Binary threshold at 50%
        self.tolerance_kernel_size = 3  # Morphological operations kernel
        self.min_area = 200  # Minimum contour area in pixels
        self.merge_distance_px = 40  # Distance for merging nearby contours
        
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
            rt_image_pos_x = float(rt_image_position[0])  # mm from patient origin (X)
            rt_image_pos_y = float(rt_image_position[1])  # mm from patient origin (Y)
            
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
        """
        Preprocess image with normalization, CLAHE, and Laplacian sharpening.
        Follows notebook Section 3: Image Preprocessing exactly.
        """
        # Normalize to 0-1 range
        normalized_img = (image_array - image_array.min()) / (image_array.max() - image_array.min())
        
        # Convert to 8-bit for OpenCV processing
        img_8bit = cv2.normalize(normalized_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(img_8bit)
        
        # Apply Laplacian sharpening (from notebook)
        laplacian_kernel = np.array([[0, -1, 0],
                                     [-1, 5, -1],
                                     [0, -1, 0]], dtype=np.float32)
        laplacian_sharpened = cv2.filter2D(clahe_img, -1, laplacian_kernel)
        laplacian_sharpened = np.clip(laplacian_sharpened, 0, 255).astype(np.uint8)
        
        return img_8bit, clahe_img, laplacian_sharpened
    
    def detect_field_contours(self, clahe_img):
        """
        Detect field contours using thresholding and morphological operations.
        Follows notebook Section 4: Contour Detection.
        """
        # Create binary image
        _, binary_image = cv2.threshold(clahe_img, self.tolerance_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations to clean up regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                          (self.tolerance_kernel_size, self.tolerance_kernel_size))
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > self.min_area]
        
        return contours, binary_image
    
    def merge_nearby_contours(self, contours, binary_image):
        """
        Merge contours that are close to each other.
        Follows notebook Section 4: Contour Merging exactly.
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
    
    def calculate_field_center(self, contours, metadata):
        """Calculate the center of the radiation field"""
        if not contours:
            return None
        
        # Find overall bounding box of all contours
        all_x_min = min([cv2.boundingRect(c)[0] for c in contours])
        all_x_max = max([cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] for c in contours])
        all_y_min = min([cv2.boundingRect(c)[1] for c in contours])
        all_y_max = max([cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3] for c in contours])
        
        # Calculate center in pixels
        center_x_px = (all_x_min + all_x_max) / 2
        center_y_px = (all_y_min + all_y_max) / 2
        
        # Convert to mm coordinates (patient reference frame)
        center_x_mm = metadata['rt_image_pos_x'] + (center_x_px * metadata['pixel_spacing_x'])
        center_y_mm = metadata['rt_image_pos_y'] + (center_y_px * metadata['pixel_spacing_y'])
        
        # Convert to isocenter coordinates
        center_x_iso = center_x_mm * metadata['scaling_factor']
        center_y_iso = center_y_mm * metadata['scaling_factor']
        
        # Calculate field size
        field_width_px = all_x_max - all_x_min
        field_height_px = all_y_max - all_y_min
        
        field_width_mm = field_width_px * metadata['pixel_spacing_x'] * metadata['scaling_factor']
        field_height_mm = field_height_px * metadata['pixel_spacing_y'] * metadata['scaling_factor']
        
        return {
            'center_x_px': center_x_px,
            'center_y_px': center_y_px,
            'center_x_mm': center_x_mm,
            'center_y_mm': center_y_mm,
            'center_x_iso': center_x_iso,
            'center_y_iso': center_y_iso,
            'field_width_px': field_width_px,
            'field_height_px': field_height_px,
            'field_width_mm': field_width_mm,
            'field_height_mm': field_height_mm,
            'bbox': (all_x_min, all_y_min, all_x_max, all_y_max)
        }
    
    # Visualization removed - values only for monthly trend analysis
    
    def process_image(self, filepath):
        """Process a single DICOM image to detect field center"""
        print(f"\n{'='*60}")
        print(f"Field Center Detection: {Path(filepath).name}")
        print(f"{'='*60}")
        
        # Load image and metadata
        image_array, ds, metadata = self.load_dicom_image(filepath)
        if image_array is None:
            return None
        
        # Preprocess image (Normalization → CLAHE → Laplacian Sharpening)
        img_8bit, clahe_img, laplacian_sharpened = self.preprocess_image(image_array)
        print("Preprocessing: Normalization → CLAHE → Laplacian Sharpening")
        
        # Detect contours
        contours, binary_image = self.detect_field_contours(clahe_img)
        print(f"Initial contours found: {len(contours)}")
        
        # Merge nearby contours
        merged_contours = self.merge_nearby_contours(contours, binary_image)
        final_contours = [c for c in merged_contours if cv2.contourArea(c) > self.min_area]
        print(f"After merging: {len(final_contours)} contours")
        
        # Calculate field center
        field_center = self.calculate_field_center(final_contours, metadata)
        
        if field_center:
            print(f"\nField Center (Image Coordinates):")
            print(f"  u: {field_center['center_x_px']:.2f} px")
            print(f"  v: {field_center['center_y_px']:.2f} px")
            print(f"\nField Center (Isocenter):")
            print(f"  X: {field_center['center_x_iso']:.2f} mm")
            print(f"  Y: {field_center['center_y_iso']:.2f} mm")
            print(f"  Field Size: {field_center['field_width_mm']:.2f} × {field_center['field_height_mm']:.2f} mm")
        else:
            print("\n⚠️  Could not detect field center")
        
        print(f"{'='*60}\n")
        
        return {
            'field_center': field_center,
            'metadata': metadata
        }


def main():
    """Main entry point for standalone execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python field_center_detection.py <dicom_file>")
        sys.exit(1)
    
    detector = FieldCenterDetector()
    result = detector.process_image(sys.argv[1])
    
    if result and result['field_center']:
        print("✅ Field center detection completed successfully")
    else:
        print("❌ Field center detection failed")


if __name__ == "__main__":
    main()
