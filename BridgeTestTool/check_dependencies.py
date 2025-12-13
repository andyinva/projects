#!/usr/bin/env python3
"""
Standalone dependency checker for Bridge Test Tool
Run this before using the tool to verify your system is ready
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dependency_checker import check_and_exit_if_missing


if __name__ == '__main__':
    print("=" * 70)
    print(" Bridge Test Tool - Pre-Installation Dependency Check")
    print("=" * 70)
    print()
    print("This script will verify that your system has all required")
    print("dependencies to run the Bridge Test Tool.")
    print()

    check_and_exit_if_missing(verbose=True)

    print()
    print("=" * 70)
    print(" System Check Complete - You're ready to run the tool!")
    print("=" * 70)
    print()
    print("To start the application:")
    print("  Windows: Double-click run.bat")
    print("  Linux/Mac: Run ./run.sh or python3 run.py")
    print()
