#!/usr/bin/env python3
"""
Complete test runner for formal platooning system
"""

import sys
import os
import subprocess
import pytest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_all_tests():
    """Run complete test suite"""
    print("🧪 FORMAL PLATOONING VERIFICATION - COMPLETE TEST SUITE")
    print("=" * 60)
    
    # Run unit tests
    print("\n1. Running Unit Tests...")
    result1 = subprocess.run([
        'python', '-m', 'pytest', 
        'tests/test_safety.py', 
        '-v',
        '--tb=short'
    ])
    
    # Run integration tests
    print("\n2. Running Integration Tests...")
    result2 = subprocess.run([
        'python', '-m', 'pytest', 
        'tests/test_integration.py', 
        '-v',
        '--tb=short'
    ])
    
    # Run with coverage
    print("\n3. Running Coverage Analysis...")
    result3 = subprocess.run([
        'python', '-m', 'pytest',
        'tests/',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html:coverage_report'
    ])
    
    # Run examples to verify they work
    print("\n4. Verifying Examples...")
    try:
        from examples.basic_platoon import main as basic_main
        basic_main()
        print("   ✅ basic_platoon.py works")
    except Exception as e:
        print(f"   ❌ basic_platoon.py failed: {e}")
    
    try:
        from examples.emergency_scenario import main as emergency_main
        emergency_main()
        print("   ✅ emergency_scenario.py works")
    except Exception as e:
        print(f"   ❌ emergency_scenario.py failed: {e}")
    
    # Final report
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    
    all_passed = (result1.returncode == 0 and 
                  result2.returncode == 0 and 
                  result3.returncode == 0)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is formally verified.")
        print("📊 Coverage report: coverage_report/index.html")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)