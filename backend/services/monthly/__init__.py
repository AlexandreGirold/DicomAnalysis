"""
Monthly Tests Package
Collection of monthly quality control tests for medical equipment
"""

# Monthly test registry
MONTHLY_TESTS = {
    # Add monthly tests here as they are implemented
    # Example:
    # 'test_name': {
    #     'class': TestClass,
    #     'function': test_function,
    #     'description': 'Test description',
    #     'category': 'monthly'
    # }
}

def get_monthly_tests():
    """
    Get list of all available monthly tests
    
    Returns:
        dict: Dictionary of available monthly tests with their descriptions
    """
    return {
        test_id: {
            'description': test_info['description'],
            'class_name': test_info['class'].__name__,
            'category': test_info['category']
        }
        for test_id, test_info in MONTHLY_TESTS.items()
    }
