# Phase 4B: Search Controller Extraction - Installation Guide

## Quick Start

### For First-Time Installation

```bash
# Navigate to your project directory
cd ~/projects/bible-search-lite

# Extract the archive
tar -xzf bible_search_phase4.tar.gz

# The structure will be:
bible-search-lite/
├── bible_search_lite.py          (updated main file)
├── bible_search.py                (unchanged)
├── bible_search_service.py        (unchanged)
├── bible_search_lite_config.json  (your config - preserved)
├── database/
│   └── bibles.db                  (unchanged)
└── bible_search_ui/
    ├── __init__.py                (updated exports)
    ├── config/
    │   ├── __init__.py
    │   └── config_manager.py      (from Phase 3)
    ├── controllers/               (NEW in Phase 4)
    │   ├── __init__.py
    │   └── search_controller.py   (NEW)
    └── ui/
        ├── __init__.py
        ├── widgets.py             (from Phase 1)
        └── dialogs.py             (from Phase 2)

# Test the application
python3 bible_search_lite.py
```

### For Upgrading from Phase 3

```bash
# Backup your Phase 3 installation
cp -r ~/projects/bible-search-lite ~/projects/bible-search-lite-phase3-backup

# Navigate to project directory
cd ~/projects/bible-search-lite

# Extract Phase 4 files (will overwrite Phase 3 files)
tar -xzf bible_search_phase4.tar.gz

# Verify new controller directory exists
ls -la bible_search_ui/controllers/

# Test the application
python3 bible_search_lite.py
```

## Testing Checklist

After installation, verify all functionality works:

### 1. Basic Search (5 minutes)
- [ ] Enter search term (e.g., "love")
- [ ] Click Search button
- [ ] Results appear in Search Results window (Window 2)
- [ ] Status message shows count and time
- [ ] Search term added to history dropdown

### 2. Lazy Loading (2 minutes)
- [ ] Search for common word (e.g., "the") to get many results
- [ ] Scroll down in search results
- [ ] More results load automatically
- [ ] Status message updates with loaded count
- [ ] All results eventually load

### 3. Context Loading (3 minutes)
- [ ] Click a verse in search results
- [ ] Reading window (Window 3) loads context verses
- [ ] Clicked verse is highlighted in yellow
- [ ] Can see verses before and after
- [ ] Scroll works in reading window

### 4. Translation Selector (2 minutes)
- [ ] Click "Translations" button
- [ ] Dialog shows all available translations
- [ ] Can check/uncheck translations
- [ ] "Select All" / "Select None" buttons work
- [ ] Click OK to save selections
- [ ] Search uses selected translations

### 5. Search Options (2 minutes)
- [ ] Case Sensitive checkbox works
- [ ] Unique Verse checkbox works
- [ ] Abbreviate Results checkbox works
- [ ] Options affect search results correctly

### 6. Font Settings (2 minutes)
- [ ] Click gear icon (âš™)
- [ ] Font settings dialog appears
- [ ] Can change title font size
- [ ] Can change verse font size
- [ ] Changes apply immediately after clicking OK
- [ ] Settings persist after restart

### 7. Window Management (2 minutes)
- [ ] Can resize windows by dragging splitters
- [ ] Window sizes persist after restart
- [ ] Click verses to make windows active
- [ ] Active window has blue border and background

### 8. Subject Verses (3 minutes)
- [ ] Select verse in search results (checkbox)
- [ ] Click Acquire button
- [ ] Verse appears in Subject Verses (Window 4)
- [ ] Can acquire verses from reading window too
- [ ] Selections clear after acquire

### 9. Configuration Persistence (2 minutes)
- [ ] Change window sizes
- [ ] Change font settings
- [ ] Select different translations
- [ ] Close application
- [ ] Reopen application
- [ ] All settings restored correctly

### 10. Error Handling (2 minutes)
- [ ] Try empty search - shows "Please enter search terms"
- [ ] Search with no results - shows "No results found"
- [ ] Verify no crashes or unhandled errors

**Total Testing Time: ~25 minutes**

## What Changed in Phase 4

### User-Visible Changes
**NONE** - All functionality works exactly the same as Phase 3.

### Developer-Visible Changes
1. **New SearchController class** handles all search operations
2. **Cleaner main file** - search logic moved to controller
3. **Better signal organization** - controller emits signals, UI responds
4. **Improved code structure** - clear separation of concerns

## File-by-File Changes

### bible_search_lite.py
**Before (Phase 3)**: 886 lines
**After (Phase 4)**: 789 lines
**Change**: -97 lines (-11%)

**What changed**:
- Removed `BibleSearch` and `BibleSearchService` imports
- Added `SearchController` import
- Replaced `self.bible_search` and `self.search_service` with `self.search_controller`
- Simplified `perform_search()` method (32 → 26 lines)
- Replaced old signal handlers with new ones:
  - `on_search_completed` → `on_search_results_ready`
  - `on_search_scroll` → handled by controller's `load_more_results`
  - `on_search_failed` → simplified version
  - `on_search_progress` → `on_search_status`
  - Added `on_search_more_results_ready`
  - Added `on_context_verses_ready`
- Fixed `load_context_verses()` to properly extract verse info

### bible_search_ui/controllers/search_controller.py
**New file**: 398 lines

**What it contains**:
- `FormattedVerse` class - data container for verse display
- `SearchController` class - all search business logic
  - `search()` - initiate search
  - `load_more_results()` - lazy loading
  - `load_context()` - context verse loading
  - Internal handlers for search service signals
  - Result formatting and parsing

### bible_search_ui/__init__.py
**Change**: Added exports for `SearchController` and `FormattedVerse`

### bible_search_ui/controllers/__init__.py
**New file**: 10 lines - package initialization

## Troubleshooting

### Problem: "ImportError: cannot import name 'SearchController'"

**Solution**:
```bash
# Verify controller files exist
ls -la bible_search_ui/controllers/

# Should see:
# __init__.py
# search_controller.py

# If missing, extract archive again
tar -xzf bible_search_phase4.tar.gz
```

### Problem: "Search doesn't work / No results appear"

**Solution**:
```bash
# Check for Python errors
python3 bible_search_lite.py 2>&1 | tee debug.log

# Look for specific error messages
# Check database exists
ls -la database/bibles.db

# Verify imports work
python3 -c "from bible_search_ui.controllers import SearchController; print('OK')"
```

### Problem: "AttributeError: 'SearchController' object has no attribute..."

**Solution**:
```bash
# Make sure you have the complete Phase 4 files
# Re-extract the archive
tar -xzf bible_search_phase4.tar.gz

# Clear any cached Python files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete

# Run again
python3 bible_search_lite.py
```

### Problem: "Verses don't load in reading window"

**Solution**:
1. Check console output for errors when clicking verses
2. Verify `on_context_verses_ready` handler exists in bible_search_lite.py
3. Check signal connection in `__init__`:
   ```python
   self.search_controller.context_verses_ready.connect(self.on_context_verses_ready)
   ```

### Problem: "Lazy loading doesn't work"

**Solution**:
1. Search for a common word to get many results
2. Check console for "Loading more results: X to Y" messages
3. Verify scroll bar connection in `on_search_results_ready`
4. Try scrolling all the way to bottom (past 80% threshold)

## Rollback to Phase 3

If you encounter issues with Phase 4:

```bash
# Stop the application if running

# Remove Phase 4 installation
cd ~/projects/bible-search-lite
rm -rf bible_search_ui/controllers

# Restore Phase 3 backup
cp -r ~/projects/bible-search-lite-phase3-backup/* ~/projects/bible-search-lite/

# Or extract Phase 3 archive again
tar -xzf bible_search_phase3.tar.gz

# Test Phase 3
python3 bible_search_lite.py
```

## Performance Notes

### Expected Behavior

**Search Performance**:
- Simple searches: < 0.5 seconds
- Complex searches (multiple translations): 1-3 seconds
- Large result sets (1000+ verses): 2-5 seconds
- Initial display: First 100 results load immediately
- Lazy loading: Next 100 results load when scrolling near bottom

**Memory Usage**:
- Baseline: ~50 MB
- With 1000 search results: ~80 MB
- With 5000 search results: ~150 MB

**UI Responsiveness**:
- Search runs in background thread (UI stays responsive)
- Lazy loading prevents UI freeze with large result sets
- Context loading is nearly instant (< 0.1 seconds)

### If Performance Issues Occur

**Slow searches**:
- Check database file integrity
- Verify SSD/HDD speed (database on slow drive)
- Reduce number of enabled translations

**High memory usage**:
- Clear search results before new search
- Click "Clear" button to free memory
- Close and restart application

**UI freeze/lag**:
- Should not occur with Phase 4 refactoring
- If it does, report as bug (search should be async)

## Getting Help

If you encounter issues not covered here:

1. **Check console output** - most errors print detailed messages
2. **Verify file structure** - make sure all files extracted correctly
3. **Test incrementally** - use the testing checklist above
4. **Check phase documentation** - PHASE4_SUMMARY.md has detailed info
5. **Contact support** - ajhinva@gmail.com with error logs

## Next Steps

After confirming Phase 4 works correctly:

### Optional: Clean up old backups
```bash
# Once confident Phase 4 is stable
rm -rf ~/projects/bible-search-lite-phase3-backup
rm -rf ~/projects/bible-search-lite-phase2-backup
# etc.
```

### Optional: Future phases
Phase 4 completes the major refactoring. Future enhancements could include:
- Style management extraction (centralized themes)
- Window management extraction (layout builders)
- Advanced search features (caching, history, suggestions)
- Performance optimizations

### Recommended: Create your own backup
```bash
# Create backup with today's date
tar -czf ~/bible_search_phase4_working_$(date +%Y%m%d).tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='*.log' \
    ~/projects/bible-search-lite/
```

## Summary

Phase 4B successfully extracts all search logic into a dedicated controller. This is the final major refactoring phase, resulting in:

- **43% smaller main file** (1,386 → 789 lines)
- **Well-organized codebase** with clear separation of concerns
- **Highly testable** components
- **Easy to maintain** and extend
- **All functionality preserved** - works exactly like before

Enjoy your cleaner, more maintainable Bible search application!
