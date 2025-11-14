"""
Weekly Tests Package
Collection of weekly quality control tests for medical equipment
"""

# Weekly test registry
WEEKLY_TESTS = {
    # Add weekly tests here as they are implemented
    # Example:
    # 'test_name': {
    #     'class': TestClass,
    #     'function': test_function,
    #     'description': 'Test description',
    #     'category': 'weekly'
    # }
}

def get_weekly_tests():
    """
    Get list of all available weekly tests
    
    Returns:
        dict: Dictionary of available weekly tests with their descriptions
    """
    return {
        test_id: {
            'description': test_info['description'],
            'class_name': test_info['class'].__name__,
            'category': test_info['category']
        }
        for test_id, test_info in WEEKLY_TESTS.items()
    }
