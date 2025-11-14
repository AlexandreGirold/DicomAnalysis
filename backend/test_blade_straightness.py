"""
Standalone test for blade straightness (90° alignment)
Analyzes the middle position between opposing leaf edges for each open blade
Tests if each blade is straight (perpendicular to beam axis at 90°)
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pydicom
from scipy.signal import find_peaks
from scipy import ndimage

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))
from leaf_pos import MLCBladeAnalyzer


def detect_blade_midline(edges, u_pos, center_v, blade_width, binary_image=None):
    """
    Detect the midline between opposing blade edges and check if it's perpendicular (90°)
    Uses 50% threshold: pixels 50% black or darker are considered black
    Returns the midline coordinates, straightness score, and actual angle
    """
    # Sample region around blade position
    v_start = int(center_v - 200)  # Increased search range
    v_end = int(center_v + 200)
    
    if v_start < 0:
        v_start = 0
    if v_end >= edges.shape[0]:
        v_end = edges.shape[0] - 1
    if u_pos < 0 or u_pos >= edges.shape[1]:
        return None, None, None, False
    
    # Sample larger horizontal region around blade
    window = 15  # Increased window size
    u_start = max(0, u_pos - window)
    u_end = min(edges.shape[1], u_pos + window)
    
    # Find the midline by detecting the gap between opposing blade edges
    midline_points_u = []  # horizontal positions of midline
    midline_points_v = []  # vertical positions of midline
    
    # Get the original image intensity profile to help detect gaps
    # Sample vertically to find midline at each level
    for v in range(v_start, v_end, 3):  # Sample every 3 pixels for better coverage
        if v < 0 or v >= edges.shape[0]:
            continue
            
        # Get horizontal profile at this vertical position
        h_profile = edges[v, u_start:u_end]
        
        # Also get binary profile for clearer gap detection
        if binary_image is not None:
            h_binary = binary_image[v, u_start:u_end]
        else:
            h_binary = h_profile
        
        if len(h_profile) < 5:
            continue
        
        # Apply light smoothing to reduce noise but preserve edges
        from scipy import ndimage
        h_smooth = ndimage.gaussian_filter1d(h_profile, sigma=0.8)
        h_binary_smooth = ndimage.gaussian_filter1d(h_binary, sigma=0.5) if binary_image is not None else h_smooth
        
        # Look for the gap pattern using 50% threshold logic
        # In binary image: 0 = black (blade material), 1 = white (gap/air)
        # Gap should have higher values (closer to 1), blade edges should have lower values (closer to 0)
        
        profile_length = len(h_smooth)
        center_idx = profile_length // 2
        
        # Check multiple methods to find the gap center
        gap_candidates = []
        
        # Method 1: Maximum in binary image (brightest = biggest gap)
        if binary_image is not None:
            max_idx = np.argmax(h_binary_smooth)
            gap_candidates.append(max_idx)
        
        # Method 2: Minimum in edge image (least edges = center of gap)
        min_idx = np.argmin(h_smooth)
        gap_candidates.append(min_idx)
        
        # Method 3: Find region above 50% threshold and take its center
        if binary_image is not None:
            threshold_50 = 0.5
            above_threshold = h_binary_smooth > threshold_50
            if np.any(above_threshold):
                threshold_indices = np.where(above_threshold)[0]
                center_of_threshold = int(np.mean(threshold_indices))
                gap_candidates.append(center_of_threshold)
        
        # Method 4: Look for valley (local minimum with higher values on sides)
        for i in range(2, len(h_smooth) - 2):
            if (h_smooth[i] < h_smooth[i-1] and h_smooth[i] < h_smooth[i+1] and
                h_smooth[i] < h_smooth[i-2] and h_smooth[i] < h_smooth[i+2]):
                gap_candidates.append(i)
        
        # Choose the best candidate (prefer one closest to expected center)
        if gap_candidates:
            # Remove duplicates and find best
            gap_candidates = list(set(gap_candidates))
            if len(gap_candidates) == 1:
                best_gap = gap_candidates[0]
            else:
                # Choose the one closest to center
                distances = [abs(c - center_idx) for c in gap_candidates]
                best_gap = gap_candidates[np.argmin(distances)]
            
            # Verify this is actually a gap using 50% threshold logic
            if binary_image is not None:
                gap_value_binary = h_binary_smooth[best_gap]
                # Gap should be closer to white (1) than black (0)
                if gap_value_binary > 0.3:  # At least 30% white
                    u_midline = u_start + best_gap
                    midline_points_u.append(u_midline)
                    midline_points_v.append(v)
            else:
                # Fallback to edge-based detection
                gap_value = h_smooth[best_gap]
                max_value = np.max(h_smooth)
                if max_value > gap_value * 1.2:
                    u_midline = u_start + best_gap
                    midline_points_u.append(u_midline)
                    midline_points_v.append(v)
    
    # Need at least 3 points for analysis
    if len(midline_points_u) < 3:
        # Try with even more lenient detection
        midline_points_u = []
        midline_points_v = []
        
        for v in range(v_start, v_end, 5):  # Less frequent sampling
            if v < 0 or v >= edges.shape[0]:
                continue
                
            h_profile = edges[v, u_start:u_end]
            if len(h_profile) < 3:
                continue
            
            # Just take the minimum - most lenient approach
            min_idx = np.argmin(h_profile)
            u_midline = u_start + min_idx
            midline_points_u.append(u_midline)
            midline_points_v.append(v)
        
        if len(midline_points_u) < 3:
            return None, None, None, False
    
    # Convert to numpy arrays
    midline_points_u = np.array(midline_points_u)
    midline_points_v = np.array(midline_points_v)
    
    # Calculate straightness - how much the midline deviates horizontally
    u_variation = np.std(midline_points_u)
    is_straight = u_variation < 3.0  # More lenient threshold
    
    # Calculate actual angle of the midline
    # For a perfect 90° blade, the midline should be perfectly vertical (constant u)
    try:
        if len(set(midline_points_u)) > 1:
            # Fit line: u = slope * v + intercept
            # For vertical line, slope should be 0 (no change in u as v changes)
            slope, intercept = np.polyfit(midline_points_v, midline_points_u, 1)
            
            # Calculate angle from vertical
            # slope = du/dv = tan(angle_from_vertical)
            angle_from_vertical_rad = np.arctan(abs(slope))
            angle_from_vertical_deg = np.degrees(angle_from_vertical_rad)
            
            # The actual angle (90° - deviation from vertical)
            actual_angle = 90.0 - angle_from_vertical_deg
            
        else:
            # All u positions are the same - perfectly vertical
            actual_angle = 90.0
            
    except (np.linalg.LinAlgError, ValueError, FloatingPointError):
        # If fitting fails, check variation manually
        if u_variation < 1.0:
            actual_angle = 90.0  # Very close to vertical
        else:
            actual_angle = None  # Unable to determine
    
    return midline_points_v, u_variation, actual_angle, True


def analyze_blade_straightness(filepath):
    """Analyze blade straightness for all blades (alternating open/closed)"""
    print(f"\n{'='*70}")
    print(f"BLADE STRAIGHTNESS ANALYSIS (90° Alignment)")
    print(f"{'='*70}")
    print(f"File: {os.path.basename(filepath)}")
    print(f"Pattern: Alternating (1st=closed, 2nd=open, 3rd=closed, etc.)")
    print(f"{'='*70}\n")
    
    # Create analyzer
    analyzer = MLCBladeAnalyzer(gui_mode=False)
    
    # Load image
    print("Loading DICOM image...")
    original_image, ds = analyzer.load_dicom_image(filepath)
    if original_image is None:
        print("ERROR: Failed to load image")
        return None
    
    print(f"Image loaded: {original_image.shape}")
    
    # Process image
    print("Inverting image...")
    image = analyzer.invert_image(original_image)
    
    # Apply 50% threshold: pixels 50% black or darker = black (0), else white (1)
    print("Applying 50% threshold...")
    threshold_value = 0.5 * np.max(image)  # 50% of maximum intensity
    binary_image = (image > threshold_value).astype(np.float32)
    
    print("Detecting edges...")
    edges = analyzer.find_edges(binary_image)
    
    # Enhance edge detection with additional processing
    edges_enhanced = ndimage.gaussian_filter(edges, sigma=1.0)
    
    # Also use the binary image for gap detection
    binary_enhanced = ndimage.gaussian_filter(binary_image, sigma=0.5)
    
    print("\nAnalyzing blade straightness (checking open blades only)...\n")
    results = []
    all_angles = []  # Collect angles for average calculation
    
    print(f"{'Pair':<6} {'Status':<10} {'U Pos':<8} {'Angle':<12} {'Deviation':<12} {'Result':<15}")
    print("-" * 80)
    
    # Analyze all 28 blade pairs (27-54)
    for idx, pair in enumerate(range(27, 55)):
        # Calculate blade position
        if pair >= 41:
            blade_offset = pair - 41
            u_pos = int(analyzer.center_u + blade_offset * analyzer.blade_width_pixels)
        else:
            blade_offset = 40 - pair
            u_pos = int(analyzer.center_u - (blade_offset + 1) * analyzer.blade_width_pixels)
        
        if u_pos < 0 or u_pos >= image.shape[1]:
            continue
        
        # Determine if blade should be open or closed (alternating pattern)
        # Assuming: odd indices (0, 2, 4...) = closed, even indices (1, 3, 5...) = open
        is_expected_open = (idx % 2) == 1
        
        if is_expected_open:
            # Analyze this blade
            midline_coords, straightness_score, actual_angle, edges_detected = detect_blade_midline(
                edges_enhanced, u_pos, analyzer.center_v, analyzer.blade_width_pixels, binary_enhanced
            )
            
            if edges_detected and straightness_score is not None:
                status = "OPEN"
                is_straight = straightness_score < 2.0
                result = "✓ STRAIGHT" if is_straight else "✗ BENT"
                deviation = f"{straightness_score:.2f}px"
                
                # Display actual angle
                if actual_angle is not None:
                    angle_str = f"{actual_angle:.2f}°"
                    all_angles.append(actual_angle)  # Collect for average
                else:
                    angle_str = "N/A"
                
                print(f"{pair:<6} {status:<10} {u_pos:<8} {angle_str:<12} {deviation:<12} {result:<15}")
                
                results.append({
                    'pair': pair,
                    'u_pos': u_pos,
                    'status': 'open',
                    'expected_open': True,
                    'midline_coords': midline_coords,
                    'straightness_score': straightness_score,
                    'actual_angle': actual_angle,
                    'is_straight': is_straight,
                    'edges_detected': True
                })
            else:
                status = "OPEN"
                result = "? NO EDGES"
                print(f"{pair:<6} {status:<10} {u_pos:<8} {'-':<12} {'-':<12} {result:<15}")
                
                results.append({
                    'pair': pair,
                    'u_pos': u_pos,
                    'status': 'open',
                    'expected_open': True,
                    'midline_coords': None,
                    'straightness_score': None,
                    'actual_angle': None,
                    'is_straight': False,
                    'edges_detected': False
                })
        else:
            # Expected closed
            print(f"{pair:<6} {'CLOSED':<10} {u_pos:<8} {'-':<12} {'-':<12} {'○ CLOSED':<15}")
            
            results.append({
                'pair': pair,
                'u_pos': u_pos,
                'status': 'closed',
                'expected_open': False,
                'midline_coords': None,
                'straightness_score': None,
                'actual_angle': None,
                'is_straight': None,
                'edges_detected': False
            })
    
    # Calculate statistics
    open_blades = [r for r in results if r['status'] == 'open']
    closed_blades = [r for r in results if r['status'] == 'closed']
    analyzed_blades = [r for r in open_blades if r['edges_detected']]
    straight_blades = [r for r in analyzed_blades if r['is_straight']]
    
    # Calculate average angle and determine pass/fail
    if all_angles:
        average_angle = np.mean(all_angles)
        angle_deviation_from_90 = abs(90.0 - average_angle)
        angle_test_pass = angle_deviation_from_90 < 1.0  # Pass if less than 1° deviation
    else:
        average_angle = None
        angle_deviation_from_90 = None
        angle_test_pass = False
    
    print("\n" + "="*70)
    print(f"SUMMARY:")
    print("="*70)
    print(f"Total blade pairs:              {len(results)}")
    print(f"Expected open (alternating):    {len(open_blades)}")
    print(f"Expected closed:                {len(closed_blades)}")
    print(f"Successfully analyzed:          {len(analyzed_blades)}")
    
    if average_angle is not None:
        print(f"Average angle:                  {average_angle:.2f}°")
        print(f"Deviation from 90°:             {angle_deviation_from_90:.2f}°")
        print(f"Angle test (< 1° deviation):    {'✓ PASS' if angle_test_pass else '✗ FAIL'}")
    else:
        print(f"Average angle:                  N/A (no blades analyzed)")
        print(f"Angle test:                     ✗ FAIL")
    
    print(f"Overall Status:                 {'✓ PASS' if angle_test_pass else '✗ FAIL'}")
    print("="*70)
    
    # Generate simple visualization
    print("\nGenerating visualization...")
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # 1. Original image with blade indicators
    axes[0].imshow(original_image, cmap='gray', alpha=0.8)
    axes[0].axhline(y=analyzer.center_v, color='cyan', linestyle='--', linewidth=1, alpha=0.5)
    axes[0].axvline(x=analyzer.center_u, color='cyan', linestyle='--', linewidth=1, alpha=0.5)
    
    for result in results:
        if result['status'] == 'closed':
            # Closed blade - gray
            axes[0].axvline(x=result['u_pos'], color='gray', alpha=0.2, linewidth=1)
        elif result['edges_detected'] and result['actual_angle'] is not None:
            # Check if this individual blade is off by more than 1°
            blade_deviation = abs(90.0 - result['actual_angle'])
            if blade_deviation >= 1.0:
                # Red line for blade off by 1° or more
                color = 'red'
            else:
                # Green line for good blade
                color = 'green'
            axes[0].axvline(x=result['u_pos'], color=color, alpha=0.7, linewidth=2)
            
            # Draw midline if available
            if result['midline_coords'] is not None and len(result['midline_coords']) > 0:
                axes[0].scatter([result['u_pos']] * len(result['midline_coords']), 
                                 result['midline_coords'], 
                                 c=color, s=1, alpha=0.5)
        else:
            # Open but no detection - orange
            axes[0].axvline(x=result['u_pos'], color='orange', alpha=0.5, linewidth=1)
    
    axes[0].set_title('Blade Straightness Check\nGreen=Good (<1°) | Red=Off (≥1°) | Gray=Closed', 
                         fontweight='bold', fontsize=12)
    axes[0].axis('off')
    
    # 2. Results table
    axes[1].axis('off')
    
    # Calculate summary for table
    if all_angles:
        average_angle = np.mean(all_angles)
        angle_deviation = abs(90.0 - average_angle)
        test_result = "✓ PASS" if angle_deviation < 1.0 else "✗ FAIL"
    else:
        average_angle = None
        angle_deviation = None
        test_result = "✗ FAIL"
    
    # Create simple summary table
    table_data = []
    table_data.append(['Metric', 'Value', 'Status'])
    table_data.append(['Total Blades', f'{len(analyzed_blades)}', ''])
    if average_angle is not None:
        table_data.append(['Average Angle', f'{average_angle:.2f}°', ''])
        table_data.append(['Deviation from 90°', f'{angle_deviation:.2f}°', ''])
        table_data.append(['Test Result', 'Deviation < 1°', test_result])
    else:
        table_data.append(['Average Angle', 'N/A', ''])
        table_data.append(['Test Result', 'No data', test_result])
    
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
        if test_result == "✓ PASS":
            result_cell.set_facecolor('#E8F5E9')
            result_cell.set_text_props(color='green', weight='bold')
        else:
            result_cell.set_facecolor('#FFEBEE')
            result_cell.set_text_props(color='red', weight='bold')
    
    axes[1].set_title('Blade Straightness Test Results\n(Average Angle Method)', 
                     fontweight='bold', fontsize=14, pad=20)
    
    plt.tight_layout()
    
    # Save
    output_filename = os.path.join(os.path.dirname(__file__), 
                                   f"blade_straightness_{os.path.splitext(os.path.basename(filepath))[0]}.png")
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    print(f"\n✓ Visualization saved: {output_filename}")
    
    plt.show()
    
    return results


if __name__ == "__main__":
    filepath = r"R:\Radiotherapie - Physique Medicale\90 Encadrement etudiant\07EPITA\Etudiant Epita 2025\Alexandre Girold\TEST_AQUA\1.3.46.423632.420000.1761060621.5.dcm"
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    
    results = analyze_blade_straightness(filepath)
    
    if results:
        print("\n✓ Analysis complete!")
    else:
        print("\n✗ Analysis failed!")
