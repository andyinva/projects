# Phase 3: Config Manager Extraction - Installation Guide

## Prerequisites
- Phase 2 must be successfully installed and working
- Backup of current working code recommended

## Installation Steps

### Step 1: Backup Current Code
```bash
cd ~/projects/bible-search-lite
cp bible_search_lite.py bible_search_lite_phase2_backup.py
```

### Step 2: Extract Phase 3 Archive
```bash
cd ~/projects/bible-search-lite
tar -xzf bible_search_phase3.tar.gz
```

This will:
- Update `bible_search_lite.py` (main file)
- Update `bible_search_ui/__init__.py`
- Create `bible_search_ui/config/` directory (NEW)
- Create `bible_search_ui/config/config_manager.py` (NEW)
- Create `bible_search_ui/config/__init__.py` (NEW)
- Preserve all other files from Phase 2

### Step 3: Verify File Structure
```bash
tree bible_search_ui
```

Expected output:
```
bible_search_ui/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── config_manager.py
└── ui/
    ├── __init__.py
    ├── dialogs.py
    └── widgets.py
```

### Step 4: Run the Application
```bash
python3 bible_search_lite.py
```

Or use the launcher script:
```bash
./run_bible_search.sh
```

## What Changed

### Configuration Management
All configuration file operations are now handled by the `ConfigManager` class:

**Old approach (Phase 2):**
```python
# In bible_search_lite.py
self.config_file = "bible_search_lite_config.json"

def save_config(self):
    try:
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error: {e}")
```

**New approach (Phase 3):**
```python
# In bible_search_lite.py
self.config_manager = ConfigManager("bible_search_lite_config.json")

def save_config(self):
    self.config_manager.save(config)
```

### Import Changes
Phase 3 removes unused imports from main file:
- ~~`import json`~~ (moved to ConfigManager)
- ~~`import os`~~ (moved to ConfigManager)

New import added:
```python
from bible_search_ui.config import ConfigManager
```

## Testing Checklist

### Basic Functionality
- [ ] Application starts without errors
- [ ] Window opens at saved position and size
- [ ] Search functionality works
- [ ] Translation selector opens and functions
- [ ] Font settings dialog opens and functions

### Configuration Persistence
- [ ] Change window size and restart - size is remembered
- [ ] Change translation selections and restart - selections remembered
- [ ] Change checkbox settings and restart - settings remembered
- [ ] Change font sizes and restart - fonts remembered
- [ ] Move window position and restart - position remembered

### Configuration Files
- [ ] Config file exists at `bible_search_lite_config.json`
- [ ] Config file is valid JSON (can open in text editor)
- [ ] Config file structure matches expected format

### Error Handling
- [ ] Delete config file while app is closed - app starts with defaults
- [ ] Corrupt config file (add invalid JSON) - app starts with defaults and prints error
- [ ] App can save config after loading defaults

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'bible_search_ui.config'"

**Cause**: Phase 3 files not properly extracted or config directory missing.

**Solution**:
```bash
cd ~/projects/bible-search-lite
ls -la bible_search_ui/config/
# Should show __init__.py and config_manager.py

# If missing, re-extract the archive
tar -xzf bible_search_phase3.tar.gz
```

### Issue: "AttributeError: ... object has no attribute 'config_manager'"

**Cause**: Old version of bible_search_lite.py still being used.

**Solution**:
```bash
# Verify you're running the Phase 3 version
grep "self.config_manager" bible_search_lite.py
# Should show: self.config_manager = ConfigManager(...)

# If not found, re-extract
tar -xzf bible_search_phase3.tar.gz
```

### Issue: App starts but doesn't save configuration

**Check 1**: Verify ConfigManager is initialized
```bash
grep "ConfigManager" bible_search_lite.py
# Should show import and initialization
```

**Check 2**: Check file permissions
```bash
ls -la bible_search_lite_config.json
# Should be writable by your user
```

**Check 3**: Run with verbose output
```bash
python3 bible_search_lite.py 2>&1 | grep -i config
# Look for "Configuration saved" or error messages
```

### Issue: Config file appears corrupted

**Solution**: Delete and let app recreate with defaults
```bash
rm bible_search_lite_config.json
python3 bible_search_lite.py
# App will start with defaults and create new config file
```

### Issue: Import error related to dialogs or widgets

**Cause**: Phase 2 may not have been properly installed.

**Solution**: Verify Phase 2 structure exists
```bash
ls -la bible_search_ui/ui/
# Should show: dialogs.py and widgets.py

# If missing, you may need to install Phase 2 first
```

## Rollback Instructions

If you encounter issues and need to revert to Phase 2:

```bash
cd ~/projects/bible-search-lite

# Restore Phase 2 backup
cp bible_search_lite_phase2_backup.py bible_search_lite.py

# Remove Phase 3 config directory
rm -rf bible_search_ui/config/

# Restart application
python3 bible_search_lite.py
```

## Verification Commands

Run these commands to verify successful installation:

```bash
# Check line count (should be around 886)
wc -l bible_search_lite.py

# Check for ConfigManager usage
grep -c "config_manager" bible_search_lite.py
# Should return 3 or more

# Check for removed imports
grep "^import json" bible_search_lite.py
# Should return nothing (no match)

grep "^import os" bible_search_lite.py  
# Should return nothing (no match)

# Check config directory structure
find bible_search_ui/config -type f
# Should list: __init__.py and config_manager.py

# Verify config module can be imported
python3 -c "from bible_search_ui.config import ConfigManager; print('OK')"
# Should print: OK
```

## Next Steps After Installation

1. **Test thoroughly** - Run through the testing checklist above
2. **Review changes** - Read PHASE3_SUMMARY.md for technical details
3. **Report issues** - Note any problems for debugging
4. **Decide on Phase 4** - Review Phase 4 options in PHASE3_SUMMARY.md

## Success Indicators

You'll know Phase 3 is working correctly when:
- ✅ App starts without import errors
- ✅ Configuration saves and loads correctly
- ✅ All dialogs (Translations, Fonts) work
- ✅ Settings persist across app restarts
- ✅ No "json" or "os" import errors
- ✅ Console shows "Configuration loaded/saved" messages

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify file structure matches expected layout
3. Check console output for error messages
4. Use rollback instructions if needed

## Performance Notes

Phase 3 should have **no impact** on performance:
- Configuration loading/saving is identical speed
- File I/O operations are the same
- Only the organization of code has changed
- May see slightly faster startup due to less code in main file

## Summary

Phase 3 is a **low-risk refactoring** that:
- Doesn't change any user-visible functionality
- Improves code organization significantly
- Makes the codebase more maintainable
- Sets foundation for future enhancements

The main risk is import errors, which are easily fixed by re-extracting the archive or rolling back to Phase 2.
