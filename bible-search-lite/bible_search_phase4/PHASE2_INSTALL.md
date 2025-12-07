# Phase 2: Dialog Extraction - Quick Start Guide

## What Changed in Phase 2?

Phase 2 extracted dialog window code into a separate module, building on the widget extraction from Phase 1.

### Before Phase 2:
- 992 lines in `bible_search_lite.py`
- Dialog creation code embedded in main file (117 lines)
- 2 methods with complex UI construction logic

### After Phase 2:
- 901 lines in `bible_search_lite.py` (**-9.2%**)
- Dialog classes in separate `bible_search_ui/ui/dialogs.py` module
- 2 simplified methods that just instantiate dialog classes

## Installation

### Option 1: If you already have Phase 1 installed

```bash
cd ~/projects/bible-search-lite

# Backup your current working version
cp bible_search_lite.py bible_search_lite_phase1_backup.py

# Copy the new files
cp /path/to/phase2/bible_search_lite.py .
cp /path/to/phase2/bible_search_ui/ui/dialogs.py bible_search_ui/ui/

# Update the __init__.py
cp /path/to/phase2/bible_search_ui/ui/__init__.py bible_search_ui/ui/
```

### Option 2: Fresh installation

```bash
cd ~/projects/bible-search-lite

# Backup everything
cp -r bible_search_ui bible_search_ui_backup
cp bible_search_lite.py bible_search_lite_backup.py

# Extract the Phase 2 archive
tar -xzf bible_search_phase2.tar.gz

# This will update:
# - bible_search_lite.py (main file)
# - bible_search_ui/ui/dialogs.py (new)
# - bible_search_ui/ui/__init__.py (updated)
```

## Testing Phase 2

Run the application and test the extracted dialogs:

```bash
python3 bible_search_lite.py
```

### Test Checklist:

#### Translation Settings Dialog
- [ ] Click gear icon (⚙) in Message Window
- [ ] Translation settings dialog opens
- [ ] All translations listed in 4-column grid
- [ ] "Select All" button checks all boxes
- [ ] "Select None" button unchecks all boxes
- [ ] Selecting translations and clicking OK applies changes
- [ ] Button shows count: "Translations (3)"
- [ ] Clicking Cancel makes no changes

#### Font Settings Dialog  
- [ ] Click gear icon (⚙) in Message Window
- [ ] Font settings dialog opens
- [ ] Two separate sections: Title and Bible Text
- [ ] Each section has 5 radio button choices
- [ ] Current selection is indicated
- [ ] Selecting new sizes and clicking OK applies changes
- [ ] Fonts update throughout the application
- [ ] Clicking Cancel makes no changes

## What Was Extracted?

### Files Created/Modified:

1. **`bible_search_ui/ui/dialogs.py`** (NEW - 327 lines)
   - `TranslationSelectorDialog` class
   - `FontSettingsDialog` class
   - Comprehensive docstrings with examples

2. **`bible_search_lite.py`** (MODIFIED - reduced 992 → 901 lines)
   - Simplified `show_translation_selector()` (58 → 14 lines)
   - Simplified `show_font_settings()` (60 → 13 lines)
   - Cleaner imports (removed unused PyQt dialog imports)

3. **`bible_search_ui/ui/__init__.py`** (UPDATED)
   - Added exports for dialog classes

## Benefits You'll Notice

1. **Cleaner Code**: Main file is shorter and easier to navigate
2. **Better Organization**: Settings dialogs separated from main logic
3. **Reusable**: Dialog classes can be used elsewhere if needed
4. **Well Documented**: All dialog classes have comprehensive docstrings

## File Structure After Phase 2

```
bible-search-lite/
├── bible_search.py                  (unchanged - core engine)
├── bible_search_service.py          (unchanged - PyQt service)
├── bible_search_lite.py             (modified - 901 lines, -9.2%)
├── bible_search_lite_config.json    (unchanged - settings)
├── run_bible_search.sh              (unchanged - launcher)
└── bible_search_ui/                 (package)
    ├── __init__.py
    └── ui/
        ├── __init__.py              (updated - exports dialogs)
        ├── widgets.py               (Phase 1 - 700 lines)
        └── dialogs.py               (Phase 2 - 327 lines)
```

## Troubleshooting

### Import Error: "cannot import name 'TranslationSelectorDialog'"
**Solution**: Make sure `bible_search_ui/ui/dialogs.py` exists and `__init__.py` is updated

### Dialog doesn't appear
**Solution**: Check console for Python errors. Verify all files copied correctly.

### Application crashes when opening dialogs
**Solution**: 
1. Check that the import statement is correct: 
   `from bible_search.ui.dialogs import ...`
2. Verify you don't have naming conflicts (bible_search.py vs bible_search/ directory)

## Rollback Instructions

If you encounter issues:

```bash
cd ~/projects/bible-search-lite

# Restore backups
cp bible_search_lite_phase1_backup.py bible_search_lite.py
rm bible_search_ui/ui/dialogs.py

# Or restore the full backup
rm -rf bible_search_ui
cp -r bible_search_ui_backup bible_search_ui
```

## Next Phase Options

After Phase 2, we can continue with:

- **Phase 3A**: Extract Styles Module (~100 line reduction)
- **Phase 3B**: Extract Config Manager (~150 line reduction)  
- **Phase 3C**: Extract Search Service Integration (~200 line reduction)

Let me know when you're ready to proceed!

## Support

If you run into any issues:
1. Check console output for error messages
2. Verify file structure matches the diagram above
3. Ensure all imports use `bible_search_ui` (not `bible_search`)
4. Check that Python can find the modules: `python3 -c "from bible_search_ui.ui.dialogs import TranslationSelectorDialog; print('OK')"`
