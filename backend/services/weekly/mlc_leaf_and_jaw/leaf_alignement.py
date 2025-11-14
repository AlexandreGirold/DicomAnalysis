"""
Leaf Alignment Analysis

Uses field edge detection to find individual MLC leaf blocks, then calculates
the middle lines between adjacent leaves to determine alignment angles.
The goal is to find the middle between each individual leaf and calculate:
- Leaf Bank Y1 Average Angle
- Leaf Bank Y2 Average Angle
"""
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web server
import matplotlib.pyplot as plt
import pydicom
import sys
from pathlib import Path


class LeafAlignmentAnalyzer:
    def __init__(self):
        # Detection parameters (same as field_edge_detection.py)
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
        Uses same preprocessing as field_edge_detection.py
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
        Detect field contours using same method as field_edge_detection.py
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
        Uses same method as field_edge_detection.py
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
    
    def find_leaf_midlines(self, contours):
        """
        Find the middle lines between adjacent leaf blocks
        """
        if len(contours) < 2:
            return [], []
        
        # Get bounding boxes and sort by x-coordinate (left to right)
        leaf_boxes = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            leaf_boxes.append({
                'index': i,
                'contour': contour,
                'bbox': (x, y, w, h),
                'center_x': x + w/2,
                'center_y': y + h/2,
                'left_edge': x,
                'right_edge': x + w,
                'top_edge': y,
                'bottom_edge': y + h
            })
        
        # Sort by x-coordinate (left to right)
        leaf_boxes.sort(key=lambda box: box['center_x'])
        
        # Find midlines between adjacent leaves
        midlines = []
        for i in range(len(leaf_boxes) - 1):
            left_leaf = leaf_boxes[i]
            right_leaf = leaf_boxes[i + 1]
            
            # Calculate middle x-coordinate between adjacent leaves
            middle_x = (left_leaf['right_edge'] + right_leaf['left_edge']) / 2
            
            # Determine y-range (overlap region between the two leaves)
            top_y = max(left_leaf['top_edge'], right_leaf['top_edge'])
            bottom_y = min(left_leaf['bottom_edge'], right_leaf['bottom_edge'])
            
            if bottom_y > top_y:  # Valid overlap
                midlines.append({
                    'x': middle_x,
                    'y_start': top_y,
                    'y_end': bottom_y,
                    'center_y': (top_y + bottom_y) / 2,
                    'length': bottom_y - top_y,
                    'angle': 90.0,  # Assume perfect vertical for now
                    'left_leaf_idx': i,
                    'right_leaf_idx': i + 1
                })
        
        return midlines, leaf_boxes
    
    def calculate_midline_angles(self, midlines, processed_img):
        """
        Calculate actual angles of midlines by analyzing the image data along each midline
        """
        for midline in midlines:
            x = int(midline['x'])
            y_start = int(midline['y_start'])
            y_end = int(midline['y_end'])
            
            # Extract pixel values along the midline
            if y_end > y_start and 0 <= x < processed_img.shape[1]:
                # Get a small window around the midline to detect the actual edge
                window_width = 5
                x_start = max(0, x - window_width)
                x_end = min(processed_img.shape[1], x + window_width)
                
                # Extract region around midline
                region = processed_img[y_start:y_end, x_start:x_end]
                
                if region.size > 0:
                    # Find the most vertical line in this region using edge detection
                    edges = cv2.Canny(region, 50, 150)
                    
                    # Use HoughLines to detect the most prominent line
                    lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=int(region.shape[0] * 0.3))
                    
                    if lines is not None and len(lines) > 0:
                        # Find the most vertical line (closest to 90 degrees)
                        best_angle = 90.0
                        for line in lines:
                            rho, theta = line[0]
                            angle_deg = np.degrees(theta)
                            
                            # Convert to angle from vertical (90 degrees is perfect vertical)
                            if angle_deg > 90:
                                angle_from_vertical = 180 - angle_deg
                            else:
                                angle_from_vertical = angle_deg
                            
                            # Convert to actual angle (90° is perfect vertical)
                            actual_angle = 90 + (angle_from_vertical - 90)
                            
                            # Keep the angle closest to vertical
                            if abs(actual_angle - 90) < abs(best_angle - 90):
                                best_angle = actual_angle
                        
                        midline['angle'] = best_angle
                    else:
                        # Default to 90 degrees if no line detected
                        midline['angle'] = 90.0
                else:
                    midline['angle'] = 90.0
            else:
                midline['angle'] = 90.0
        
        return [midline['angle'] for midline in midlines]
    
    def classify_midlines_by_banks(self, midlines, image_height):
        """
        Classify midlines into Y1 (bottom) and Y2 (top) banks
        """
        y1_midlines = []  # Bottom bank
        y2_midlines = []  # Top bank
        
        # Use image center as dividing line
        center_y = image_height / 2
        
        for midline in midlines:
            if midline['center_y'] > center_y:
                y1_midlines.append(midline)
            else:
                y2_midlines.append(midline)
        
        return y1_midlines, y2_midlines
    
    def visualize_leaf_alignment(self, original_img, contours, midlines, y1_midlines, y2_midlines, filename):
        """
        Create visualization showing detected leaves and their midlines with angles
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Panel 1: Detected leaf blocks with midlines
        axes[0, 0].imshow(original_img, cmap='gray')
        
        # Draw leaf blocks
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            rect = plt.Rectangle((x, y), w, h, fill=False, color='green', linewidth=1)
            axes[0, 0].add_patch(rect)
            cx, cy = x + w//2, y + h//2
            axes[0, 0].text(cx, cy, str(i+1), color='red', fontsize=6, ha='center')
        
        # Draw all midlines as green crosses (like in the image)
        for i, midline in enumerate(midlines):
            x = midline['x']
            y1, y2 = midline['y_start'], midline['y_end']
            
            # Draw vertical line
            axes[0, 0].plot([x, x], [y1, y2], 'lime', linewidth=2)
            
            # Draw crosses at regular intervals along the midline
            num_crosses = 10
            for j in range(num_crosses):
                y_pos = y1 + (y2 - y1) * j / (num_crosses - 1)
                cross_size = 3
                # Horizontal line of cross
                axes[0, 0].plot([x-cross_size, x+cross_size], [y_pos, y_pos], 'lime', linewidth=1)
                # Vertical line of cross (already drawn above)
            
            # Add angle text
            axes[0, 0].text(x+5, (y1+y2)/2, f"{midline['angle']:.1f}°", 
                           color='yellow', fontsize=7, rotation=0)
        
        axes[0, 0].set_title(f'Detected Leaves & Midlines ({len(contours)} blocks, {len(midlines)} midlines)', fontweight='bold')
        axes[0, 0].axis('off')
        
        # Panel 2: Y1 Bank midlines (bottom)
        axes[0, 1].imshow(original_img, cmap='gray')
        for midline in y1_midlines:
            x = midline['x']
            y1, y2 = midline['y_start'], midline['y_end']
            axes[0, 1].plot([x, x], [y1, y2], 'blue', linewidth=3)
            axes[0, 1].text(x+5, (y1+y2)/2, f"{midline['angle']:.1f}°", 
                           color='cyan', fontsize=8, rotation=0)
        axes[0, 1].set_title(f'Y1 Bank (Bottom) - {len(y1_midlines)} midlines', fontweight='bold')
        axes[0, 1].axis('off')
        
        # Panel 3: Y2 Bank midlines (top)
        axes[1, 0].imshow(original_img, cmap='gray')
        for midline in y2_midlines:
            x = midline['x']
            y1, y2 = midline['y_start'], midline['y_end']
            axes[1, 0].plot([x, x], [y1, y2], 'red', linewidth=3)
            axes[1, 0].text(x+5, (y1+y2)/2, f"{midline['angle']:.1f}°", 
                           color='yellow', fontsize=8, rotation=0)
        axes[1, 0].set_title(f'Y2 Bank (Top) - {len(y2_midlines)} midlines', fontweight='bold')
        axes[1, 0].axis('off')
        
        # Panel 4: Summary statistics
        axes[1, 1].axis('off')
        
        # Calculate statistics
        y1_angles = [midline['angle'] for midline in y1_midlines]
        y2_angles = [midline['angle'] for midline in y2_midlines]
        
        y1_avg = np.mean(y1_angles) if y1_angles else 0
        y2_avg = np.mean(y2_angles) if y2_angles else 0
        y1_std = np.std(y1_angles) if y1_angles else 0
        y2_std = np.std(y2_angles) if y2_angles else 0
        
        summary_text = f"""
LEAF ALIGNMENT ANALYSIS

Leaf Bank    Average Angle (°)    Std Dev (°)    Count
Y1           {y1_avg:.2f}            {y1_std:.2f}         {len(y1_midlines)}
Y2           {y2_avg:.2f}            {y2_std:.2f}         {len(y2_midlines)}

Total Leaf Blocks: {len(contours)}
Total Midlines: {len(midlines)}

Individual Midline Angles:
Y1: {', '.join([f'{a:.1f}°' for a in y1_angles[:8]])}{'...' if len(y1_angles) > 8 else ''}
Y2: {', '.join([f'{a:.1f}°' for a in y2_angles[:8]])}{'...' if len(y2_angles) > 8 else ''}
        """
        
        axes[1, 1].text(0.05, 0.95, summary_text, transform=axes[1, 1].transAxes, 
                        fontsize=10, verticalalignment='top', fontfamily='monospace')
        axes[1, 1].set_title('Analysis Summary', fontweight='bold')
        
        plt.tight_layout()
        
        # Save figure
        output_filename = f"leaf_alignment_{Path(filename).stem}.png"
        plt.savefig(output_filename, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {output_filename}")
        plt.close()
        
        return output_filename
    
    def process_image(self, filepath):
        """Process a single DICOM image to analyze leaf alignment"""
        print(f"\n{'='*60}")
        print(f"Leaf Alignment Analysis: {Path(filepath).name}")
        print(f"{'='*60}")
        
        # Load image and metadata
        image_array, ds, metadata = self.load_dicom_image(filepath)
        if image_array is None:
            return None
        
        # Preprocess image (same as field_edge_detection.py)
        img_8bit, clahe_img, laplacian_sharpened = self.preprocess_image(image_array)
        print("Preprocessing: Normalization → CLAHE → Laplacian Sharpening")
        
        # Detect leaf block contours (using field edge detection approach)
        contours, binary_image = self.detect_field_contours(clahe_img)
        print(f"Initial contours found: {len(contours)}")
        
        # Merge nearby contours (same as field_edge_detection.py)
        merged_contours = self.merge_nearby_contours(contours, binary_image)
        final_contours = [c for c in merged_contours if cv2.contourArea(c) > self.min_area]
        print(f"After merging: {len(final_contours)} leaf blocks detected")
        
        # Find midlines between adjacent leaves
        midlines, leaf_boxes = self.find_leaf_midlines(final_contours)
        print(f"Found {len(midlines)} midlines between adjacent leaves")
        
        # Calculate actual midline angles by analyzing image data
        angles = self.calculate_midline_angles(midlines, clahe_img)
        
        # Classify midlines into Y1 and Y2 banks
        y1_midlines, y2_midlines = self.classify_midlines_by_banks(midlines, image_array.shape[0])
        print(f"Y1 Bank (bottom): {len(y1_midlines)} midlines")
        print(f"Y2 Bank (top): {len(y2_midlines)} midlines")
        
        # Calculate average angles
        y1_angles = [midline['angle'] for midline in y1_midlines]
        y2_angles = [midline['angle'] for midline in y2_midlines]
        
        y1_avg_angle = np.mean(y1_angles) if y1_angles else 0
        y2_avg_angle = np.mean(y2_angles) if y2_angles else 0
        
        print(f"\nLEAF ALIGNMENT RESULTS:")
        print(f"Leaf Bank    Average Angle (°)")
        print(f"Y1           {y1_avg_angle:.2f}")
        print(f"Y2           {y2_avg_angle:.2f}")
        
        # Create visualization
        viz_filename = self.visualize_leaf_alignment(clahe_img, final_contours, midlines,
                                                    y1_midlines, y2_midlines, Path(filepath).name)
        
        print(f"{'='*60}\n")
        
        return {
            'y1_avg_angle': y1_avg_angle,
            'y2_avg_angle': y2_avg_angle,
            'y1_midlines': y1_midlines,
            'y2_midlines': y2_midlines,
            'total_midlines': len(midlines),
            'total_leaf_blocks': len(final_contours),
            'metadata': metadata,
            'visualization': viz_filename
        }


def main():
    """Main entry point for standalone execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python leaf_alignement.py <dicom_file>")
        sys.exit(1)
    
    analyzer = LeafAlignmentAnalyzer()
    result = analyzer.process_image(sys.argv[1])
    
    if result:
        print(f"✅ Leaf alignment analysis completed successfully")
        print(f"   Y1 Average Angle: {result['y1_avg_angle']:.2f}°")
        print(f"   Y2 Average Angle: {result['y2_avg_angle']:.2f}°")
        print(f"   Total Midlines: {result['total_midlines']}")
        print(f"   Total Leaf Blocks: {result['total_leaf_blocks']}")
    else:
        print("❌ Leaf alignment analysis failed")


if __name__ == "__main__":
    main()