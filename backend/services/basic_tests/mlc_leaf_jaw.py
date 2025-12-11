"""
MLC Leaf and Jaw Test
Tests Multi-Leaf Collimator (MLC) blade positions from DICOM images
"""
from .base_test import BaseTest
from datetime import datetime
from typing import Optional, List
import os
import sys
import logging
import base64
import io
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
from scipy import ndimage

# Setup logging
logger = logging.getLogger(__name__)

# Add parent directory to path to import leaf_pos
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

try:
    from leaf_pos import MLCBladeAnalyzer
except ImportError:
    # Try alternative import path
    from ..leaf_pos import MLCBladeAnalyzer


class MLCLeafJawTest(BaseTest):
    """
    Test for analyzing MLC blade and jaw positions from DICOM images
    Processes DICOM files and returns detailed analysis with visualizations
    """
    
    def __init__(self):
        super().__init__(
            test_name="MLC Leaf and Jaw",
            description="ANSM - Exactitude des positions de lames MLC - Analyse DICOM"
        )
        self.analyzer = None
        self.analyzer_results = []  # Separate variable for MLC analyzer output
        self.visualizations = []
        self.dicom_files = []  # Store file paths for visualization
    
    def execute(self, files: List[str], operator: str, test_date: Optional[datetime] = None):
        """
        Execute the MLC analysis test on DICOM files
        
        Multi-step analysis based on file creation date order:
        1. Image 1: Center detection (U and V coordinates)
        2. Image 2: Leaf edges detection
        3. Image 3: Leaf middle alignment check (Y1 and Y2 at 90°)
        4. Image 4-5: Leaf position calculation
        5. Image 6: Jaw position (X1 and X2 at ~-100mm)
        
        Args:
            files: List of DICOM file paths
            operator: Name of the operator performing the test
            test_date: Date of the test (defaults to current date)
        
        Returns:
            dict: Test results including blade analysis and visualizations
        """
        # Set test information
        self.set_test_info(operator, test_date)
        
        # Validate inputs
        if not files:
            raise ValueError("At least one DICOM file is required")
        
        # Sort files by creation date
        files_with_datetime = []
        for filepath in files:
            try:
                ds = self.analyzer.get_dicom_dataset(filepath) if self.analyzer else self._read_dicom_header(filepath)
                dt = self._get_dicom_datetime(ds)
                if dt:
                    files_with_datetime.append((filepath, dt))
                else:
                    logger.warning(f"Could not extract datetime from {filepath}, using file modification time")
                    mtime = os.path.getmtime(filepath)
                    files_with_datetime.append((filepath, datetime.fromtimestamp(mtime)))
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
                # Use file modification time as fallback
                mtime = os.path.getmtime(filepath)
                files_with_datetime.append((filepath, datetime.fromtimestamp(mtime)))
        
        # Sort by datetime (oldest first)
        files_with_datetime.sort(key=lambda x: x[1])
        sorted_files = [f[0] for f in files_with_datetime]
        
        logger.info(f"Processing {len(sorted_files)} files in chronological order")
        for i, (filepath, dt) in enumerate(files_with_datetime, 1):
            logger.info(f"  {i}. {os.path.basename(filepath)} - {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add input files
        self.add_input("dicom_files", [os.path.basename(f) for f in sorted_files], "files")
        self.add_input("file_count", len(sorted_files), "files")
        
        # Store file paths for visualization
        self.dicom_files = sorted_files
        
        # Create analyzer instance
        self.analyzer = MLCBladeAnalyzer(gui_mode=False)
        
        # Store individual file results for visualization
        self.file_results = []  # List of results per file
        
        try:
            # Process each file based on its position in the sequence
            all_results = []
            
            for file_index, file_path in enumerate(sorted_files):
                logger.info(f"Processing file {file_index + 1}/{len(sorted_files)}: {os.path.basename(file_path)}")
                
                # Determine analysis type based on file position (1-indexed)
                analysis_type = self._get_analysis_type(file_index + 1, len(sorted_files))
                logger.info(f"Analysis type: {analysis_type}")
                
                # Perform appropriate analysis
                result = self._analyze_image(file_path, analysis_type, file_index)
                
                if result is None:
                    logger.warning(f"Failed to analyze DICOM file: {file_path}")
                    continue
                
                # Extract acquisition date from DICOM
                ds = self._read_dicom_header(file_path)
                acquisition_date = self._get_dicom_datetime(ds)
                
                # Store per-file results
                self.file_results.append({
                    'file': file_path,
                    'results': result,
                    'analysis_type': analysis_type,
                    'acquisition_date': acquisition_date.strftime('%Y-%m-%d %H:%M:%S') if acquisition_date else 'Unknown'
                })
                
                # Combine results for overall statistics (only for leaf position tests)
                if analysis_type == 'leaf_position' and isinstance(result, list):
                    all_results.extend(result)
            
            # Store combined results for overall statistics
            self.analyzer_results = all_results
            logger.info(f"Total results collected: {len(self.analyzer_results)}")
            
            # Process results
            self._process_results()
            
            # Generate visualizations
            self._generate_visualizations()
            
            # Calculate overall result
            self.calculate_overall_result()
            
            return self.to_dict()
            
        except Exception as e:
            logger.error(f"Error in MLC analysis: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Add error result
            self.add_result(
                name="analysis_error",
                value=str(e),
                status="FAIL",
                tolerance="No errors"
            )
            
            self.overall_result = "FAIL"
            self.overall_status = "FAIL"
            
            return self.to_dict()
    
    def _read_dicom_header(self, filepath):
        """Read DICOM header without loading full pixel data"""
        import pydicom
        return pydicom.dcmread(filepath, stop_before_pixels=True)
    
    def _get_dicom_datetime(self, ds):
        """Extract creation date and time from DICOM dataset"""
        try:
            if hasattr(ds, 'ContentDate') and hasattr(ds, 'ContentTime'):
                date_str = ds.ContentDate
                time_str = ds.ContentTime
            elif hasattr(ds, 'AcquisitionDate') and hasattr(ds, 'AcquisitionTime'):
                date_str = ds.AcquisitionDate
                time_str = ds.AcquisitionTime
            elif hasattr(ds, 'StudyDate') and hasattr(ds, 'StudyTime'):
                date_str = ds.StudyDate
                time_str = ds.StudyTime
            else:
                return None
            
            datetime_str = f"{date_str}{time_str.split('.')[0]}"
            from datetime import datetime
            dt = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            return dt
        except Exception as e:
            logger.error(f"Error extracting datetime: {e}")
            return None
    
    def _get_analysis_type(self, image_number, total_images):
        """Determine analysis type based on image position in sequence"""
        if image_number == 1:
            return 'center_detection'
        elif image_number == 2:
            return 'jaw_position'
        elif image_number == 3:
            return 'leaf_position'
        elif image_number == 4:
            return 'leaf_position'
        elif image_number == 5:
            return 'blade_straightness'  # Use image 5 for leaf alignment
        else:
            # Default to leaf position for any additional images
            return 'leaf_position'
    
    def _analyze_image(self, filepath, analysis_type, file_index):
        """Analyze image based on analysis type"""
        if analysis_type == 'center_detection':
            return self._analyze_center_detection(filepath)
        elif analysis_type == 'leaf_edges':
            return self._analyze_leaf_edges(filepath)
        elif analysis_type == 'blade_straightness':
            return self._analyze_blade_straightness(filepath)
        elif analysis_type == 'leaf_position':
            return self.analyzer.process_image(filepath)
        elif analysis_type == 'jaw_position':
            return self._analyze_jaw_position(filepath)
        else:
            return None
    
    def _analyze_center_detection(self, filepath):
        """Analyze center detection (U and V coordinates) using first derivative edge detection"""
        logger.info("Performing center detection analysis with edge detection")
        original_image, ds = self.analyzer.load_dicom_image(filepath)
        if original_image is None:
            return None
        
        # Apply edge detection using first derivative (gradient)
        image = self.analyzer.invert_image(original_image)
        edges = self.analyzer.find_edges(image)
        
        # Calculate threshold from edge-detected image
        roi = edges[437:867, 5:1023]  # Same ROI as blade position detection
        max_val = np.max(roi)
        min_val = np.min(roi)
        edge_threshold = min_val + (max_val - min_val) * self.analyzer.edge_detection_threshold
        
        # Use current center coordinates
        u_center = self.analyzer.center_u
        v_center = self.analyzer.center_v
        
        # Count edge pixels above threshold in ROI
        edge_pixels = np.sum(roi > edge_threshold)
        
        return {
            'type': 'center_detection',
            'u_center_px': u_center,
            'v_center_px': v_center,
            'edge_threshold': float(edge_threshold),
            'edge_pixels': int(edge_pixels),
            'status': 'OK'
        }
    
    def _analyze_leaf_edges(self, filepath):
        """Analyze leaf edges detection"""
        logger.info("Performing leaf edges detection analysis")
        original_image, ds = self.analyzer.load_dicom_image(filepath)
        if original_image is None:
            return None
        
        image = self.analyzer.invert_image(original_image)
        edges = self.analyzer.find_edges(image)
        
        # Count detected edges
        edge_threshold = np.max(edges) * 0.3
        edge_pixels = np.sum(edges > edge_threshold)
        
        return {
            'type': 'leaf_edges',
            'edge_pixels': int(edge_pixels),
            'edge_threshold': float(edge_threshold),
            'status': 'OK' if edge_pixels > 1000 else 'FAIL'
        }
    
    def _analyze_blade_straightness(self, filepath):
        """
        Analyze blade straightness (90° alignment) using the enhanced algorithm
        Uses 50% threshold for black/white classification and measures average angle deviation
        """
        logger.info("Performing blade straightness analysis (90° alignment)")
        original_image, ds = self.analyzer.load_dicom_image(filepath)
        if original_image is None:
            return None
        
        # Process image with 50% threshold
        image = self.analyzer.invert_image(original_image)
        
        # Apply 50% threshold: pixels 50% black or darker = black (0), else white (1)
        threshold_value = 0.5 * np.max(image)
        binary_image = (image > threshold_value).astype(np.float32)
        
        edges = self.analyzer.find_edges(binary_image)
        
        # Enhance processing
        edges_enhanced = ndimage.gaussian_filter(edges, sigma=1.0)
        binary_enhanced = ndimage.gaussian_filter(binary_image, sigma=0.5)
        
        # Analyze blade straightness for alternating pattern (14 open blades)
        results = []
        all_angles = []
        
        for idx, pair in enumerate(range(27, 55)):  # Blade pairs 27-54
            # Calculate blade position
            if pair >= 41:
                blade_offset = pair - 41
                u_pos = int(self.analyzer.center_u + blade_offset * self.analyzer.blade_width_pixels)
            else:
                blade_offset = 40 - pair
                u_pos = int(self.analyzer.center_u - (blade_offset + 1) * self.analyzer.blade_width_pixels)
            
            if u_pos < 0 or u_pos >= image.shape[1]:
                continue
            
            # Determine if blade should be open (alternating pattern: even indices = open)
            is_expected_open = (idx % 2) == 1
            
            if is_expected_open:
                # Analyze this open blade
                midline_coords, straightness_score, actual_angle, edges_detected = self._detect_blade_midline(
                    edges_enhanced, u_pos, self.analyzer.center_v, self.analyzer.blade_width_pixels, binary_enhanced
                )
                
                if edges_detected and actual_angle is not None:
                    all_angles.append(actual_angle)
                    results.append({
                        'pair': pair,
                        'u_pos': u_pos,
                        'angle': actual_angle,
                        'deviation': abs(90.0 - actual_angle),
                        'status': 'analyzed'
                    })
                else:
                    results.append({
                        'pair': pair,
                        'u_pos': u_pos,
                        'angle': None,
                        'deviation': None,
                        'status': 'no_detection'
                    })
            else:
                # Closed blade
                results.append({
                    'pair': pair,
                    'u_pos': u_pos,
                    'angle': None,
                    'deviation': None,
                    'status': 'closed'
                })
        
        # Calculate average angle and test result
        if all_angles:
            average_angle = np.mean(all_angles)
            angle_deviation_from_90 = abs(90.0 - average_angle)
            test_passed = angle_deviation_from_90 < 1.0  # Pass if less than 1° deviation
        else:
            average_angle = None
            angle_deviation_from_90 = None
            test_passed = False
        
        return {
            'type': 'blade_straightness',
            'total_blades': len([r for r in results if r['status'] in ['analyzed', 'no_detection']]),
            'analyzed_blades': len([r for r in results if r['status'] == 'analyzed']),
            'closed_blades': len([r for r in results if r['status'] == 'closed']),
            'average_angle': round(average_angle, 2) if average_angle else None,
            'deviation_from_90': round(angle_deviation_from_90, 2) if angle_deviation_from_90 else None,
            'test_passed': test_passed,
            'blade_results': results,
            'status': 'OK' if test_passed else 'FAIL'
        }
    
    def _detect_blade_midline(self, edges, u_pos, center_v, blade_width, binary_image=None):
        """
        Detect the midline between opposing blade edges using 50% threshold
        Returns the midline coordinates, straightness score, and actual angle
        """
        # Sample region around blade position
        v_start = int(center_v - 200)
        v_end = int(center_v + 200)
        
        if v_start < 0:
            v_start = 0
        if v_end >= edges.shape[0]:
            v_end = edges.shape[0] - 1
        if u_pos < 0 or u_pos >= edges.shape[1]:
            return None, None, None, False
        
        # Sample horizontal region around blade
        window = 15
        u_start = max(0, u_pos - window)
        u_end = min(edges.shape[1], u_pos + window)
        
        # Find midline points
        midline_points_u = []
        midline_points_v = []
        
        # Scan vertically to find midline at each level
        for v in range(v_start, v_end, 3):
            if v < 0 or v >= edges.shape[0]:
                continue
                
            # Get horizontal profile
            h_profile = edges[v, u_start:u_end]
            if len(h_profile) < 5:
                continue
            
            # Get binary profile for clearer gap detection
            if binary_image is not None:
                h_binary = binary_image[v, u_start:u_end]
            else:
                h_binary = h_profile
            
            # Apply smoothing
            h_smooth = ndimage.gaussian_filter1d(h_profile, sigma=0.8)
            h_binary_smooth = ndimage.gaussian_filter1d(h_binary, sigma=0.5) if binary_image is not None else h_smooth
            
            profile_length = len(h_smooth)
            center_idx = profile_length // 2
            
            # Find gap center using multiple methods
            gap_candidates = []
            
            # Method 1: Maximum in binary image (brightest = biggest gap)
            if binary_image is not None:
                max_idx = np.argmax(h_binary_smooth)
                gap_candidates.append(max_idx)
            
            # Method 2: Minimum in edge image
            min_idx = np.argmin(h_smooth)
            gap_candidates.append(min_idx)
            
            # Method 3: Find region above 50% threshold
            if binary_image is not None:
                threshold_50 = 0.5
                above_threshold = h_binary_smooth > threshold_50
                if np.any(above_threshold):
                    threshold_indices = np.where(above_threshold)[0]
                    center_of_threshold = int(np.mean(threshold_indices))
                    gap_candidates.append(center_of_threshold)
            
            # Choose best candidate
            if gap_candidates:
                gap_candidates = list(set(gap_candidates))
                if len(gap_candidates) == 1:
                    best_gap = gap_candidates[0]
                else:
                    distances = [abs(c - center_idx) for c in gap_candidates]
                    best_gap = gap_candidates[np.argmin(distances)]
                
                # Verify this is a gap
                if binary_image is not None:
                    gap_value_binary = h_binary_smooth[best_gap]
                    if gap_value_binary > 0.3:  # At least 30% white
                        u_midline = u_start + best_gap
                        midline_points_u.append(u_midline)
                        midline_points_v.append(v)
                else:
                    gap_value = h_smooth[best_gap]
                    max_value = np.max(h_smooth)
                    if max_value > gap_value * 1.2:
                        u_midline = u_start + best_gap
                        midline_points_u.append(u_midline)
                        midline_points_v.append(v)
        
        # Need at least 3 points for analysis
        if len(midline_points_u) < 3:
            # Try more lenient detection
            midline_points_u = []
            midline_points_v = []
            
            for v in range(v_start, v_end, 5):
                if v < 0 or v >= edges.shape[0]:
                    continue
                
                h_profile = edges[v, u_start:u_end]
                if len(h_profile) < 3:
                    continue
                
                # Just take the minimum
                min_idx = np.argmin(h_profile)
                u_midline = u_start + min_idx
                midline_points_u.append(u_midline)
                midline_points_v.append(v)
            
            if len(midline_points_u) < 3:
                return None, None, None, False
        
        # Convert to numpy arrays
        midline_points_u = np.array(midline_points_u)
        midline_points_v = np.array(midline_points_v)
        
        # Calculate straightness and angle
        u_variation = np.std(midline_points_u)
        
        try:
            if len(set(midline_points_u)) > 1:
                # Fit line: u = slope * v + intercept
                slope, intercept = np.polyfit(midline_points_v, midline_points_u, 1)
                
                # Calculate angle from vertical
                angle_from_vertical_rad = np.arctan(abs(slope))
                angle_from_vertical_deg = np.degrees(angle_from_vertical_rad)
                
                # Actual angle (90° - deviation from vertical)
                actual_angle = 90.0 - angle_from_vertical_deg
            else:
                # All u positions are the same - perfectly vertical
                actual_angle = 90.0
                
        except (np.linalg.LinAlgError, ValueError, FloatingPointError):
            if u_variation < 1.0:
                actual_angle = 90.0
            else:
                actual_angle = None
        
        return midline_points_v, u_variation, actual_angle, True
    
    def _analyze_jaw_position(self, filepath):
        """Analyze jaw position (X1 and X2 at ~-100mm)"""
        logger.info("Performing jaw position analysis")
        original_image, ds = self.analyzer.load_dicom_image(filepath)
        if original_image is None:
            return None
        
        image = self.analyzer.invert_image(original_image)
        edges = self.analyzer.find_edges(image)
        
        # Detect jaw edges (X1 left, X2 right)
        # Sample horizontal profile at center V
        center_v = int(self.analyzer.center_v)
        h_profile = edges[center_v, :]
        
        # Find peaks in horizontal profile
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(h_profile, height=np.max(h_profile) * 0.3, distance=50)
        
        # Identify X1 (left jaw) and X2 (right jaw)
        center_u = int(self.analyzer.center_u)
        left_peaks = [p for p in peaks if p < center_u]
        right_peaks = [p for p in peaks if p > center_u]
        
        x1_px = left_peaks[-1] if left_peaks else None
        x2_px = right_peaks[0] if right_peaks else None
        
        # Convert to mm from center
        x1_mm = ((x1_px - center_u) * self.analyzer.pixel_size) if x1_px is not None else None
        x2_mm = ((x2_px - center_u) * self.analyzer.pixel_size) if x2_px is not None else None
        
        # Expected jaw positions (~-100mm and ~+100mm)
        expected_jaw_pos = 100.0  # mm
        jaw_tolerance = 2.0  # mm
        
        x1_status = 'PASS' if x1_mm and abs(abs(x1_mm) - expected_jaw_pos) < jaw_tolerance else 'FAIL'
        x2_status = 'PASS' if x2_mm and abs(abs(x2_mm) - expected_jaw_pos) < jaw_tolerance else 'FAIL'
        
        return {
            'type': 'jaw_position',
            'x1_px': int(x1_px) if x1_px else None,
            'x2_px': int(x2_px) if x2_px else None,
            'x1_mm': round(x1_mm, 2) if x1_mm else None,
            'x2_mm': round(x2_mm, 2) if x2_mm else None,
            'x1_status': x1_status,
            'x2_status': x2_status,
            'status': 'PASS' if x1_status == 'PASS' and x2_status == 'PASS' else 'FAIL'
        }
    
    def _generate_visualizations(self):
        """Generate PNG visualization from the MLC analysis"""
        try:
            if not self.dicom_files or not self.analyzer:
                logger.warning("No DICOM files or analyzer available for visualization")
                return
            
            # Process each file for visualization based on analysis type
            for file_index, filepath in enumerate(self.dicom_files):
                if file_index < len(self.file_results):
                    analysis_type = self.file_results[file_index].get('analysis_type', 'leaf_position')
                    
                    if analysis_type == 'leaf_position':
                        self._generate_single_visualization(filepath, file_index)
                    else:
                        self._generate_analysis_visualization(filepath, file_index, analysis_type)
            
            logger.info(f"Generated {len(self.visualizations)} visualizations")
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _generate_analysis_visualization(self, filepath, file_index, analysis_type):
        """Generate visualization for non-leaf-position analysis types"""
        try:
            original_image, ds = self.analyzer.load_dicom_image(filepath)
            if original_image is None:
                logger.warning(f"Could not load image for visualization: {filepath}")
                return
            
            image = self.analyzer.invert_image(original_image)
            edges = self.analyzer.find_edges(image)
            
            # Get results for this file
            file_results = self.file_results[file_index]['results']
            
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Create visualization based on analysis type
            if analysis_type == 'center_detection':
                fig, axes = plt.subplots(1, 2, figsize=(12, 6))
                
                # Original image with center crosshair
                axes[0].imshow(original_image, cmap='gray')
                axes[0].axhline(y=file_results['v_center_px'], color='red', linestyle='--', linewidth=2, label='V Center')
                axes[0].axvline(x=file_results['u_center_px'], color='blue', linestyle='--', linewidth=2, label='U Center')
                axes[0].plot(file_results['u_center_px'], file_results['v_center_px'], 'r+', markersize=20, markeredgewidth=3)
                axes[0].set_title(f'Center Detection\nU={file_results["u_center_px"]:.1f}px, V={file_results["v_center_px"]:.1f}px', fontweight='bold')
                axes[0].legend()
                axes[0].axis('off')
                
                # Zoomed view
                zoom_size = 100
                u_center = int(file_results['u_center_px'])
                v_center = int(file_results['v_center_px'])
                zoomed = original_image[v_center-zoom_size:v_center+zoom_size, u_center-zoom_size:u_center+zoom_size]
                axes[1].imshow(zoomed, cmap='gray')
                axes[1].axhline(y=zoom_size, color='red', linestyle='--', linewidth=1)
                axes[1].axvline(x=zoom_size, color='blue', linestyle='--', linewidth=1)
                axes[1].plot(zoom_size, zoom_size, 'r+', markersize=15, markeredgewidth=2)
                axes[1].set_title('Zoomed Center View', fontweight='bold')
                axes[1].axis('off')
                
            elif analysis_type == 'leaf_edges':
                fig, axes = plt.subplots(1, 2, figsize=(12, 6))
                
                axes[0].imshow(original_image, cmap='gray')
                axes[0].set_title('Original Image', fontweight='bold')
                axes[0].axis('off')
                
                axes[1].imshow(edges, cmap='hot')
                axes[1].set_title(f'Leaf Edges Detection\n{file_results["edge_pixels"]} edge pixels detected', fontweight='bold')
                axes[1].axis('off')
                
            elif analysis_type == 'blade_straightness':
                fig, axes = plt.subplots(1, 2, figsize=(16, 8))
                
                # Original image with blade indicators
                axes[0].imshow(original_image, cmap='gray', alpha=0.8)
                axes[0].axhline(y=self.analyzer.center_v, color='cyan', linestyle='--', linewidth=1, alpha=0.5)
                axes[0].axvline(x=self.analyzer.center_u, color='cyan', linestyle='--', linewidth=1, alpha=0.5)
                
                # Draw blade indicators based on results
                for blade_result in file_results['blade_results']:
                    u_pos = blade_result['u_pos']
                    status = blade_result['status']
                    angle = blade_result['angle']
                    
                    if status == 'closed':
                        # Gray for closed blades
                        axes[0].axvline(x=u_pos, color='gray', alpha=0.2, linewidth=1)
                    elif status == 'analyzed' and angle is not None:
                        # Check if blade is off by 1° or more
                        blade_deviation = abs(90.0 - angle)
                        if blade_deviation >= 1.0:
                            color = 'red'  # Off by 1° or more
                        else:
                            color = 'green'  # Good blade
                        axes[0].axvline(x=u_pos, color=color, alpha=0.7, linewidth=2)
                    else:
                        # Orange for no detection
                        axes[0].axvline(x=u_pos, color='orange', alpha=0.5, linewidth=1)
                
                axes[0].set_title('Blade Straightness Check\nGreen=Good (<1°) | Red=Off (≥1°) | Gray=Closed', 
                                 fontweight='bold', fontsize=12)
                axes[0].axis('off')
                
                # Results summary table
                axes[1].axis('off')
                
                # Create summary table
                table_data = []
                table_data.append(['Metric', 'Value', 'Status'])
                table_data.append(['Total Open Blades', f'{file_results["analyzed_blades"]}', ''])
                
                if file_results['average_angle'] is not None:
                    table_data.append(['Average Angle', f'{file_results["average_angle"]:.2f}°', ''])
                    table_data.append(['Deviation from 90°', f'{file_results["deviation_from_90"]:.2f}°', ''])
                    test_result = "✓ PASS" if file_results['test_passed'] else "✗ FAIL"
                    table_data.append(['Test Result', 'Deviation < 1°', test_result])
                else:
                    table_data.append(['Average Angle', 'N/A', ''])
                    table_data.append(['Test Result', 'No data', '✗ FAIL'])
                
                # Create table
                table = axes[1].table(cellText=table_data, loc='center', cellLoc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(12)
                table.scale(1, 3)
                
                # Style header row
                for i in range(3):
                    cell = table[(0, i)]
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                
                # Color code result row
                if len(table_data) > 4:  # Has test result row
                    result_cell = table[(4, 2)]  # Test result status cell
                    if file_results['test_passed']:
                        result_cell.set_facecolor('#E8F5E9')
                        result_cell.set_text_props(color='green', weight='bold')
                    else:
                        result_cell.set_facecolor('#FFEBEE')
                        result_cell.set_text_props(color='red', weight='bold')
                
                axes[1].set_title('Blade Straightness Test Results\n(Average Angle Method)', 
                                 fontweight='bold', fontsize=14, pad=20)
                
            elif analysis_type == 'jaw_position':
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                
                axes[0, 0].imshow(original_image, cmap='gray')
                if file_results['x1_px']:
                    axes[0, 0].axvline(x=file_results['x1_px'], color='red', linewidth=2, label=f'X1 (Left): {file_results["x1_mm"]}mm')
                if file_results['x2_px']:
                    axes[0, 0].axvline(x=file_results['x2_px'], color='blue', linewidth=2, label=f'X2 (Right): {file_results["x2_mm"]}mm')
                axes[0, 0].axvline(x=self.analyzer.center_u, color='cyan', linestyle='--', linewidth=1, label='Center')
                axes[0, 0].set_title('Jaw Position Detection', fontweight='bold')
                axes[0, 0].legend()
                axes[0, 0].axis('off')
                
                axes[0, 1].imshow(edges, cmap='gray')
                axes[0, 1].set_title('Edge Detection', fontweight='bold')
                axes[0, 1].axis('off')
                
                # Horizontal profile
                center_v = int(self.analyzer.center_v)
                h_profile = edges[center_v, :]
                axes[1, 0].plot(h_profile)
                if file_results['x1_px']:
                    axes[1, 0].axvline(x=file_results['x1_px'], color='red', linestyle='--', label='X1')
                if file_results['x2_px']:
                    axes[1, 0].axvline(x=file_results['x2_px'], color='blue', linestyle='--', label='X2')
                axes[1, 0].axvline(x=self.analyzer.center_u, color='cyan', linestyle='--', label='Center')
                axes[1, 0].set_xlabel('U Coordinate (pixels)')
                axes[1, 0].set_ylabel('Edge Intensity')
                axes[1, 0].set_title('Horizontal Profile at Isocenter', fontweight='bold')
                axes[1, 0].legend()
                axes[1, 0].grid(True, alpha=0.3)
                
                # Summary
                axes[1, 1].text(0.5, 0.7, 'Jaw Positions:', ha='center', va='center', fontsize=14, fontweight='bold', transform=axes[1, 1].transAxes)
                axes[1, 1].text(0.5, 0.6, f'X1 (Left): {file_results["x1_mm"]}mm [{file_results["x1_status"]}]', 
                              ha='center', va='center', fontsize=12, 
                              color='green' if file_results["x1_status"] == 'PASS' else 'red',
                              transform=axes[1, 1].transAxes)
                axes[1, 1].text(0.5, 0.5, f'X2 (Right): {file_results["x2_mm"]}mm [{file_results["x2_status"]}]', 
                              ha='center', va='center', fontsize=12,
                              color='green' if file_results["x2_status"] == 'PASS' else 'red',
                              transform=axes[1, 1].transAxes)
                axes[1, 1].text(0.5, 0.4, f'Expected: ±100mm ±2mm', 
                              ha='center', va='center', fontsize=10, color='gray', transform=axes[1, 1].transAxes)
                axes[1, 1].text(0.5, 0.3, f'Overall: {file_results["status"]}', 
                              ha='center', va='center', fontsize=14, fontweight='bold',
                              color='green' if file_results["status"] == 'PASS' else 'red',
                              transform=axes[1, 1].transAxes)
                axes[1, 1].axis('off')
            
            plt.tight_layout()
            
            # Convert to base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            # Calculate statistics
            file_stats = {
                'status': file_results.get('status', 'UNKNOWN'),
                'analysis_type': analysis_type,
                'total_blades': file_results.get('total_blades', 0) if analysis_type == 'blade_straightness' else 0,
                'ok_blades': file_results.get('analyzed_blades', 0) if analysis_type == 'blade_straightness' else 0,
                'out_of_tolerance': 0,  # Not used for blade straightness
                'closed_blades': file_results.get('closed_blades', 0) if analysis_type == 'blade_straightness' else 0
            }
            
            # Store visualization
            filename = os.path.basename(filepath)
            analysis_name = analysis_type.replace('_', ' ').title()
            self.visualizations.append({
                'name': f'Image {file_index + 1}: {analysis_name} - {filename}',
                'type': 'image',
                'data': f'data:image/png;base64,{image_base64}',
                'filename': filename,
                'index': file_index,
                'statistics': file_stats
            })
            
            logger.info(f"Visualization generated for {filename} ({analysis_type})")
            
        except Exception as e:
            logger.error(f"Error generating visualization for {filepath}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _generate_single_visualization(self, filepath, file_index):
        """Generate visualization for a single DICOM file"""
        try:
            
            # Load and process image using analyzer's methods
            original_image, ds = self.analyzer.load_dicom_image(filepath)
            if original_image is None:
                logger.warning(f"Could not load image for visualization: {filepath}")
                return
            
            # Apply same processing as leaf_pos.py
            image = self.analyzer.invert_image(original_image)
            edges = self.analyzer.find_edges(image)
            
            # Get results for THIS specific file only
            file_specific_results = []
            if file_index < len(self.file_results):
                file_specific_results = self.file_results[file_index]['results']
            
            # Get detected points from results (reconstruct from file-specific results)
            detected_points_a = []
            detected_points_b = []
            
            # Parse results to extract detected points for this file only
            if isinstance(file_specific_results, list):
                for result in file_specific_results:
                    if isinstance(result, (list, tuple)) and len(result) >= 5:
                        pair, dist_sup, dist_inf, field_size, status = result[0], result[1], result[2], result[3], result[4]
                        
                        # Reconstruct point data structure
                        point = {
                            'pair': pair,
                            'u': None,  # Will be calculated
                            'v_sup': None,
                            'v_inf': None,
                            'field_size': field_size,
                            'status': status
                        }
                        
                        # Separate into A and B sections based on blade pair number
                        if pair >= 41:
                            detected_points_a.append(point)
                        else:
                            detected_points_b.append(point)
            
            # Generate visualization using analyzer's method
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            
            # Create the visualization figure
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Original image
            axes[0, 0].imshow(original_image, cmap='gray')
            axes[0, 0].set_title('Original DICOM Image', fontweight='bold')
            axes[0, 0].axis('off')
            
            # 2. Edge detection
            axes[0, 1].imshow(edges, cmap='gray')
            axes[0, 1].set_title('Edge Detection', fontweight='bold')
            axes[0, 1].axis('off')
            
            # 3. Detected blades on original - with leaf edge markers
            axes[1, 0].imshow(original_image, cmap='gray', alpha=0.7)
            axes[1, 0].axhline(y=self.analyzer.center_v, color='cyan', linestyle='--', linewidth=1, label='Center V')
            axes[1, 0].axvline(x=self.analyzer.center_u, color='cyan', linestyle='--', linewidth=1, label='Center U')
            
            # Draw detected leaf edges from file-specific results
            if isinstance(file_specific_results, list):
                cross_size = 8
                for result in file_specific_results:
                    if isinstance(result, (list, tuple)) and len(result) >= 5:
                        pair, dist_sup, dist_inf, field_size, status = result[0], result[1], result[2], result[3], result[4]
                        
                        # Skip closed blades
                        if status == 'CLOSED':
                            continue
                        
                        # Calculate blade position (u coordinate)
                        # Blade pairs: 27-40 are on the left, 41-54 are on the right
                        if pair >= 41:
                            # Right side blades (section A)
                            blade_offset = pair - 41
                            u_pos = self.analyzer.center_u + blade_offset * self.analyzer.blade_width_pixels
                        else:
                            # Left side blades (section B)
                            blade_offset = 40 - pair
                            u_pos = self.analyzer.center_u - (blade_offset + 1) * self.analyzer.blade_width_pixels
                        
                        # Calculate v coordinates from distances
                        # dist_sup and dist_inf are in mm, need to convert to pixels
                        v_sup = self.analyzer.center_v - (dist_sup / self.analyzer.pixel_size)
                        v_inf = self.analyzer.center_v - (dist_inf / self.analyzer.pixel_size)
                        
                        # Choose color based on status
                        if 'OK' in status:
                            color_sup = 'red'    # Top edge - red
                            color_inf = 'blue'   # Bottom edge - blue
                        else:
                            color_sup = 'orange'  # Out of tolerance - orange
                            color_inf = 'orange'
                        
                        # Draw top edge marker (horizontal cross)
                        axes[1, 0].plot([u_pos - cross_size, u_pos + cross_size], 
                                       [v_sup, v_sup], 
                                       color=color_sup, linewidth=2)
                        axes[1, 0].plot([u_pos, u_pos], 
                                       [v_sup - cross_size, v_sup + cross_size], 
                                       color=color_sup, linewidth=2)
                        
                        # Draw bottom edge marker (horizontal cross)
                        axes[1, 0].plot([u_pos - cross_size, u_pos + cross_size], 
                                       [v_inf, v_inf], 
                                       color=color_inf, linewidth=2)
                        axes[1, 0].plot([u_pos, u_pos], 
                                       [v_inf - cross_size, v_inf + cross_size], 
                                       color=color_inf, linewidth=2)
                        
                        # Add leaf pair number label
                        label_color = 'white' if 'OK' in status else 'orange'
                        axes[1, 0].text(u_pos, (v_sup + v_inf) / 2, str(pair), 
                                       color=label_color, fontsize=8, fontweight='bold',
                                       ha='center', va='center',
                                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7, edgecolor='none'))
            
            axes[1, 0].set_title('Detected Blade Positions\n(Red = Top Edge | Blue = Bottom Edge)', 
                                fontweight='bold', fontsize=11)
            axes[1, 0].legend()
            
            # 4. Field size plot (for this file only)
            if isinstance(file_specific_results, list) and len(file_specific_results) > 0:
                pairs = []
                field_sizes = []
                statuses = []
                distances_sup = []
                distances_inf = []
                
                for result in file_specific_results:
                    if isinstance(result, (list, tuple)) and len(result) >= 5:
                        pair, dist_sup, dist_inf, field_size, status = result[0], result[1], result[2], result[3], result[4]
                        if field_size is not None and status != 'CLOSED':
                            pairs.append(pair)
                            field_sizes.append(field_size)
                            statuses.append(status)
                            if dist_sup is not None and not np.isnan(dist_sup):
                                distances_sup.append(dist_sup)
                            if dist_inf is not None and not np.isnan(dist_inf):
                                distances_inf.append(dist_inf)
                
                # Separate OK and out-of-tolerance points
                pairs_ok = [pairs[i] for i in range(len(pairs)) if 'OK' in statuses[i]]
                field_sizes_ok = [field_sizes[i] for i in range(len(field_sizes)) if 'OK' in statuses[i]]
                pairs_bad = [pairs[i] for i in range(len(pairs)) if 'OUT_OF_TOLERANCE' in statuses[i]]
                field_sizes_bad = [field_sizes[i] for i in range(len(field_sizes)) if 'OUT_OF_TOLERANCE' in statuses[i]]
                
                # Calculate statistics
                # Calculate average leaf length (distance between sup and inf for each blade)
                leaf_lengths = []
                min_length = min(len(distances_sup), len(distances_inf))
                for i in range(min_length):
                    # Leaf length = distance between top edge and bottom edge
                    leaf_length = abs(distances_sup[i] - distances_inf[i])
                    leaf_lengths.append(leaf_length)
                
                # Calculate average and standard deviation of leaf lengths
                avg_leaf_length = np.mean(leaf_lengths) if leaf_lengths else None
                std_leaf_length = np.std(leaf_lengths) if leaf_lengths else None
                
                avg_field_size = np.mean(field_sizes) if field_sizes else None
                std_field_size = np.std(field_sizes) if field_sizes else None
                
                # Plot tolerance bands
                axes[1, 1].axhline(y=self.analyzer.expected_field_size, color='green', linestyle='-', 
                                  linewidth=2, label=f'Expected ({self.analyzer.expected_field_size}mm)', alpha=0.7)
                axes[1, 1].axhspan(self.analyzer.expected_field_size - self.analyzer.field_size_tolerance, 
                                  self.analyzer.expected_field_size + self.analyzer.field_size_tolerance, 
                                  color='green', alpha=0.1, label=f'Tolerance ±{self.analyzer.field_size_tolerance}mm')
                
                # Plot field sizes
                if pairs_ok:
                    axes[1, 1].plot(pairs_ok, field_sizes_ok, 'go', label='Within Tolerance', markersize=5)
                if pairs_bad:
                    axes[1, 1].plot(pairs_bad, field_sizes_bad, 'ro', label='Out of Tolerance', markersize=7, markeredgewidth=2)
                
                # Add statistics text box
                stats_text = []
                if avg_leaf_length is not None:
                    stats_text.append(f'Longueur Lames - Moyenne: {avg_leaf_length:.3f} mm')
                    stats_text.append(f'Longueur Lames - Écart-type: {std_leaf_length:.3f} mm')
                
                if stats_text:
                    axes[1, 1].text(0.02, 0.98, '\n'.join(stats_text),
                                   transform=axes[1, 1].transAxes,
                                   fontsize=9,
                                   verticalalignment='top',
                                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                
                axes[1, 1].set_xlabel('Blade Pair Number')
                axes[1, 1].set_ylabel('Field Size (mm)')
                axes[1, 1].set_title(f'Field Size per Blade Pair (Expected: {self.analyzer.expected_field_size}±{self.analyzer.field_size_tolerance}mm)', 
                                    fontweight='bold')
                axes[1, 1].legend(loc='upper right')
                axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert plot to PNG image in memory
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            
            # Encode as base64
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            # Calculate statistics for this specific file
            file_stats = self._calculate_file_statistics(file_specific_results)
            
            # Store visualization with file info and statistics
            filename = os.path.basename(filepath)
            self.visualizations.append({
                'name': f'Image {file_index + 1}: {filename}',
                'type': 'image',
                'data': f'data:image/png;base64,{image_base64}',
                'filename': filename,
                'index': file_index,
                'statistics': file_stats
            })
            
            logger.info(f"Visualization generated for {filename}")
            
        except Exception as e:
            logger.error(f"Error generating visualization for {filepath}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _calculate_file_statistics(self, file_results):
        """Calculate statistics for a single file's results"""
        stats = {
            'total_blades': 0,
            'ok_blades': 0,
            'out_of_tolerance': 0,
            'closed_blades': 0,
            'status': 'PASS'  # Overall status for this file
        }
        
        if not isinstance(file_results, list):
            return stats
        
        stats['total_blades'] = len(file_results)
        
        for result in file_results:
            if isinstance(result, (list, tuple)) and len(result) >= 5:
                status = result[4]
                if status == 'OK':
                    stats['ok_blades'] += 1
                elif 'OUT_OF_TOLERANCE' in str(status):
                    stats['out_of_tolerance'] += 1
                    stats['status'] = 'FAIL'  # Set to FAIL if any blade is out of tolerance
                elif status == 'CLOSED':
                    stats['closed_blades'] += 1
        
        return stats
    
    def _process_results(self):
        """Process the MLC analysis results and convert to test format"""
        logger.info(f"Processing results: {type(self.analyzer_results)}")
        if hasattr(self.analyzer_results, '__len__') and len(self.analyzer_results) > 0:
            logger.info(f"First result item: {type(self.analyzer_results[0]) if len(self.analyzer_results) > 0 else 'empty'}")
            if len(self.analyzer_results) > 0:
                logger.info(f"First result content: {self.analyzer_results[0]}")
        
        # Add image name and acquisition date for each processed file
        for file_idx, file_result in enumerate(self.file_results):
            filename = os.path.basename(file_result['file'])
            acq_date = file_result.get('acquisition_date', 'Unknown')
            analysis_type = file_result.get('analysis_type', 'unknown')
            
            # Add a header result for this image
            self.add_result(
                name=f"Image {file_idx + 1}: {filename}",
                value=f"Acquisition: {acq_date}",
                status="INFO",
                unit="",
                tolerance=f"Analysis Type: {analysis_type.replace('_', ' ').title()}"
            )
        
        if not self.analyzer_results:
            self.add_result(
                name="analysis_result",
                value="No results",
                status="FAIL",
                tolerance="Valid analysis required"
            )
            return
        
        # Handle different result formats
        if isinstance(self.analyzer_results, list):
            # Batch results - list of blade measurements
            total_blades = len(self.analyzer_results)
            ok_blades = 0
            out_of_tolerance = 0
            closed_blades = 0
            
            # Collect blade positions for statistics
            distances_sup = []  # Top edge distances
            distances_inf = []  # Bottom edge distances
            field_sizes = []    # Field sizes
            
            # Safely process each result item
            for i, r in enumerate(self.analyzer_results):
                try:
                    logger.info(f"Processing result {i}: {type(r)} = {r}")
                    
                    if isinstance(r, (list, tuple)) and len(r) > 4:
                        status = r[4]
                        if status == 'OK':
                            ok_blades += 1
                        elif 'OUT_OF_TOLERANCE' in str(status):
                            out_of_tolerance += 1
                        elif status == 'CLOSED':
                            closed_blades += 1
                        
                        # Collect position data (skip closed blades)
                        if status != 'CLOSED' and len(r) >= 4:
                            dist_sup = r[1]  # Distance superior (top edge)
                            dist_inf = r[2]  # Distance inferior (bottom edge)
                            field_size = r[3]  # Field size
                            
                            if dist_sup is not None and not np.isnan(dist_sup):
                                distances_sup.append(dist_sup)
                            if dist_inf is not None and not np.isnan(dist_inf):
                                distances_inf.append(dist_inf)
                            if field_size is not None and not np.isnan(field_size):
                                field_sizes.append(field_size)
                                
                    elif isinstance(r, dict):
                        # Handle dictionary format
                        status = r.get('status', 'UNKNOWN')
                        if status == 'OK':
                            ok_blades += 1
                        elif 'OUT_OF_TOLERANCE' in str(status):
                            out_of_tolerance += 1
                        elif status == 'CLOSED':
                            closed_blades += 1
                    else:
                        logger.warning(f"Unexpected result format for item {i}: {type(r)} = {r}")
                        
                except Exception as e:
                    logger.error(f"Error processing result item {i}: {e}")
                    continue
            
            # Store detailed results
            self.detailed_results = self.analyzer_results
            
        else:
            # Single file result or other format
            self.add_result(
                name="analysis_completed",
                value="Yes",
                status="PASS",
                tolerance="Successful analysis"
            )
    
    def get_form_data(self):
        """
        Get the form structure for frontend implementation
        
        Returns:
            dict: Form configuration
        """
        return {
            'title': 'ANSM - MLC Leaf and Jaw - Analyse DICOM',
            'description': 'Test d\'exactitude des positions de lames MLC à partir d\'images DICOM',
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
                    'label': 'Fichiers DICOM:',
                    'type': 'file',
                    'required': True,
                    'accept': '.dcm',
                    'multiple': True,
                    'description': 'Sélectionner un ou plusieurs fichiers DICOM (.dcm)'
                }
            ],
            'tolerance': 'Analyse des positions de lames selon les spécifications ANSM',
            'file_upload': True  # Special flag for file upload handling
        }
    
    def get_detailed_results(self):
        """
        Get detailed MLC blade results
        
        Returns:
            dict: Detailed blade analysis results
        """
        if not hasattr(self, 'detailed_results'):
            return {}
        
        if isinstance(self.detailed_results, list):
            # Format blade results for display
            blade_results = []
            for i, result in enumerate(self.detailed_results):
                if len(result) >= 5:
                    blade_results.append({
                        'blade_pair': result[0],
                        'distance_sup_mm': round(result[1], 3) if result[1] is not None else None,
                        'distance_inf_mm': round(result[2], 3) if result[2] is not None else None,
                        'field_size_mm': round(result[3], 3) if result[3] is not None else None,
                        'status': result[4]
                    })
            
            return {
                'blade_results': blade_results,
                'total_blades': len(blade_results),
                'summary': {
                    'ok': sum(1 for r in blade_results if r['status'] == 'OK'),
                    'out_of_tolerance': sum(1 for r in blade_results if 'OUT_OF_TOLERANCE' in str(r['status'])),
                    'closed': sum(1 for r in blade_results if r['status'] == 'CLOSED')
                }
            }
        
        return {'message': 'Single file analysis completed'}
    
    def to_dict(self):
        """Override to_dict to include visualizations and file results"""
        import numpy as np
        
        def convert_to_json_serializable(obj):
            """Convert numpy/other types to JSON-serializable Python types"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_json_serializable(item) for item in obj]
            else:
                return obj
        
        result = super().to_dict()
        
        # Add filenames at top level for easy database storage
        if self.dicom_files:
            result['filenames'] = [os.path.basename(f) for f in self.dicom_files]
        
        # Add visualizations to the output
        if self.visualizations:
            result['visualizations'] = self.visualizations
        
        # Add file_results for detailed per-image data (convert to JSON-serializable)
        if hasattr(self, 'file_results'):
            result['file_results'] = convert_to_json_serializable(self.file_results)
        
        return result


# Convenience function for standalone use
def test_mlc_leaf_jaw(files: List[str], operator: str, test_date: Optional[datetime] = None):
    """
    Standalone function to test MLC leaf and jaw positions
    
    Args:
        files: List of DICOM file paths
        operator: Name of the operator performing the test
        test_date: Date of the test (defaults to current date)
    
    Returns:
        dict: Test results
    """
    test = MLCLeafJawTest()
    return test.execute(files, operator, test_date)