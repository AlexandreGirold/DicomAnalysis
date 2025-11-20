"""
Alignement Laser Test
Tests the alignment of laser markers
"""
from .base_test import BaseTest
from datetime import datetime
from typing import Optional


class AlignementLaserTest(BaseTest):
    """
    Test for checking laser marker alignment
    All marker deviations must be below the tolerance (2mm) to pass
    """
    
    def __init__(self):
        super().__init__(
            test_name="Alignement Laser",
            description="ANSM - Alignement Laser - Test des marqueurs"
        )
        self.tolerance_mm = 2.0  # Tolerance in mm
    
    def execute(self, ecart_proximal: float, ecart_central: float, ecart_distal: float, 
                operator: str, test_date: Optional[datetime] = None):
        """
        Execute the laser alignment test
        
        Args:
            ecart_proximal: Deviation of proximal marker in mm
            ecart_central: Deviation of central marker in mm
            ecart_distal: Deviation of distal marker in mm
            operator: Name of the operator performing the test
            test_date: Date of the test (defaults to current date)
        
        Returns:
            dict: Test results
        """
        # Set test information
        self.set_test_info(operator, test_date)
        
        # Add inputs
        self.add_input("ecart_proximal", ecart_proximal, "mm")
        self.add_input("ecart_central", ecart_central, "mm")
        self.add_input("ecart_distal", ecart_distal, "mm")
        
        # Validate inputs (deviations should be positive or zero)
        for name, value in [("ecart_proximal", ecart_proximal), 
                           ("ecart_central", ecart_central), 
                           ("ecart_distal", ecart_distal)]:
            if value < 0:
                raise ValueError(f"{name} must be a positive value (absolute deviation)")
        
        # Check each measurement against tolerance
        markers = [
            ("proximal", ecart_proximal),
            ("central", ecart_central),
            ("distal", ecart_distal)
        ]
        
        all_pass = True
        
        for marker_name, deviation in markers:
            status = "PASS" if deviation <= self.tolerance_mm else "FAIL"
            if status == "FAIL":
                all_pass = False
            
            self.add_result(
                name=f"ecart_{marker_name}",
                value=round(deviation, 2),
                status=status,
                unit="mm",
                tolerance=f"≤ {self.tolerance_mm} mm"
            )
        
        # Calculate overall result
        self.overall_result = "PASS" if all_pass else "FAIL"
        self.overall_status = "PASS" if all_pass else "FAIL"
        
        return self.to_dict()
    
    def get_form_data(self):
        """
        Get the form structure for frontend implementation
        
        Returns:
            dict: Form configuration
        """
        return {
            'title': 'ANSM - Alignement Laser - Test des marqueurs',
            'description': 'Test d\'alignement des marqueurs laser',
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
                    'name': 'ecart_proximal',
                    'label': 'Écart marqueur proximal:',
                    'type': 'number',
                    'required': True,
                    'min': 0,
                    'step': 0.01,
                    'unit': 'mm'
                },
                {
                    'name': 'ecart_central',
                    'label': 'Écart marqueur central:',
                    'type': 'number',
                    'required': True,
                    'min': 0,
                    'step': 0.01,
                    'unit': 'mm'
                },
                {
                    'name': 'ecart_distal',
                    'label': 'Écart marqueur distal:',
                    'type': 'number',
                    'required': True,
                    'min': 0,
                    'step': 0.01,
                    'unit': 'mm'
                }
            ],
            'tolerance': f'Écarts inférieurs à {self.tolerance_mm} mm'
        }
    
    def get_detailed_results(self):
        """
        Get detailed results with individual marker status
        
        Returns:
            dict: Detailed results
        """
        if not self.results:
            return {}
        
        marker_results = []
        for result_name, result_data in self.results.items():
            marker_name = result_name.replace('ecart_', '').title()
            marker_results.append({
                'marker': marker_name,
                'deviation': result_data['value'],
                'unit': result_data['unit'],
                'status': result_data['status'],
                'within_tolerance': result_data['status'] == 'PASS'
            })
        
        return {
            'marker_results': marker_results,
            'tolerance': f'{self.tolerance_mm} mm',
            'overall_pass': self.overall_result == 'PASS',
            'failed_markers': [r['marker'] for r in marker_results if r['status'] == 'FAIL']
        }


# Convenience function for standalone use
def test_alignement_laser(ecart_proximal: float, ecart_central: float, ecart_distal: float,
                         operator: str, test_date: Optional[datetime] = None):
    """
    Standalone function to test laser alignment
    
    Args:
        ecart_proximal: Deviation of proximal marker in mm
        ecart_central: Deviation of central marker in mm
        ecart_distal: Deviation of distal marker in mm
        operator: Name of the operator performing the test
        test_date: Date of the test (defaults to current date)
    
    Returns:
        dict: Test results
    """
    test = AlignementLaserTest()
    return test.execute(ecart_proximal, ecart_central, ecart_distal, operator, test_date)