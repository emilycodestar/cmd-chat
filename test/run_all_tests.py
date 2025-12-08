"""Run all test suites."""
import sys
import time

def run_test_module(module_name):
    """Import and run a test module."""
    try:
        module = __import__(f"test.{module_name}", fromlist=[module_name])
        if hasattr(module, "test_" + module_name.split("_")[-1]):
            func = getattr(module, "test_" + module_name.split("_")[-1])
            return func()
        elif hasattr(module, "run_all_tests"):
            return module.run_all_tests()
        else:
            # Try to find any test function
            for attr in dir(module):
                if attr.startswith("test_"):
                    func = getattr(module, attr)
                    if callable(func):
                        return func()
            return None
    except Exception as e:
        print(f"Error running {module_name}: {e}")
        return False

def main():
    """Run all test suites."""
    print("\n" + "="*60)
    print("  CMD CHAT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  python cmd_chat.py serve 0.0.0.0 1000 --password TestPass123")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nTests cancelled.")
        return
    
    test_modules = [
        "test_security",
        "test_error_handling",
        "test_json_parsing",
        "test_heartbeat",
        "test_rate_limiting",
        "test_rooms",
        "test_commands",
        "test_delta_updates",
    ]
    
    results = []
    for module in test_modules:
        print(f"\n{'='*60}")
        print(f"Running {module}...")
        print('='*60)
        try:
            result = run_test_module(module)
            results.append((module, result))
            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
            results.append((module, False))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for module, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {module}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

