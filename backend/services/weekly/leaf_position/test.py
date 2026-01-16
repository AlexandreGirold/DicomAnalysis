"""
Leaf Position Test
Simple test to check MLC blade positions and their lengths from DICOM images.
Similar to MLC Leaf and Jaw test but supports 20mm, 30mm, or 40mm field sizes.
"""
from ...basic_tests.base_test import BaseTest
from datetime import datetime
from typing import Optional, List
import os
import sys
import logging
import base64
import io
import glob
from ...visualization_storage import save_multiple_visualizations

# Setup logging
logger = logging.getLogger(__name__)

# Add parent directory to path to import leaf_position
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

try:
    from .analyzer import MLCBladeAnalyzer
except ImportError:
    from analyzer import MLCBladeAnalyzer


class LeafPositionTest(BaseTest):
    """
    Test for checking MLC blade positions and lengths
    Supports field sizes: 20mm, 30mm, or 40mm
    """
    
    def __init__(self):
        super().__init__(
            test_name="Leaf Position",
            description="Détection automatique des positions et longueurs des lames MLC"
        )
        self.analyzer = None
        self.visualizations = []
        self.blade_results = []  # Store individual blade results
        self.file_results = []  # Store file-level summaries
    
    def _get_dicom_acquisition_date(self, filepath):
        """Extract acquisition date/time from DICOM file"""
        import pydicom
        try:
            ds = pydicom.dcmread(filepath, stop_before_pixels=True)
            
            # Try different date/time fields in order of preference
            if hasattr(ds, 'AcquisitionDate') and hasattr(ds, 'AcquisitionTime'):
                date_str = ds.AcquisitionDate  # Format: YYYYMMDD
                time_str = ds.AcquisitionTime  # Format: HHMMSS.ffffff
            elif hasattr(ds, 'ContentDate') and hasattr(ds, 'ContentTime'):
                date_str = ds.ContentDate
                time_str = ds.ContentTime
            elif hasattr(ds, 'StudyDate') and hasattr(ds, 'StudyTime'):
                date_str = ds.StudyDate
                time_str = ds.StudyTime
            else:
                return None
            
            # Format: YYYY-MM-DD HH:MM:SS
            datetime_str = f"{date_str}{time_str.split('.')[0]}"
            from datetime import datetime
            dt = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.warning(f"Could not extract acquisition date from {filepath}: {e}")
            return None
    
    def _get_analysis_type(self, image_number, total_images):
        """Determine analysis type based on image position in sequence"""
        # For 6-image leaf position test:
        # Image 1: Center Detection
        # Image 2: Jaw Position
        # Image 3: Leaf Position
        # Image 4: Leaf Position
        # Image 5: Blade Straightness
        # Image 6: Leaf Position
        if image_number == 1:
            return 'Center Detection'
        elif image_number == 2:
            return 'Jaw Position'
        elif image_number == 3:
            return 'Leaf Position'
        elif image_number == 4:
            return 'Leaf Position'
        elif image_number == 5:
            return 'Blade Straightness'
        elif image_number == 6:
            return 'Leaf Position'
        else:
            return 'Leaf Position'
    
    def get_form_data(self):
        """Return form configuration for this test"""
        return {
            'test_id': 'leaf_position',
            'test_name': self.test_name,
            'description': self.description,
            'fields': [
                {
                    'name': 'test_date',
                    'type': 'date',
                    'label': 'Date du Test',
                    'required': False,
                    'default': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'name': 'operator',
                    'type': 'text',
                    'label': 'Opérateur',
                    'required': True,
                    'placeholder': 'Nom de l\'opérateur'
                },
                {
                    'name': 'dicom_file',
                    'type': 'file',
                    'label': 'Fichiers DICOM',
                    'required': True,
                    'accept': '.dcm',
                    'multiple': True
                },
                {
                    'name': 'notes',
                    'type': 'textarea',
                    'label': 'Notes',
                    'required': False,
                    'placeholder': 'Notes additionnelles...'
                }
            ]
        }
    
    def execute(self, files: List[str], operator: str, 
                test_date: Optional[datetime] = None, notes: Optional[str] = None):
        """
        Execute the leaf position test on DICOM files
        Automatically detects blade positions and lengths for each file
        
        Args:
            files: List of DICOM file paths
            operator: Name of the operator performing the test
            test_date: Date of the test (defaults to current date)
            notes: Additional notes
        
        Returns:
            dict: Test results including blade analysis and visualizations
        """
        # Set test information
        self.set_test_info(operator, test_date)
        
        # Validate inputs - MUST have exactly 6 DICOM files
        if not files or len(files) == 0:
            raise ValueError("At least one DICOM file is required")
        
        if len(files) != 6:
            raise ValueError(f"Exactly 6 DICOM files are required for Leaf Position test, but {len(files)} were provided")
        
        logger.info(f"Analyzing leaf positions from {len(files)} DICOM file(s)")
        logger.info(f"Files to process: {[os.path.basename(f) for f in files]}")
        
        # Create analyzer
        self.analyzer = MLCBladeAnalyzer()
        
        # Process each DICOM file
        all_ok_count = 0
        all_out_of_tolerance_count = 0
        all_closed_count = 0
        all_total_blades = 0
        
        try:
            for file_index, filepath in enumerate(files, 1):
                logger.info(f"Processing file {file_index}/{len(files)}: {os.path.basename(filepath)}")
                
                filename = os.path.basename(filepath)
                
                # Extract acquisition date from DICOM
                acquisition_date = self._get_dicom_acquisition_date(filepath)
                display_name = acquisition_date if acquisition_date else filename
                
                # Determine analysis type based on file position
                analysis_type = self._get_analysis_type(file_index, len(files))
                
                # Add image info result - this displays in the results section
                self.add_result(
                    name=f"image_{file_index}_info",
                    value=f"{filename} | Acquisition: {acquisition_date if acquisition_date else 'Unknown'}",
                    status="INFO",
                    details=None
                )
                
                # Process image - this creates a PNG visualization file
                result = self.analyzer.process_image(filepath)
                
                if not result:
                    self.add_result(
                        name=f"file_{file_index}_analysis",
                        value=None,
                        status="FAIL",
                        details=f"[{filename}] Failed to analyze DICOM file"
                    )
                    continue
                
                # result is a list of blade data tuples
                blade_data = result if isinstance(result, list) else []
                if not blade_data:
                    self.add_result(
                        name=f"file_{file_index}_analysis",
                        value=None,
                        status="FAIL",
                        details=f"[{filename}] No blade data found in analysis"
                    )
                    continue
                
                # Find and convert the generated PNG visualization to base64
                # The analyzer saves files as: blade_detection_{basename}.png
                base_name = os.path.splitext(filename)[0]
                
                # Search in multiple locations for the PNG file
                search_dirs = [
                    os.getcwd(),  # Current working directory
                    os.path.dirname(filepath),  # Same directory as DICOM file
                    os.path.join(os.getcwd(), 'backend'),  # Backend directory
                    'backend',  # Relative backend
                ]
                
                png_files = []
                for search_dir in search_dirs:
                    if not os.path.exists(search_dir):
                        continue
                    # Try with wildcards
                    pattern1 = os.path.join(search_dir, f"blade_detection_*{base_name}*.png")
                    pattern2 = os.path.join(search_dir, f"blade_detection_{base_name}.png")
                    png_files.extend(glob.glob(pattern1))
                    png_files.extend(glob.glob(pattern2))
                
                # Remove duplicates
                png_files = list(set(png_files))
                
                logger.info(f"Looking for PNG for {base_name}, found: {len(png_files)} files")
                if png_files:
                    logger.info(f"Found PNG files: {png_files}")
                
                if png_files:
                    # Use the most recent file
                    png_file = max(png_files, key=os.path.getctime)
                    try:
                        with open(png_file, 'rb') as f:
                            image_base64 = base64.b64encode(f.read()).decode('utf-8')
                        
                        # Format visualization like MVIC_fente does
                        viz_obj = {
                            'name': display_name,  # Use acquisition date instead of filename
                            'type': 'image',
                            'data': f'data:image/png;base64,{image_base64}',
                            'filename': filename,
                            'acquisition_date': acquisition_date,
                            'index': file_index,
                            'statistics': {
                                'status': 'COMPLETE',
                                'total_blades': 0,  # Will be updated below
                                'ok_blades': 0,
                                'out_of_tolerance': 0,
                                'closed_blades': 0
                            }
                        }
                        self.visualizations.append(viz_obj)
                        logger.info(f"Captured visualization from: {png_file}")
                        
                        # Clean up the PNG file
                        try:
                            os.remove(png_file)
                        except:
                            pass
                    except Exception as e:
                        logger.warning(f"Could not read visualization file {png_file}: {e}")
                else:
                    logger.warning(f"No visualization PNG found for {filename}")
                
                # Analyze blade positions and lengths for this file
                total_blades = len(blade_data)
                ok_count = 0
                out_of_tolerance_count = 0
                closed_count = 0
                
                # Collect detected positions for field size estimation
                detected_lengths = []
                
                # Valid field sizes with tolerance
                valid_field_sizes = [20, 30, 40]
                tolerance = 1.0  # ±1mm tolerance
                
                # Store individual blade results for this file/image
                file_blade_results = {'blades': []}
                
                for blade in blade_data:
                    # blade is a tuple: (pair_lame, distance_t, distance_p, field_size, status, detected_points)
                    blade_pair = blade[0]
                    field_size_mm = blade[3] if blade[3] is not None else 0
                    original_status = blade[4] if blade[4] else 'UNKNOWN'
                    
                    # Re-evaluate status: check if field_size is close to 20, 30, or 40mm
                    if 'CLOSED' in original_status:
                        status_simple = 'CLOSED'
                    elif field_size_mm == 0 or field_size_mm is None:
                        status_simple = 'CLOSED'
                    else:
                        # Check if the field size matches any valid size (20, 30, or 40mm) within tolerance
                        is_valid = False
                        for valid_size in valid_field_sizes:
                            if abs(field_size_mm - valid_size) <= tolerance:
                                is_valid = True
                                break
                        
                        status_simple = 'OK' if is_valid else 'OUT OF TOLERANCE'
                    
                    if status_simple == 'OK':
                        ok_count += 1
                    elif status_simple == 'OUT OF TOLERANCE':
                        out_of_tolerance_count += 1
                    elif status_simple == 'CLOSED':
                        closed_count += 1
                    
                    # Get position and blade edges from detected_points dict (last element of tuple)
                    detected_points = blade[5] if len(blade) > 5 else {}
                    position_u = detected_points.get('u', 0) if isinstance(detected_points, dict) else 0
                    v_sup = detected_points.get('v_sup', None) if isinstance(detected_points, dict) else None
                    v_inf = detected_points.get('v_inf', None) if isinstance(detected_points, dict) else None
                    distance_sup = detected_points.get('distance_sup', None) if isinstance(detected_points, dict) else None
                    distance_inf = detected_points.get('distance_inf', None) if isinstance(detected_points, dict) else None
                    
                    if field_size_mm > 0:
                        detected_lengths.append(field_size_mm)
                    
                    # Store blade result for database
                    file_blade_results['blades'].append({
                        'pair': blade_pair,
                        'position_u_px': position_u,
                        'v_sup_px': v_sup,
                        'v_inf_px': v_inf,
                        'distance_sup_mm': distance_sup,
                        'distance_inf_mm': distance_inf,
                        'length_mm': field_size_mm,
                        'field_size_mm': field_size_mm,
                        'is_valid': status_simple,
                        'status_message': original_status
                    })
                
                # Add this file's blade results to the collection
                self.blade_results.append(file_blade_results)
                
                # Estimate field size from detected lengths
                avg_length = sum(detected_lengths) / len(detected_lengths) if detected_lengths else 0
                detected_field_size = round(avg_length / 10) * 10  # Round to nearest 10mm
                
                # File summary result - removed to avoid [object Object] display
                file_status = "PASS" if out_of_tolerance_count == 0 else "FAIL"
                file_summary = {
                    'file': filename,
                    'total_blades': total_blades,
                    'ok': ok_count,
                    'out_of_tolerance': out_of_tolerance_count,
                    'closed': closed_count,
                    'detected_field_size_mm': detected_field_size,
                    'average_length_mm': avg_length
                }
                
                # Don't add file_summary as a result (causes [object Object] display)
                # self.add_result(
                #     name=f"file_{file_index}_summary",
                #     value=file_summary,
                #     status=file_status,
                #     details=f"[{filename}] Detected field size: ~{detected_field_size}mm - {ok_count}/{total_blades} blades OK"
                # )
                
                # Store file-level summary for display
                self.file_results.append(file_summary)
                
                # Update visualization statistics
                if self.visualizations and len(self.visualizations) >= file_index:
                    self.visualizations[file_index - 1]['statistics'] = {
                        'status': 'COMPLETE',
                        'total_blades': total_blades,
                        'ok_blades': ok_count,
                        'out_of_tolerance': out_of_tolerance_count,
                        'closed_blades': closed_count
                    }
                
                # Accumulate totals
                all_total_blades += total_blades
                all_ok_count += ok_count
                all_out_of_tolerance_count += out_of_tolerance_count
                all_closed_count += closed_count
                all_ok_count += ok_count
                all_out_of_tolerance_count += out_of_tolerance_count
                all_closed_count += closed_count
            
            # Overall summary for all files - removed to avoid [object Object] display
            overall_status = "PASS" if all_out_of_tolerance_count == 0 else "FAIL"
            # Don't add overall_summary as a result (causes [object Object] display)
            # self.add_result(
            #     name="overall_summary",
            #     value={
            #         'total_files': len(files),
            #         'total_blades': all_total_blades,
            #         'ok': all_ok_count,
            #         'out_of_tolerance': all_out_of_tolerance_count,
            #         'closed': all_closed_count
            #     },
            #     status=overall_status,
            #     details=f"Total: {all_ok_count}/{all_total_blades} blades OK across {len(files)} file(s)"
            # )
            
            # Calculate overall result using BaseTest method
            self.calculate_overall_result()
            
            logger.info(f"Leaf position test completed: {self.overall_result}")
            return self._format_output(notes=notes)
            
        except Exception as e:
            logger.error(f"Error during leaf position analysis: {e}", exc_info=True)
            self.add_result(
                name="error",
                value=None,
                status="FAIL",
                details=f"Analysis error: {str(e)}"
            )
            self.calculate_overall_result()
            return self._format_output(notes=notes)
    
    def _format_output(self, notes: Optional[str] = None):
        """Format test output"""
        output = {
            'test_name': self.test_name,
            'test_date': self.test_date.isoformat() if self.test_date else datetime.now().isoformat(),
            'operator': self.operator,
            'overall_result': self.overall_result,
            'results': self.results,
            'blade_results': self.blade_results,  # Individual blade data for database
            'file_results': self.file_results,  # File-level summaries for display
            'notes': notes or ''
        }
        
        # Add visualizations if any were generated
        if self.visualizations:
            output['visualizations'] = self.visualizations
        
        return output


def test_leaf_position(files: List[str], operator: str,
                      test_date: Optional[datetime] = None, notes: Optional[str] = None):
    """
    Standalone function for leaf position test
    Automatically detects blade positions and field size for multiple files
    
    Args:
        files: List of DICOM file paths
        operator: Operator name
        test_date: Test date
        notes: Additional notes
    
    Returns:
        dict: Test results
    """
    test = LeafPositionTest()
    return test.execute(files, operator, test_date, notes)
