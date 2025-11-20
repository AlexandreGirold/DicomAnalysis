"""
Base test class for basic quality control tests
"""
from datetime import datetime
from typing import Dict, Any, Optional
import json


class BaseTest:
    """
    Base class for all quality control tests
    Provides common functionality for test execution and result formatting
    """
    
    def __init__(self, test_name: str, description: str):
        self.test_name = test_name
        self.description = description
        self.test_date = None
        self.operator = None
        self.inputs = {}
        self.results = {}
        self.overall_result = None
        self.overall_status = None
        
    def set_test_info(self, operator: str, test_date: Optional[datetime] = None):
        """
        Set basic test information
        
        Args:
            operator: Name of the operator performing the test
            test_date: Date of the test (defaults to current date)
        """
        self.operator = operator
        self.test_date = test_date or datetime.now()
    
    def add_input(self, name: str, value: Any, unit: str = None):
        """
        Add an input value to the test
        
        Args:
            name: Name of the input parameter
            value: Value of the input
            unit: Unit of measurement (optional)
        """
        self.inputs[name] = {
            'value': value,
            'unit': unit
        }
    
    def add_result(self, name: str, value: Any, status: str, unit: str = None, tolerance: Any = None, details: str = None):
        """
        Add a result to the test
        
        Args:
            name: Name of the result parameter
            value: Calculated value
            status: PASS or FAIL
            unit: Unit of measurement (optional)
            tolerance: Tolerance criteria (optional)
            details: Additional details or description (optional)
        """
        self.results[name] = {
            'value': value,
            'status': status,
            'unit': unit,
            'tolerance': tolerance,
            'details': details
        }
    
    def calculate_overall_result(self):
        """
        Calculate overall test result based on individual results
        Default implementation: PASS if all results are PASS, otherwise FAIL
        """
        if not self.results:
            self.overall_result = "UNKNOWN"
            self.overall_status = "UNKNOWN"
            return
        
        all_pass = all(result['status'] == 'PASS' for result in self.results.values())
        self.overall_result = "PASS" if all_pass else "FAIL"
        self.overall_status = "PASS" if all_pass else "FAIL"
    
    def execute(self, **kwargs):
        """
        Execute the test with given parameters
        This method should be overridden by specific test implementations
        
        Args:
            **kwargs: Test-specific parameters
        
        Returns:
            dict: Test results
        """
        raise NotImplementedError("execute method must be implemented by specific test classes")
    
    def to_dict(self):
        """
        Convert test results to dictionary format
        
        Returns:
            dict: Test results in dictionary format
        """
        return {
            'test_name': self.test_name,
            'description': self.description,
            'test_date': self.test_date.isoformat() if self.test_date else None,
            'operator': self.operator,
            'inputs': self.inputs,
            'results': self.results,
            'overall_result': self.overall_result,
            'overall_status': self.overall_status
        }
    
    def to_json(self):
        """
        Convert test results to JSON string
        
        Returns:
            str: Test results in JSON format
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def get_summary(self):
        """
        Get a summary of the test results
        
        Returns:
            dict: Summary information
        """
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result['status'] == 'PASS')
        failed_checks = total_checks - passed_checks
        
        return {
            'test_name': self.test_name,
            'overall_result': self.overall_result,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'operator': self.operator,
            'test_date': self.test_date.isoformat() if self.test_date else None
        }