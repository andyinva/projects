# Dependency Checking Feature

## Overview

The Bridge Test Tool now includes **automatic dependency checking** that runs before the application starts. This ensures users are immediately notified if their system is missing any required components, with clear instructions on how to fix the issue.

## What Gets Checked

### 1. Python Version
- **Minimum Required**: Python 3.7
- **Check**: Verifies the Python version meets the minimum requirement
- **Error Message**: Shows current version and provides download link if too old

### 2. Required Standard Library Modules
All of these should be included with Python, but some systems (especially Linux) may be missing tkinter:

- **tkinter** - GUI framework
  - Most likely to be missing on Linux
  - Provides installation instructions for Debian/Ubuntu, RedHat/CentOS, and Arch Linux

- **socket** - Network communication
- **sqlite3** - Database support
- **threading** - Multi-threading support
- **json** - JSON encoding/decoding

### 3. Optional Modules (Future Enhancements)
These are checked but not required:

- **matplotlib** - For graphing and visualization
- **numpy** - For advanced statistics
- **pandas** - For data analysis

## How It Works

### Automatic Checking

When you start the tool, it automatically checks dependencies:

```bash
# Any of these will trigger the check:
python run.py
python src/launcher.py
python src/server.py
python src/client.py
```

**Output Example (Success):**
```
Checking dependencies...
============================================================
Bridge Test Tool - Dependency Check
============================================================

System Information:
  Platform: Linux-6.6.87.2-microsoft-standard-WSL2-aarch64
  Python: 3.12.3 (CPython)

Checking Python Version:
  ✓ Python 3.12 (OK)

Checking Required Modules:
  ✓ tkinter (GUI framework) - OK
  ✓ socket (Network communication) - OK
  ✓ sqlite3 (Database support) - OK
  ✓ threading (Multi-threading support) - OK
  ✓ json (JSON encoding/decoding) - OK

Checking Optional Modules:
  ○ matplotlib (Graphing and visualization) - Not installed (optional)
  ○ numpy (Advanced statistics) - Not installed (optional)
  ○ pandas (Data analysis) - Not installed (optional)

============================================================
✓ All dependencies satisfied - Ready to run!
============================================================

✓ All dependencies satisfied - Starting application...
```

**Output Example (Error - Missing tkinter):**
```
Checking dependencies...
============================================================
Bridge Test Tool - Dependency Check
============================================================

System Information:
  Platform: Linux-5.15.0-58-generic-x86_64
  Python: 3.10.6 (CPython)

Checking Python Version:
  ✓ Python 3.10 (OK)

Checking Required Modules:
  ✓ socket (Network communication) - OK
  ✓ sqlite3 (Database support) - OK
  ✓ threading (Multi-threading support) - OK
  ✓ json (JSON encoding/decoding) - OK
  ✗ tkinter (GUI framework) - MISSING
    Error: No module named '_tkinter'

    Installation:
    sudo apt-get install python3-tk  # Debian/Ubuntu
    sudo yum install python3-tkinter  # RedHat/CentOS
    sudo pacman -S tk  # Arch Linux

============================================================
✗ Missing dependencies - Please install them first

Missing Modules:
  • tkinter (GUI framework)

Tkinter is usually missing on Linux systems.
Install it with:
  sudo apt-get install python3-tk     # Debian/Ubuntu
  sudo yum install python3-tkinter    # RedHat/CentOS
  sudo pacman -S tk                   # Arch Linux
============================================================

Press Enter to exit...
```

### Manual Pre-Check

You can also check dependencies before starting the tool:

```bash
cd BridgeTestTool
python check_dependencies.py
```

This is useful for:
- Pre-installation verification
- Troubleshooting startup issues
- Checking system compatibility

## Files Added/Modified

### New Files Created

1. **src/dependency_checker.py** (~320 lines)
   - Core dependency checking module
   - `DependencyChecker` class with comprehensive checks
   - Helper functions for quick checks

2. **check_dependencies.py** (~30 lines)
   - Standalone script for pre-installation checks
   - Can be run from project root
   - User-friendly wrapper around the checker module

### Modified Files

1. **src/launcher.py**
   - Added dependency check before importing GUI modules
   - Exits gracefully with instructions if dependencies missing

2. **src/server.py**
   - Added dependency check in `main()` function
   - Allows running server directly with checks

3. **src/client.py**
   - Added dependency check in `main()` function
   - Allows running client directly with checks

4. **README.md**
   - Added dependency check step to Installation section
   - Added "Missing Dependencies" troubleshooting section
   - Includes installation instructions for tkinter on Linux

5. **QUICKSTART.md**
   - Added "First Time Setup" section
   - Mentions automatic checking feature

## Benefits

### For Users

1. **Immediate Feedback**
   - Know right away if something is missing
   - No confusing Python tracebacks

2. **Clear Instructions**
   - Platform-specific installation commands
   - Direct links to download Python if needed

3. **System Information**
   - See exactly what Python version you're running
   - See your platform and system details

4. **Optional Enhancements**
   - Informed about optional packages that add features
   - Not blocked by missing optional packages

### For Developers

1. **Better Support**
   - Users can provide clear system information
   - Easy to diagnose environment issues

2. **Proactive Detection**
   - Catches issues before they cause crashes
   - Reduces support requests

3. **Extensible**
   - Easy to add checks for new dependencies
   - Can check versions of specific packages

## Common Scenarios

### Scenario 1: Linux User Missing tkinter

**Problem**: Fresh Linux install often doesn't include tkinter

**Solution**:
```bash
# The tool will show:
✗ tkinter (GUI framework) - MISSING
  Installation:
  sudo apt-get install python3-tk  # Debian/Ubuntu

# User runs:
sudo apt-get install python3-tk

# Then tool starts successfully
```

### Scenario 2: Python Too Old

**Problem**: User has Python 3.6 installed

**Solution**:
```bash
# The tool will show:
✗ Python 3.6 is too old
  Required: Python 3.7+
  Please upgrade Python from https://www.python.org/downloads/

# User upgrades Python, then tool works
```

### Scenario 3: All Good!

**Problem**: No problem!

**Solution**:
```bash
# The tool will show:
✓ All dependencies satisfied - Ready to run!

# And immediately start the GUI
```

## Testing the Dependency Checker

### Test Manually

```bash
# Run the standalone checker
python check_dependencies.py

# Or run the module directly
python src/dependency_checker.py

# Or run as module
python -m src.dependency_checker
```

### Expected Output

You should see:
- System information (platform, Python version)
- Python version check (✓ or ✗)
- All required modules checked (✓ for each)
- Optional modules status (○ for not installed)
- Final summary (✓ All good or ✗ Missing dependencies)

## Platform-Specific Notes

### Windows
- tkinter is always included
- Rarely has dependency issues
- Just need Python 3.7+

### macOS
- tkinter is included
- May need Xcode Command Line Tools
- Generally no issues

### Linux
- **Most common issue**: Missing tkinter
- **Solution**: Install python3-tk package
- Different package names by distro:
  - Debian/Ubuntu: `python3-tk`
  - RedHat/CentOS/Fedora: `python3-tkinter`
  - Arch: `tk`

## Technical Details

### DependencyChecker Class

```python
from dependency_checker import DependencyChecker

checker = DependencyChecker()

# Check Python version
ok, msg = checker.check_python_version()

# Check a specific module
ok, msg = checker.check_module('tkinter')

# Check all modules
all_ok, messages = checker.check_all_modules()

# Run full check
all_ok, report = checker.run_full_check(verbose=True)

# Get system info
info = checker.get_system_info()
```

### Helper Functions

```python
from dependency_checker import check_dependencies, check_and_exit_if_missing

# Check and print report
all_ok = check_dependencies(verbose=True)

# Check and exit if anything missing (good for startup)
check_and_exit_if_missing(verbose=True)
```

## Future Enhancements

Possible additions to the dependency checker:

1. **Version Checking**
   - Check minimum versions of optional packages
   - Warn if versions are outdated

2. **Network Connectivity**
   - Test if ports are available
   - Check firewall status

3. **Permissions**
   - Check write permissions for database
   - Check network permissions

4. **Configuration Validation**
   - Verify config.yaml is valid
   - Check for common configuration errors

5. **Self-Healing**
   - Attempt to install missing pip packages automatically
   - Provide one-click fix buttons

## Summary

The dependency checking feature provides:

✅ **Automatic checking** on every startup
✅ **Clear error messages** with installation instructions
✅ **Platform-specific help** for Linux/Windows/Mac
✅ **Manual pre-check** option before installation
✅ **System information** for troubleshooting
✅ **Optional package detection** for future features
✅ **Graceful failure** with helpful guidance

This ensures users have a smooth experience and can quickly resolve any environment issues before trying to use the tool.

---

**Feature Version**: 1.0
**Added**: November 5, 2025
**Files Modified**: 5
**Files Added**: 2
**Lines of Code**: ~350
