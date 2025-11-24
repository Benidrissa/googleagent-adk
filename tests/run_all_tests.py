#!/usr/bin/env python3
"""
Master test runner for Pregnancy Companion Agent Evaluation Suite.

This script runs all evaluation tests and provides a comprehensive summary.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from datetime import datetime


async def run_test_file(test_file: Path) -> dict:
    """Run a single test file and return results."""
    print(f"\n{'='*80}")
    print(f"Running: {test_file.name}")
    print('='*80)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=test_file.parent.parent,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        passed = result.returncode == 0
        
        return {
            'name': test_file.stem,
            'passed': passed,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            'name': test_file.stem,
            'passed': False,
            'output': '',
            'error': 'Test timed out after 120 seconds'
        }
    except Exception as e:
        return {
            'name': test_file.stem,
            'passed': False,
            'output': '',
            'error': str(e)
        }


async def run_pytest():
    """Run pytest integration tests."""
    print(f"\n{'='*80}")
    print("Running: pytest integration tests")
    print('='*80)
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        return {
            'name': 'pytest_integration',
            'passed': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {
            'name': 'pytest_integration',
            'passed': False,
            'output': '',
            'error': str(e)
        }


async def main():
    """Run all tests and generate summary."""
    
    print("\n" + "="*80)
    print("PREGNANCY COMPANION AGENT - EVALUATION SUITE")
    print(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Find all test files
    test_files = [
        test_dir / 'test_teen_hemorrhage.py',
        test_dir / 'test_missing_lmp.py',
        test_dir / 'test_low_risk.py',
        test_dir / 'test_invalid_date.py'
    ]
    
    # Run individual tests
    results = []
    for test_file in test_files:
        if test_file.exists():
            result = await run_test_file(test_file)
            results.append(result)
            print(result['output'])
            if result['error']:
                print(f"ERROR: {result['error']}")
    
    # Run pytest integration
    pytest_result = await run_pytest()
    results.append(pytest_result)
    print(pytest_result['output'])
    if pytest_result['error']:
        print(f"ERROR: {pytest_result['error']}")
    
    # Generate summary
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    passed_tests = [r for r in results if r['passed']]
    failed_tests = [r for r in results if not r['passed']]
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {len(passed_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    
    if passed_tests:
        print("\nPassed Tests:")
        for r in passed_tests:
            print(f"  ✅ {r['name']}")
    
    if failed_tests:
        print("\nFailed Tests:")
        for r in failed_tests:
            print(f"  ❌ {r['name']}")
            if r['error']:
                print(f"     Error: {r['error']}")
    
    # Overall result
    print("\n" + "="*80)
    if len(failed_tests) == 0:
        print("🎉 ALL TESTS PASSED! ✅")
        print("="*80)
        return True
    else:
        print(f"⚠️  {len(failed_tests)} TEST(S) FAILED")
        print("="*80)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
