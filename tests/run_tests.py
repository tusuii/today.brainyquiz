#!/usr/bin/env python
"""
Test runner script for the exam application.
This script runs unit, integration, and functional tests.
"""
import os
import sys
import pytest


def run_tests():
    """Run all tests or specific test categories based on arguments."""
    args = sys.argv[1:]
    
    if not args:
        # Run all tests
        print("Running all tests...")
        return pytest.main(['-xvs', 'tests'])
    
    if 'unit' in args:
        # Run unit tests
        print("Running unit tests...")
        pytest.main(['-xvs', 'tests/unit'])
    
    if 'integration' in args:
        # Run integration tests
        print("Running integration tests...")
        pytest.main(['-xvs', 'tests/integration'])
    
    if 'functional' in args:
        # Run functional tests
        print("Running functional tests...")
        pytest.main(['-xvs', 'tests/functional'])


if __name__ == '__main__':
    run_tests()
