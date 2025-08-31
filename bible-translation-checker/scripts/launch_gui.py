#!/usr/bin/env python3
"""
Simple launcher for the Bible Correction System GUI

Usage:
    python3 launch_gui.py
"""

import sys
import os
from pathlib import Path

# Ensure we can import the modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from bible_correction_system import main
    print("🚀 Launching Bible Text Correction System...")
    main()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required files are in the same directory:")
    print("- bible_correction_system.py")
    print("- bible_correction_gui.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error launching system: {e}")
    sys.exit(1)