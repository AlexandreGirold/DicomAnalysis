import sys
sys.path.insert(0, 'services')

print("Testing imports...")

# Test 1: Can we import daily module?
try:
    from daily import DAILY_TESTS
    print(f"✓ Daily tests imported: {list(DAILY_TESTS.keys())}")
except Exception as e:
    print(f"✗ Failed to import daily: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Can we import basic_tests?
try:
    from basic_tests import get_available_tests
    tests = get_available_tests()
    print(f"✓ Available tests: {len(tests)}")
    for test_id, info in tests.items():
        print(f"  - {test_id} ({info['category']}): {info['description'][:50]}...")
except Exception as e:
    print(f"✗ Failed to get tests: {e}")
    import traceback
    traceback.print_exc()
