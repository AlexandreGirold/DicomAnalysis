# Exactitude du MLC (Leaf Position Analysis) Package

This package provides MLC (Multi-Leaf Collimator) blade position detection and analysis from DICOM images.

## Structure

```
leaf_position/
├── __init__.py          # Package initialization
└── analyzer.py          # MLCBladeAnalyzer class (formerly leaf_pos.py)
```

## Usage

```python
from leaf_position import MLCBladeAnalyzer

# Create analyzer instance
analyzer = MLCBladeAnalyzer()

# Process DICOM file
results = analyzer.process_image(dicom_file_path)
```

## Classes

### MLCBladeAnalyzer

Main class for analyzing MLC blade positions from DICOM portal images.

**Features:**
- Automatic blade edge detection
- Position measurement in mm
- Field size validation (20mm, 30mm, 40mm)
- Tolerance checking
- Visualization generation

**Methods:**
- `process_image(filepath)` - Analyze a single DICOM file
- `visualize_detection(...)` - Generate visualization plots
- `analyze_blade_positions(...)` - Detect blade edges

## Integration

This package is used by:
- `services/weekly/leaf_position.py` - LeafPosition test
- `services/basic_tests/mlc_leaf_jaw.py` - MLCLeafJaw test

## Migration Note

This package was created from the original `services/leaf_pos.py` file to better organize the codebase.
