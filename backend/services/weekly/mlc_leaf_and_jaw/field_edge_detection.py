"""
Field Edge Detection

Detects field edges/contours from a DICOM image (NO LEAVES, NO CENTER).
Based on dicom_analysis_V2.ipynb Section 4: Contour Detection and Merging.
"""
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web server
import matplotlib.pyplot as plt
import pydicom
import sys
from pathlib import Path


class FieldEdgeDetector:
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
    
    # Visualization removed - values only for monthly trend analysis
    
    def process_image(self, filepath):
        """Process a single DICOM image to detect field edges
         filepath: Path to the DICOM file
         returns: Dictionary with detection results and metadata
        """
        print(f"\n{'='*60}")
        print(f"Field Edge Detection: {Path(filepath).name}")
        print(f"{'='*60}")
        
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
        print(f"Settings: threshold={self.tolerance_threshold}, min_area={self.min_area}, merge_distance={self.merge_distance_px}px")
        
        print(f"{'='*60}\n")
        
        return {
            'contour_count': len(final_contours),
            'contours': final_contours,
            'metadata': metadata
        }


def main():
    """Main entry point for standalone execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python field_edge_detection.py <dicom_file>")
        sys.exit(1)
    
    detector = FieldEdgeDetector()
    result = detector.process_image(sys.argv[1])
    
    if result:
        print(f"✅ Field edge detection completed successfully - {result['contour_count']} regions detected")
    else:
        print("❌ Field edge detection failed")


if __name__ == "__main__":
    main()
