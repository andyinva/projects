# Phase 4 - Hotfix #2: Translation Selector Bug

## Issue
When clicking the "Translations" button, the application crashed with:
```
AttributeError: 'BibleSearchProgram' object has no attribute 'bible_search'
```

## Root Cause
The `show_translation_selector()` method was still referencing `self.bible_search.translations` even though we moved `bible_search` into the `SearchController` during Phase 4 refactoring.

## Fix
Changed line 451 in `bible_search_lite.py`:

**Before:**
```python
self.bible_search.translations,
```

**After:**
```python
self.search_controller.bible_search.translations,
```

## File Updated
- `bible_search_lite.py` (line 451)

## How to Apply
Replace your `bible_search_lite.py` with the fixed version:
- `bible_search_lite_phase4_fixed.py`

## Testing
1. Run the application
2. Click the "Translations" button
3. Dialog should open successfully showing all available translations
4. Select/deselect translations and click OK
5. Verify the button text updates with the count

## Related
- Original hotfix: PHASE4_HOTFIX.md (FormattedVerse import error)
- This is the second hotfix for Phase 4
