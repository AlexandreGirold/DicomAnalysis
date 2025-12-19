"""
CQ Exactitude des positions de lames (paire 25 à paire 56)

This control is performed for fields at the axis of 20x200mm
The analysis is done according to field edge detection because FFF (50% not applicable)
The macro needs to be corrected if the calibration file for the MV isocenter is modified
"""

import os
import numpy as np
import pydicom
from scipy import ndimage
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web server
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sys

# Add parent directory to path for database import
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import sys
import os
# Add backend root to path for mv_center_utils import
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_root)

from mv_center_utils import get_mv_center

# Conditional import of tkinter (only needed for standalone GUI mode)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class MLCBladeAnalyzer:
    def __init__(self, testing_folder=None, gui_mode=False):
        # Default values (will be updated from DICOM metadata)
        self.pixel_size = 0.216  # mm - Pixel size at isocenter (default, will be calculated from DICOM)
        self.center_u, self.center_v = get_mv_center()
        self.blade_width_pixels = 33.25  # 1 blade = 7.18mm = 33.2 pixels (will be recalculated)
        self.blade_width_iso = 7.18  # mm - blade width at isocenter (FIXED specification)
        self.testing_folder = testing_folder if testing_folder else r"C:\Users\agirold\Desktop\testing"  # Optional: preset folder path
        self.gui_mode = gui_mode  # Flag to enable/disable GUI dialogs
        
        # DICOM metadata (will be populated when loading image)
        self.SAD = None  # Source to Axis Distance (isocenter)
        self.SID = None  # Source to Image Distance
        self.scaling_factor = None  # Geometric scaling factor
        self.pixel_spacing_x = None  # mm per pixel at image plane
        self.pixel_spacing_y = None  # mm per pixel at image plane
        
        # Tolerance settings (user-adjustable)
        self.expected_field_size = 40.0  # mm - Expected field size when fully open
        self.field_size_tolerance = 1.0  # mm - Tolerance for field size
        self.edge_detection_threshold = 0.5  # 0-1: fraction of max-min for edge detection (0.5 = median)
        self.min_blade_separation = 23  # pixels - minimum separation between opposing blades (~5mm) previously 23
        
    def show_warning(self):
        """Show warning dialog"""
        if not self.gui_mode or not TKINTER_AVAILABLE:
            print("Warning: Attention: la macro va fermer toutes les images ouvertes!")
            return
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Warning!",
            "Attention: la macro va fermer toutes les images ouvertes!\n"
        )
        root.destroy()
    

    
    def select_dicom_directory(self):
        """Open dialog to select DICOM directory"""
        # If testing_folder is provided, use it directly
        if self.testing_folder and os.path.isdir(self.testing_folder):
            print(f"Using preset folder: {self.testing_folder}")
            return self.testing_folder
        
        if not self.gui_mode or not TKINTER_AVAILABLE:
            print("Error: No testing folder provided and GUI mode is disabled")
            return None
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Ouverture image DICOM",
            "Selectionner le dossier de l'acquisition à contrôler\n"
        )
        dicom_dir = filedialog.askdirectory(title="Select a Directory")
        root.destroy()
        return dicom_dir
    
    def load_dicom_image(self, filepath):
        """Load DICOM image and return pixel array and DICOM dataset"""
        try:
            ds = pydicom.dcmread(filepath)
            image = ds.pixel_array.astype(np.float32)
            return image, ds
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None
    
    def get_dicom_datetime(self, ds):
        """Extract creation date and time from DICOM dataset"""
        try:
            # Try to get ContentDate and ContentTime first (most reliable for images)
            if hasattr(ds, 'ContentDate') and hasattr(ds, 'ContentTime'):
                date_str = ds.ContentDate
                time_str = ds.ContentTime
            # Fallback to AcquisitionDate and AcquisitionTime
            elif hasattr(ds, 'AcquisitionDate') and hasattr(ds, 'AcquisitionTime'):
                date_str = ds.AcquisitionDate
                time_str = ds.AcquisitionTime
            # Fallback to StudyDate and StudyTime
            elif hasattr(ds, 'StudyDate') and hasattr(ds, 'StudyTime'):
                date_str = ds.StudyDate
                time_str = ds.StudyTime
            else:
                return None
            
            # Parse date (YYYYMMDD) and time (HHMMSS.ffffff)
            from datetime import datetime
            datetime_str = f"{date_str}{time_str.split('.')[0]}"  # Remove fractional seconds
            dt = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            return dt
        except Exception as e:
            print(f"Error extracting datetime: {e}")
            return None
    
    def invert_image(self, image):
        """Invert image (equivalent to ImageJ Invert)"""
        max_val = np.max(image)
        return max_val - image
    
    def find_edges(self, image):
        """Apply edge detection using first derivative (gradient)"""
        # Using first derivative for edge detection
        grad_x = np.gradient(image, axis=1)  # First derivative in x direction
        grad_y = np.gradient(image, axis=0)  # First derivative in y direction
        edges = np.hypot(grad_x, grad_y)     # Magnitude of first derivatives
        return edges
    
    def analyze_blade_positions(self, image, start_u, end_u, step, initial_pair):
        """
        Analyze blade positions in one direction
        
        Args:
            image: Edge-detected image
            start_u: Starting u coordinate
            end_u: Ending u coordinate
            step: Step size (positive or negative)
            initial_pair: Initial blade pair number
        
        Returns:
            List of tuples (blade_pair, distance_sup, distance_inf, detected_points)
        """
        results = []
        all_detected_points = []  # Store all detected points for visualization
        
        # Define ROI for measurements
        roi = image[437:867, 5:1023]  # (v, u) - excluding 5px borders
        max_val = np.max(roi)
        min_val = np.min(roi)
        median_val = min_val + (max_val - min_val) * self.edge_detection_threshold
        
        print("Lames\tDistance_Sup\tDistance_Inf\tField_Size\tStatus")
        
        # Calculate blade positions
        if step > 0:
            u_positions = np.arange(start_u, end_u, step)
        else:
            u_positions = np.arange(start_u, end_u, step)
        
        pair_lame = initial_pair
        
        for u in u_positions:
            u = int(u)
            tab_coord_v = []
            tab_coord_u = []
            tab_ng = []
            
            i = 0
            stop_max = 0
            precedent = 0
            
            # Search in vertical direction
            for v in range(427, 867):
                somme = 0
                ng_sum = 0
                
                # Average over blade width
                for w in range(u, min(u + 30, image.shape[1])):
                    if w < image.shape[1] and v < image.shape[0]:
                        ng_sum += image[v, w]
                        somme += 1
                
                if somme > 0:
                    ng = ng_sum / somme
                else:
                    ng = 0
                
                # Case 1: Gray level increases (max not reached)
                if ng > precedent and ng > median_val:
                    stop_max = 2
                
                # Case 2: Gray level decreases (local max reached)
                if ng < precedent and ng > median_val and stop_max > 1:
                    if i > 0:
                        j = i - 1
                        delta = v - tab_coord_v[j]
                        
                        if delta > self.min_blade_separation:  # minimum separation between 2 opposing blades
                            tab_coord_v.append(v - 1)
                            tab_coord_u.append(pair_lame)
                            tab_ng.append(precedent)
                            i += 1
                            stop_max = 1
                        elif delta < 24:  # 2 local maxima, choose the highest
                            if ng > tab_ng[j]:
                                tab_coord_v[j] = v - 1
                                tab_coord_u[j] = pair_lame
                                tab_ng[j] = precedent
                                stop_max = 1
                    else:
                        tab_coord_v.append(v - 1)
                        tab_coord_u.append(pair_lame)
                        tab_ng.append(precedent)
                        i += 1
                        stop_max = 1
                
                precedent = ng
            
            # Calculate distances from center
            if i < 3 and len(tab_coord_v) >= 2:
                distance_t = (self.center_v - tab_coord_v[0]) * self.pixel_size
                distance_p = (self.center_v - tab_coord_v[1]) * self.pixel_size
                
                # Calculate field size (distance between superior and inferior edges)
                field_size = abs(distance_t - distance_p)
                
                # Check if field size matches any valid size (20, 30, or 40mm) within tolerance
                valid_field_sizes = [20.0, 30.0, 40.0]
                tolerance = self.field_size_tolerance
                
                is_valid = False
                closest_size = None
                min_diff = float('inf')
                
                for valid_size in valid_field_sizes:
                    diff = abs(field_size - valid_size)
                    if diff < min_diff:
                        min_diff = diff
                        closest_size = valid_size
                    if diff <= tolerance:
                        is_valid = True
                        break
                
                if is_valid:
                    status = "OK"
                else:
                    status = f"OUT_OF_TOLERANCE (closest to {closest_size}mm, off by {min_diff:.1f}mm)"
                
                print(f"{pair_lame}\t{distance_t:.3f}\t{distance_p:.3f}\t{field_size:.3f}\t{status}")
                
                # Store detected points for visualization
                detected_points = {
                    'pair': pair_lame,
                    'u': u,
                    'v_sup': tab_coord_v[0],
                    'v_inf': tab_coord_v[1],
                    'distance_sup': distance_t,
                    'distance_inf': distance_p,
                    'field_size': field_size,
                    'status': status
                }
                all_detected_points.append(detected_points)
                results.append((pair_lame, distance_t, distance_p, field_size, status, detected_points))
            elif i == 0 or len(tab_coord_v) < 2:
                # Leaf is closed or not detected
                print(f"{pair_lame}\t-\t-\t-\tCLOSED/NOT_DETECTED")
                detected_points = {
                    'pair': pair_lame,
                    'u': u,
                    'v_sup': None,
                    'v_inf': None,
                    'distance_sup': None,
                    'distance_inf': None,
                    'field_size': None,
                    'status': 'CLOSED'
                }
                all_detected_points.append(detected_points)
                results.append((pair_lame, None, None, None, 'CLOSED', detected_points))
            elif i > 2:
                print(f"{pair_lame}\t-\t-\t-\tERROR_MULTIPLE_DETECTIONS")
            
            if step > 0:
                pair_lame += 1
            else:
                pair_lame -= 1
        
        return results, all_detected_points
    
    def visualize_detection(self, original_image, edges, detected_points_a, detected_points_b, filename):
        """Create visualization of blade detection"""
        fig, axes = plt.subplots(2, 2, figsize=(18, 14))
        
        # 1. Detected blades on original
        axes[0, 0].imshow(original_image, cmap='gray', alpha=0.7)
        axes[0, 0].axhline(y=self.center_v, color='cyan', linestyle='--', linewidth=1, label='Center V')
        axes[0, 0].axvline(x=self.center_u, color='cyan', linestyle='--', linewidth=1, label='Center U')
        
        # Plot detected points for section A
        for point in detected_points_a:
            if point['status'] == 'CLOSED':
                # Mark closed blades with an X
                axes[0, 0].plot(point['u'], self.center_v, 'kx', markersize=8, markeredgewidth=2)
                axes[0, 0].text(point['u'], self.center_v-15, f"{point['pair']}\nCLOSED", 
                              color='black', fontsize=5, ha='center', weight='bold')
            elif point['v_sup'] is not None and point['v_inf'] is not None:
                # Color code based on tolerance
                if 'OUT_OF_TOLERANCE' in point['status']:
                    color_sup = 'orange'
                    color_inf = 'orange'
                    marker_size = 6
                else:
                    color_sup = 'red'
                    color_inf = 'green'
                    marker_size = 4
                
                axes[0, 0].plot(point['u'], point['v_sup'], 'o', color=color_sup, markersize=marker_size)
                axes[0, 0].plot(point['u'], point['v_inf'], 'o', color=color_inf, markersize=marker_size)
                
                # Label with blade pair number only (no field size to avoid clutter)
                label_text = f"{point['pair']}"
                if 'OUT_OF_TOLERANCE' in point['status']:
                    axes[0, 0].text(point['u'], point['v_sup']-10, label_text, 
                                  color='orange', fontsize=6, ha='center', weight='bold')
                else:
                    axes[0, 0].text(point['u'], point['v_sup']-10, label_text, 
                                  color='red', fontsize=6, ha='center')
        
        # Plot detected points for section B
        for point in detected_points_b:
            if point['status'] == 'CLOSED':
                # Mark closed blades with an X
                axes[0, 0].plot(point['u'], self.center_v, 'kx', markersize=8, markeredgewidth=2)
                axes[0, 0].text(point['u'], self.center_v-15, f"{point['pair']}\nCLOSED", 
                              color='black', fontsize=5, ha='center', weight='bold')
            elif point['v_sup'] is not None and point['v_inf'] is not None:
                # Color code based on tolerance
                if 'OUT_OF_TOLERANCE' in point['status']:
                    color_sup = 'orange'
                    color_inf = 'orange'
                    marker_size = 6
                else:
                    color_sup = 'red'
                    color_inf = 'green'
                    marker_size = 4
                
                axes[0, 0].plot(point['u'], point['v_sup'], 'o', color=color_sup, markersize=marker_size)
                axes[0, 0].plot(point['u'], point['v_inf'], 'o', color=color_inf, markersize=marker_size)
                
                # Label with blade pair number only (no field size to avoid clutter)
                label_text = f"{point['pair']}"
                if 'OUT_OF_TOLERANCE' in point['status']:
                    axes[0, 0].text(point['u'], point['v_sup']-10, label_text, 
                                  color='orange', fontsize=6, ha='center', weight='bold')
                else:
                    axes[0, 0].text(point['u'], point['v_sup']-10, label_text, 
                                  color='red', fontsize=6, ha='center')
        
        axes[0, 0].set_title('Detected Blade Positions\n(Red/Green: OK, Orange: Out of Tolerance, Black X: Closed)', fontweight='bold')
        axes[0, 0].legend()
        
        # 2. Coordinates Table (Top half - Blades 27-40)
        axes[0, 1].axis('off')
        all_points = detected_points_a + detected_points_b
        all_points_sorted = sorted(all_points, key=lambda x: x['pair'])
        
        # Split data into two tables
        mid_point = len(all_points_sorted) // 2
        table_data_1 = []
        for point in all_points_sorted[:mid_point]:
            if point['field_size'] is not None:
                table_data_1.append([
                    f"{point['pair']}",
                    f"{point['v_sup']:.0f}" if point['v_sup'] else "—",
                    f"{point['v_inf']:.0f}" if point['v_inf'] else "—",
                    f"{point['distance_sup']:.2f}" if point['distance_sup'] else "—",
                    f"{point['distance_inf']:.2f}" if point['distance_inf'] else "—",
                    f"{point['field_size']:.2f}",
                    "✓" if 'OK' in point['status'] else "✗"
                ])
            else:
                table_data_1.append([
                    f"{point['pair']}", "—", "—", "—", "—", "CLOSED", "—"
                ])
        
        table1 = axes[0, 1].table(cellText=table_data_1,
                                  colLabels=['Blade', 'V_sup\n(px)', 'V_inf\n(px)', 'Top\n(mm)', 'Bottom\n(mm)', 'Size\n(mm)', 'OK'],
                                  cellLoc='center',
                                  loc='center',
                                  colWidths=[0.12, 0.15, 0.15, 0.15, 0.15, 0.15, 0.08])
        table1.auto_set_font_size(False)
        table1.set_fontsize(7)
        table1.scale(1, 1.5)
        
        # Color code the status column
        for i, point in enumerate(all_points_sorted[:mid_point]):
            if point['field_size'] is not None:
                if 'OK' in point['status']:
                    table1[(i+1, 6)].set_facecolor('#90EE90')  # Light green
                else:
                    table1[(i+1, 6)].set_facecolor('#FFB6C6')  # Light red
        
        axes[0, 1].set_title('Blade Coordinates (Part 1)', fontweight='bold')
        
        # 3. Coordinates Table (Bottom half - Blades 41-54)
        axes[1, 0].axis('off')
        table_data_2 = []
        for point in all_points_sorted[mid_point:]:
            if point['field_size'] is not None:
                table_data_2.append([
                    f"{point['pair']}",
                    f"{point['v_sup']:.0f}" if point['v_sup'] else "—",
                    f"{point['v_inf']:.0f}" if point['v_inf'] else "—",
                    f"{point['distance_sup']:.2f}" if point['distance_sup'] else "—",
                    f"{point['distance_inf']:.2f}" if point['distance_inf'] else "—",
                    f"{point['field_size']:.2f}",
                    "✓" if 'OK' in point['status'] else "✗"
                ])
            else:
                table_data_2.append([
                    f"{point['pair']}", "—", "—", "—", "—", "CLOSED", "—"
                ])
        
        table2 = axes[1, 0].table(cellText=table_data_2,
                                  colLabels=['Blade', 'V_sup\n(px)', 'V_inf\n(px)', 'Top\n(mm)', 'Bottom\n(mm)', 'Size\n(mm)', 'OK'],
                                  cellLoc='center',
                                  loc='center',
                                  colWidths=[0.12, 0.15, 0.15, 0.15, 0.15, 0.15, 0.08])
        table2.auto_set_font_size(False)
        table2.set_fontsize(7)
        table2.scale(1, 1.5)
        
        # Color code the status column
        for i, point in enumerate(all_points_sorted[mid_point:]):
            if point['field_size'] is not None:
                if 'OK' in point['status']:
                    table2[(i+1, 6)].set_facecolor('#90EE90')  # Light green
                else:
                    table2[(i+1, 6)].set_facecolor('#FFB6C6')  # Light red
        
        axes[1, 0].set_title('Blade Coordinates (Part 2)', fontweight='bold')
        
        # 4. Field size plot with tolerance bands
        pairs = [p['pair'] for p in all_points_sorted if p['field_size'] is not None]
        field_sizes = [p['field_size'] for p in all_points_sorted if p['field_size'] is not None]
        statuses = [p['status'] for p in all_points_sorted if p['field_size'] is not None]
        
        # Separate OK and out-of-tolerance points
        pairs_ok = [pairs[i] for i in range(len(pairs)) if 'OK' in statuses[i]]
        field_sizes_ok = [field_sizes[i] for i in range(len(field_sizes)) if 'OK' in statuses[i]]
        pairs_bad = [pairs[i] for i in range(len(pairs)) if 'OUT_OF_TOLERANCE' in statuses[i]]
        field_sizes_bad = [field_sizes[i] for i in range(len(field_sizes)) if 'OUT_OF_TOLERANCE' in statuses[i]]
        
        # Plot tolerance bands for valid field sizes (20, 30, 40mm)
        valid_field_sizes = [20.0, 30.0, 40.0]
        tolerance = self.field_size_tolerance
        colors = ['blue', 'purple', 'green']
        
        for valid_size, color in zip(valid_field_sizes, colors):
            axes[1, 1].axhline(y=valid_size, color=color, linestyle='-', linewidth=1.5, alpha=0.7)
            axes[1, 1].axhspan(valid_size - tolerance, valid_size + tolerance, 
                              color=color, alpha=0.05)
        
        # Add legend for tolerance bands
        axes[1, 1].text(0.02, 0.98, f'Valid sizes: 20mm, 30mm, 40mm (±{tolerance}mm)', 
                       transform=axes[1, 1].transAxes, fontsize=9, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # Plot field sizes
        if pairs_ok:
            axes[1, 1].plot(pairs_ok, field_sizes_ok, 'go', label='Within Tolerance', markersize=5)
        if pairs_bad:
            axes[1, 1].plot(pairs_bad, field_sizes_bad, 'ro', label='Out of Tolerance', markersize=7, markeredgewidth=2)
        
        axes[1, 1].set_xlabel('Blade Pair Number')
        axes[1, 1].set_ylabel('Field Size (mm)')
        axes[1, 1].set_title(f'Field Size per Blade Pair (Valid: 20mm, 30mm, 40mm ±{tolerance}mm)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # Add closed blades markers on x-axis
        closed_pairs = [p['pair'] for p in all_points_sorted if p['status'] == 'CLOSED']
        if closed_pairs:
            for cp in closed_pairs:
                axes[1, 1].axvline(x=cp, color='black', linestyle=':', alpha=0.3, linewidth=1)
        
        plt.tight_layout()
        
        # Save figure
        output_filename = f"blade_detection_{os.path.splitext(filename)[0]}.png"
        plt.savefig(output_filename, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {output_filename}")
        
        # Only show plot in GUI mode
        if self.gui_mode:
            plt.show()
        else:
            plt.close()  # Close the figure to free memory
    
    def process_image(self, filepath):
        """Process a single DICOM image"""
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(filepath)}")
        print(f"{'='*60}")
        
        # Load image and DICOM dataset
        original_image, ds = self.load_dicom_image(filepath)
        if original_image is None:
            return None
        
        # Invert image
        image = self.invert_image(original_image)
        
        # Find edges
        edges = self.find_edges(image)
        
        # Analyze blade positions (3-A) from pair 41 to 54
        print("\n--- Section 3-A: Blades from pair 41 to 54 ---")
        results_a, detected_points_a = self.analyze_blade_positions(
            edges,
            start_u=511,
            end_u=511 + (54 - 41 + 1) * self.blade_width_pixels,  
            step=self.blade_width_pixels,
            initial_pair=41
        )
        
        # Analyze blade positions (3-B) from pair 40 to 27
        print("\n--- Section 3-B: Blades from pair 40 to 27 ---")
        results_b, detected_points_b = self.analyze_blade_positions(
            edges,
            start_u=511 - self.blade_width_pixels,  # Start at blade 40 position (one blade to the left of 41)
            end_u=511 - self.blade_width_pixels - (40 - 27 + 1) * self.blade_width_pixels,
            step=-self.blade_width_pixels,
            initial_pair=40
        )
        
        # Create visualization
        self.visualize_detection(original_image, edges, detected_points_a, detected_points_b, 
                                os.path.basename(filepath))
        
        return results_a + results_b
    
    def run(self):
        """Main execution method"""
        from datetime import datetime
        
        # Select DICOM directory
        dicom_dir = self.select_dicom_directory()
        if not dicom_dir:
            print("No directory selected. Exiting.")
            return
        
        # Get list of files with their datetime
        file_datetime_list = []
        
        for filename in os.listdir(dicom_dir):
            filepath = os.path.join(dicom_dir, filename)
            if os.path.isfile(filepath):
                try:
                    # Read DICOM to get datetime
                    ds = pydicom.dcmread(filepath)
                    dt = self.get_dicom_datetime(ds)
                    if dt:
                        file_datetime_list.append((filepath, dt, filename))
                        print(f"Found: {filename} - {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        print(f"Warning: Could not extract datetime from {filename}")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        if not file_datetime_list:
            print("No valid DICOM files found with datetime information.")
            return
        
        # Check if all files are from the same day
        dates = [dt.date() for _, dt, _ in file_datetime_list]
        unique_dates = set(dates)
        
        if len(unique_dates) > 1:
            print(f"\n{'='*60}")
            print("ERROR: Files are from different days!")
            print(f"{'='*60}")
            for date in sorted(unique_dates):
                count = dates.count(date)
                print(f"  {date}: {count} file(s)")
            print(f"{'='*60}")
            print("All files must be from the same day. Exiting.")
            return
        
        # Sort files by datetime (oldest first)
        file_datetime_list.sort(key=lambda x: x[1])
        
        print(f"\n{'='*60}")
        print(f"Processing {len(file_datetime_list)} files from {file_datetime_list[0][1].strftime('%Y-%m-%d')}")
        print("Files will be processed in chronological order (oldest first):")
        print(f"{'='*60}")
        for i, (_, dt, filename) in enumerate(file_datetime_list, 1):
            print(f"  {i}. {filename} - {dt.strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        all_results = []
        
        # Process each file in chronological order
        for filepath, dt, filename in file_datetime_list:
            try:
                print(f"\n[{dt.strftime('%H:%M:%S')}] Processing {filename}...")
                results = self.process_image(filepath)
                if results:
                    all_results.extend(results)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        
        print("\n=== Analysis Complete ===")
        return all_results


def main():
    """Main entry point"""
    # Use the testing folder path directly
    testing_folder = r"c:\Users\agirold\Desktop\testing"
    
    print(f"Using testing folder: {testing_folder}")
    
    analyzer = MLCBladeAnalyzer(testing_folder=testing_folder)
    results = analyzer.run()
    
    # Print summary
    if results:
        total_blades = len(results)
        closed_blades = sum(1 for r in results if r[4] == 'CLOSED')
        out_of_tolerance = sum(1 for r in results if r[4] and 'OUT_OF_TOLERANCE' in r[4])
        ok_blades = sum(1 for r in results if r[4] == 'OK')
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"{'='*60}")
        print(f"Total blade pairs analyzed: {total_blades}")
        print(f"OK (within tolerance):      {ok_blades}")
        print(f"Out of tolerance:           {out_of_tolerance}")
        print(f"Closed/Not detected:        {closed_blades}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()