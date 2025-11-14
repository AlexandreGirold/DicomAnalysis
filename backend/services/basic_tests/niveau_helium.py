"""
Niveau d'Hélium Test
Tests if the helium level is above the minimum threshold (65%)
"""
from .base_test import BaseTest
from datetime import datetime
from typing import Optional


class NiveauHeliumTest(BaseTest):
    """
    Test for checking helium level
    The helium level must be above 65% to pass
    """
    
    def __init__(self):
        super().__init__(
            test_name="Niveau d'Hélium",
            description="ANSM - Test du niveau d'hélium - Doit être supérieur à 65%"
        )
        self.minimum_level = 65.0  # Minimum helium level percentage
    
    def execute(self, helium_level: float, operator: str, test_date: Optional[datetime] = None):
        """
        Execute the helium level test
        
        Args:
            helium_level: Current helium level in percentage
            operator: Name of the operator performing the test
            test_date: Date of the test (defaults to current date)
        
        Returns:
            dict: Test results
        """
        # Set test information
        self.set_test_info(operator, test_date)
        
        # Add input
        self.add_input("helium_level", helium_level, "%")
        
        # Validate input
        if helium_level < 0 or helium_level > 100:
            raise ValueError("Helium level must be between 0 and 100%")
        
        # Perform test calculation
        is_above_threshold = helium_level > self.minimum_level
        status = "PASS" if is_above_threshold else "FAIL"
        
        # Add result
        self.add_result(
            name="helium_level_check",
            value=helium_level,
            status=status,
            unit="%",
            tolerance=f"> {self.minimum_level}%"
        )
        
        # Calculate overall result
        self.calculate_overall_result()
        
        return self.to_dict()
    
    def get_form_data(self):
        """
        Get the form structure for frontend implementation
        
        Returns:
            dict: Form configuration
        """
        return {
            'title': 'ANSM - Niveau d\'Hélium',
            'description': 'Test du niveau d\'hélium - Doit être supérieur à 65%',
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
                    'name': 'helium_level',
                    'label': 'Niveau d\'hélium (%):',
                    'type': 'number',
                    'required': True,
                    'min': 0,
                    'max': 100,
                    'step': 0.1,
                    'unit': '%'
                }
            ],
            'tolerance': f'Niveau supérieur à {self.minimum_level}%'
        }


# Convenience function for standalone use
def test_helium_level(helium_level: float, operator: str, test_date: Optional[datetime] = None):
    """
    Standalone function to test helium level
    
    Args:
        helium_level: Current helium level in percentage
        operator: Name of the operator performing the test
        test_date: Date of the test (defaults to current date)
    
    Returns:
        dict: Test results
    """
    test = NiveauHeliumTest()
    return test.execute(helium_level, operator, test_date)