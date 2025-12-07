# Phase 4B: Extract Search Integration - Installation Guide

## Overview

This guide walks you through installing and testing the Phase 4B refactoring, which extracts search logic into a dedicated `SearchController` class.

## What Changed

### New Files
```
bible_search_ui/controllers/
├── __init__.py                  # Package initialization
└── search_controller.py         # SearchController class (398 lines)
```

### Modified Files
- `bible_search_lite.py`: Search methods replaced with controller delegation
- `bible_search_ui/__init__.py`: Exports SearchController

## Installation Steps

### Step 1: Backup Current Code

```bash
cd ~/projects/bible-search-lite
cp bible_search_lite.py bible_search_lite_phase3_backup.py
cp -r bible_search_ui bible_search_ui_phase3_backup
```

### Step 2: Extract Phase 4B Archive

```bash
# If you have the tar.gz archive:
tar -xzf bible_search_phase4b.tar.gz

# Or copy individual files from the phase4 directory
```

### Step 3: Verify File Structure

```bash
# Check that new controller module exists
ls -l bible_search_ui/controllers/

# Should show:
# __init__.py
# search_controller.py
```

### Step 4: Check Line Counts

```bash
wc -l bible_search_lite.py
# Should show: 692 lines

wc -l bible_search_ui/controllers/search_controller.py
# Should show: 398 lines
```

### Step 5: Syntax Check

```bash
# Check for Python syntax errors
python3 -m py_compile bible_search_lite.py
python3 -m py_compile bible_search_ui/controllers/search_controller.py

# If no output, syntax is correct!
```

## Testing Checklist

### ✅ Basic Search Functionality

1. **Launch application:**
   ```bash
   python3 bible_search_lite.py
   ```

2. **Perform a simple search:**
   - Enter "love" in search box
   - Click Search button
   - Verify results appear

3. **Test search history:**
   - Perform multiple searches
   - Click search dropdown
   - Verify history appears with most recent first

4. **Test lazy loading:**
   - Search for "the" (should return many results)
   - Scroll down slowly
   - Verify more results load automatically
   - Check message shows "Loaded X of Y results"

### ✅ Context Loading

1. **Click a verse in search results**
   - Verify Reading Window populates
   - Verify 50 verses load
   - Verify first verse is highlighted in yellow

2. **Test cross-chapter context:**
   - Search for last verse of a chapter (e.g., "Gen 1:31")
   - Click it
   - Verify Reading Window shows verses from next chapter too

### ✅ Search Settings

1. **Test case sensitivity:**
   - Check "Case Sensitive"
   - Search for "Love" vs "love"
   - Verify different results

2. **Test unique verses:**
   - Check "Unique Verse"
   - Search for common term
   - Verify only one translation per verse

3. **Test abbreviate results:**
   - Check "Abbreviate Results"
   - Verify "and", "the", etc. replaced with ".."

### ✅ Translation Selection

1. **Click "Translations" button**
   - Verify dialog opens
   - Select multiple translations
   - Click OK
   - Perform search
   - Verify results from multiple translations

### ✅ Error Handling

1. **Empty search:**
   - Leave search box empty
   - Click Search
   - Verify message: "Please enter search terms"

2. **No results:**
   - Search for "zzzzzzz"
   - Verify message: "No results found"

### ✅ UI Responsiveness

1. **Search large result sets:**
   - Search for "the"
   - Verify UI stays responsive
   - Verify first 100 results load quickly

2. **Window resizing:**
   - Resize main window
   - Verify all sections resize properly
   - Verify search results remain visible

## Verification Tests

### Test 1: Search Controller Integration

```python
# In Python interpreter
from bible_search_ui.controllers import SearchController
print("✓ SearchController imports successfully")

# Check it's a QObject
from PyQt6.QtCore import QObject
assert issubclass(SearchController, QObject)
print("✓ SearchController is a QObject")
```

### Test 2: Signal Connections

```python
# After launching app in Python
import bible_search_lite
# Check controller exists
assert hasattr(app, 'search_controller')
print("✓ App has search_controller attribute")

# Check controller has required methods
assert hasattr(app.search_controller, 'perform_search')
assert hasattr(app.search_controller, 'load_context_verses')
print("✓ Controller has required methods")
```

### Test 3: Lazy Loading

1. Search for "the" (returns 30,000+ results)
2. Check message: "Loaded 100 of XXXXX results"
3. Scroll to bottom
4. Check message updates: "Loaded 200 of XXXXX results"
5. Continue scrolling
6. Verify message shows: "All XXXXX results loaded" when done

## Troubleshooting

### Issue: "No module named 'bible_search_ui.controllers'"

**Cause:** Controllers module not properly installed

**Fix:**
```bash
# Verify controllers directory exists
ls bible_search_ui/controllers/

# If missing, create it:
mkdir -p bible_search_ui/controllers

# Copy files from phase4 directory
```

### Issue: "AttributeError: 'BibleSearchProgram' object has no attribute 'search_controller'"

**Cause:** Controller not initialized in __init__

**Fix:**
```python
# In bible_search_lite.py __init__ method, add after setup_ui():
self.search_controller = SearchController(
    self.bible_search,
    self.search_service,
    self.verse_lists,
    self.message_label
)
```

### Issue: Search doesn't work / no results appear

**Cause:** Signal connections may be missing

**Fix:**
1. Check SearchController.__init__ connects signals:
   ```python
   self.search_service.search_completed.connect(self._on_search_completed)
   ```

2. Verify BibleSearchProgram doesn't have old signal connections

### Issue: Lazy loading doesn't work

**Cause:** Scroll signal not connected

**Fix:**
- Controller automatically connects scroll signal in `_on_search_completed`
- Verify `scroll_bar.valueChanged.connect(self.on_search_scroll)` is called

### Issue: Context verses don't load

**Cause:** load_context_verses not delegating properly

**Fix:**
```python
# In bible_search_lite.py:
def load_context_verses(self, center_verse_id):
    """Load context verses - delegates to SearchController"""
    self.search_controller.load_context_verses(center_verse_id)
```

## Performance Check

After installation, verify performance:

| Test | Expected Result | Status |
|------|----------------|--------|
| Simple search ("love") | < 1 second | ☐ |
| Large search ("the") | < 3 seconds initial load | ☐ |
| Lazy load next batch | < 0.5 seconds | ☐ |
| Context loading | < 1 second | ☐ |
| UI remains responsive | No freezing during search | ☐ |

## Rollback Procedure

If you encounter issues and need to revert:

### Step 1: Restore Backup Files

```bash
cd ~/projects/bible-search-lite
cp bible_search_lite_phase3_backup.py bible_search_lite.py
rm -rf bible_search_ui
cp -r bible_search_ui_phase3_backup bible_search_ui
```

### Step 2: Verify Application Works

```bash
python3 bible_search_lite.py
# Test basic search functionality
```

### Step 3: Report Issue

If you had to rollback, please note:
- What operation caused the issue
- Error messages received
- Steps to reproduce

## Configuration

No configuration changes needed for Phase 4B. All settings remain the same:
- Window geometry
- Search settings
- Translation preferences
- Font settings

## Next Steps

After successful installation and testing:

1. **Use the application normally** for a few days
2. **Monitor for any issues** with search functionality
3. **Note any improvements** in:
   - Code clarity
   - Ease of debugging
   - Performance
   - Maintainability

4. **Consider next phase:**
   - Option A: Extract Styles Module (~100 line reduction)
   - Option C: Extract Window Management (~150 line reduction)
   - Or stop here if satisfied with current structure

## Support

**Phase 4B Details:**
- Main file: 692 lines (was 886)
- New controller: 398 lines
- Total reduction: 194 lines (21.9%)
- All functionality preserved

**Contact:**
- Email: ajhinva@gmail.com
- Project: ~/projects/bible-search-lite

## Success Criteria

✅ Application launches without errors  
✅ Search functionality works as before  
✅ Context loading works  
✅ Lazy loading works for large result sets  
✅ All UI interactions responsive  
✅ No regressions in features  
✅ Code is cleaner and more organized  

---

**Completion:** Once all tests pass, Phase 4B is successfully installed!
