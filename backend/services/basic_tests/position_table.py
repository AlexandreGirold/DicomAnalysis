"""
Position Table V2 Test
Tests the positioning accuracy of the treatment table
"""
from .base_test import BaseTest
from datetime import datetime
from typing import Optional


class PositionTableV2Test(BaseTest):
    """
    Test for checking table positioning accuracy
    Calculates the difference between two table positions and checks tolerance
    """
    
    def __init__(self):
        super().__init__(
            test_name="Position Table V2",
            description="ANSM - Laser et Table - Test de positionnement"
        )
        self.expected_difference = 4.0  # Expected difference in cm (21.5 - 17.5)
        self.tolerance_mm = 2.0  # Tolerance in mm
    
    def execute(self, position_175: float, position_215: float, operator: str, test_date: Optional[datetime] = None):
        """
        Execute the table position test
        
        Args:
            position_175: Table position at 17.5 cm
            position_215: Table position at 21.5 cm  
            operator: Name of the operator performing the test
            test_date: Date of the test (defaults to current date)
        
        Returns:
            dict: Test results
        """
        # Set test information
        self.set_test_info(operator, test_date)
        
        # Add inputs
        self.add_input("position_175", position_175, "cm")
        self.add_input("position_215", position_215, "cm")
        
        # Calculate actual difference between positions (in cm)
        actual_difference = position_215 - position_175
        
        # Calculate gap in mm: abs((expected_difference - actual_difference) * 10)
        # Convert to mm for tolerance check
        ecart_mm = abs((self.expected_difference - actual_difference) * 10)
        
        # Check tolerance
        ecart_status = "PASS" if ecart_mm <= self.tolerance_mm else "FAIL"
        
        # Add results
        self.add_result(
            name="actual_difference",
            value=round(actual_difference, 2),
            status="INFO",  # This is just informational
            unit="cm"
        )
        
        self.add_result(
            name="ecart_mm",
            value=round(ecart_mm, 2),
            status=ecart_status,
            unit="mm",
            tolerance=f"≤ {self.tolerance_mm} mm"
        )
        
        # Calculate overall result
        self.overall_result = ecart_status
        self.overall_status = ecart_status
        
        return self.to_dict()
    
    def get_form_data(self):
        """
        Get the form structure for frontend implementation
        
        Returns:
            dict: Form configuration
        """
        return {
            'title': 'ANSM - Laser et Table - Test de positionnement',
            'description': 'Test de positionnement de la table',
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
                    'name': 'position_175',
                    'label': 'Position de table 17,5 (cm):',
                    'type': 'number',
                    'required': True,
                    'step': 0.01,
                    'unit': 'cm'
                },
                {
                    'name': 'position_215',
                    'label': 'Position de table 21,5 (cm):',
                    'type': 'number',
                    'required': True,
                    'step': 0.01,
                    'unit': 'cm'
                }
            ],
            'tolerance': f'Écart inférieur à {self.tolerance_mm} mm',
            'expected_difference': f'Différence attendue: {self.expected_difference} cm'
        }
    
    def get_calculation_details(self):
        """
        Get detailed calculation information for results display
        
        Returns:
            dict: Calculation details
        """
        if not self.inputs:
            return {}
        
        position_175 = self.inputs.get('position_175', {}).get('value', 0)
        position_215 = self.inputs.get('position_215', {}).get('value', 0)
        actual_difference = position_215 - position_175
        ecart_mm = abs((self.expected_difference - actual_difference) * 10)
        
        return {
            'calculations': [
                {
                    'description': 'Différence réelle entre positions',
                    'formula': f'{position_215} - {position_175}',
                    'result': f'{actual_difference:.2f} cm'
                },
                {
                    'description': 'Écart par rapport à la valeur attendue',
                    'formula': f'|({self.expected_difference} - {actual_difference:.2f}) * 10|',
                    'result': f'{ecart_mm:.2f} mm'
                }
            ],
            'tolerance_check': f'Écart ({ecart_mm:.2f} mm) {"≤" if ecart_mm <= self.tolerance_mm else ">"} {self.tolerance_mm} mm'
        }


# Convenience function for standalone use
def test_position_table_v2(position_175: float, position_215: float, operator: str, test_date: Optional[datetime] = None):
    """
    Standalone function to test table positioning
    
    Args:
        position_175: Table position at 17.5 cm
        position_215: Table position at 21.5 cm
        operator: Name of the operator performing the test
        test_date: Date of the test (defaults to current date)
    
    Returns:
        dict: Test results
    """
    test = PositionTableV2Test()
    return test.execute(position_175, position_215, operator, test_date)