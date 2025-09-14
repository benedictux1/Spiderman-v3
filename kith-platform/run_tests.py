#!/usr/bin/env python3
"""
Test runner script for Kith Platform
"""

import os
import sys
import subprocess
import argparse

def run_tests(test_type='all', verbose=False, coverage=True):
    """Run tests with specified options"""
    
    # Base pytest command
    cmd = ['python3', '-m', 'pytest']
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            '--cov=app',
            '--cov=config',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=80'
        ])
    
    # Add test type filters
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'auth':
        cmd.extend(['-m', 'auth'])
    elif test_type == 'database':
        cmd.extend(['-m', 'database'])
    elif test_type == 'api':
        cmd.extend(['-m', 'api'])
    elif test_type == 'celery':
        cmd.extend(['-m', 'celery'])
    elif test_type == 'slow':
        cmd.extend(['-m', 'slow'])
    
    # Add test directory
    cmd.append('tests/')
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run tests
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='Run Kith Platform tests')
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'auth', 'database', 'api', 'celery', 'slow'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--quick', action='store_true', help='Quick test run (unit tests only, no coverage)')
    
    args = parser.parse_args()
    
    # Quick mode overrides
    if args.quick:
        args.type = 'unit'
        args.no_coverage = True
        args.verbose = False
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=not args.no_coverage
    )
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
