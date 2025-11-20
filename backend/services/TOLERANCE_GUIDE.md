# MLC Blade Analyzer - Tolerance Guide

## Overview
This guide explains how to adjust the tolerance parameters for the MLC blade analysis.

## Tolerance Parameters

All tolerance parameters are defined in the `__init__` method of the `MLCBladeAnalyzer` class (lines 22-28):

```python
# Tolerance settings (user-adjustable)
self.expected_field_size = 20.0  # mm - Expected field size when fully open
self.field_size_tolerance = 1.0  # mm - Tolerance for field size
self.edge_detection_threshold = 0.5  # 0-1: fraction of max-min for edge detection, 
self.min_blade_separation = 23  # pixels - minimum separation between opposing blades
```

### 1. Expected Field Size (`expected_field_size`)
- **Default:** 20.0 mm
- **Purpose:** The expected distance between superior and inferior blade edges when fully open
- **How to adjust:** Change this value if your protocol expects a different field size

### 2. Field Size Tolerance (`field_size_tolerance`)
- **Default:** 1.0 mm
- **Purpose:** Acceptable deviation from the expected field size
- **How to adjust:** 
  - Increase for more lenient tolerance (e.g., 1.5 mm)
  - Decrease for stricter tolerance (e.g., 0.5 mm)
- **Result:** Blades will be marked as "OUT_OF_TOLERANCE" if their field size is outside the range: `expected_field_size ± field_size_tolerance`

### 3. Edge Detection Threshold (`edge_detection_threshold`)
- **Default:** 0.5 (median)
- **Purpose:** Controls sensitivity of edge detection
- **Range:** 0.0 to 1.0
- **How to adjust:**
  - **Lower values (e.g., 0.3):** More sensitive, detects fainter edges
  - **Higher values (e.g., 0.7):** Less sensitive, only detects strong edges
- **Tip:** If you're getting false positives (detecting edges that aren't real), increase this value

### 4. Minimum Blade Separation (`min_blade_separation`)
- **Default:** 23 pixels (~5 mm)
- **Purpose:** Minimum distance between opposing blades to avoid detecting the same edge twice
- **How to adjust:** Only change if you're getting detection errors or false detections

## Visual Indicators

### In the Detection Image (Bottom-Left Plot):
- **Red/Green dots:** Blade within tolerance (Red = Superior, Green = Inferior)
- **Orange dots:** Blade out of tolerance (with field size displayed)
- **Black X:** Blade closed or not detected

### In the Field Size Plot (Bottom-Right Plot):
- **Green band:** Tolerance range (expected ± tolerance)
- **Green line:** Expected field size
- **Green dots:** Blades within tolerance
- **Red dots:** Blades out of tolerance
- **Vertical dotted lines:** Closed blades

## Status Codes

| Status | Meaning |
|--------|---------|
| `OK` | Field size is within tolerance |
| `OUT_OF_TOLERANCE` | Field size is outside the acceptable range |
| `CLOSED` | Blade could not be detected (likely closed) |

## Example Adjustments

### More Lenient Analysis
```python
self.expected_field_size = 20.0
self.field_size_tolerance = 2.0  # Changed from 1.0
self.edge_detection_threshold = 0.4  # Changed from 0.5 (more sensitive)
```

### Stricter Analysis
```python
self.expected_field_size = 20.0
self.field_size_tolerance = 0.5  # Changed from 1.0
self.edge_detection_threshold = 0.6  # Changed from 0.5 (less sensitive)
```

### Different Expected Field Size
```python
self.expected_field_size = 10.0  # For 10mm field
self.field_size_tolerance = 0.5
```

## Summary Statistics

After analysis, the script provides:
- **Total blade pairs analyzed**
- **OK (within tolerance):** Number of blades meeting criteria
- **Out of tolerance:** Number of blades failing criteria
- **Closed/Not detected:** Number of blades that couldn't be detected

## Output Files

1. **`blade_detection_[filename].png`** - Visual analysis with all 4 plots
2. **`mlc_blade_analysis_results.csv`** - Detailed results for all blades

## Tips

1. **If too many false positives:** Increase `edge_detection_threshold`
2. **If missing real blades:** Decrease `edge_detection_threshold`
3. **If getting duplicate detections:** Increase `min_blade_separation`
4. **For different protocols:** Adjust `expected_field_size` accordingly
