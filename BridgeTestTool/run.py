#!/usr/bin/env python3
"""
Main entry point for Bridge Test Tool
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from launcher import main

if __name__ == '__main__':
    main()
