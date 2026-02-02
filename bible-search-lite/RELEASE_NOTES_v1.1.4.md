# Bible Search Lite v1.1.4 Release Notes

**Release Date:** February 2, 2026

## Overview
This release introduces significant enhancements to the search and highlighting system, including two-color highlighting for wildcard searches, improved possessive form matching, and a reorganized translation selector. The database has also been cleaned to ensure accurate highlighting.

---

## 🎨 New Features

### Two-Color Highlighting for Wildcard Searches
- **Base words** are now highlighted in **green** (light green background)
- **Variations** (like possessive endings) are highlighted in **blue** (light blue background)
- Example: Searching for `"father*"` shows "father" in green and "'s" in blue
- Makes it easy to distinguish base words from their variations

### Enhanced Possessive Form Matching
- Wildcard searches now automatically match possessive forms
- Searching for `"father*"` now matches: father, fathers, father's, fathers'
- Apostrophes are properly handled in all search patterns
- Works with both regular apostrophes (') and typographic apostrophes (')

### Translation Selector Improvements
- **Old English translations grouped separately** at the bottom of the translation selector
- Added divider labeled "Translations With Old English Wording"
- Grouped translations: BIS, COV, WYC, GN2, GEN, TYD, TYN
- **"Select All" button now skips old English translations** for easier modern translation selection
- Added missing translation dates:
  - SLT (Smith's Literal Translation) - 1876
  - EDG (Easy-to-Read Version) - 1864
- Removed duplicate dates that were appearing next to translation names

### Filter Window Enhancements
- Filter window now shows all word variations including possessives
- Example: `"father*"` filter shows: Father, Fathers, Father's, Fatherless, etc.
- **Smart re-highlighting**: When filtering to specific words, only those words are highlighted
  - Search `"father*"` → all variations highlighted
  - Filter to only "Father's" → only "father's" is highlighted, not plain "father"
- Filter properly handles apostrophes and contractions

### Contraction Search Support
- Searches like `"?'*"` now correctly match contractions
- Examples: it's, I'm, isn't, I'll, won't, etc.
- Contractions are highlighted with single-color (green) highlighting
- Fixed apostrophe handling in wildcard patterns

---

## 🐛 Bug Fixes

### Database Cleanup
- Removed pre-existing brackets `[`, `]`, `{`, `}` from verse text in the database
- These were causing incorrect highlighting of words that weren't part of the search
- All ~31,000+ verses have been cleaned

### Bracket Notation Handling
- Fixed issue where curly braces `{` `}` weren't being removed during filtering
- Filter now properly extracts complete words including possessives
- Resolved issue where "father's" would be split into "father" and "s"

### Wildcard Pattern Improvements
- Changed wildcard pattern from `\w*` to `[a-zA-Z]*(?:[''][a-zA-Z]*)*`
- This allows wildcards to properly match words containing apostrophes
- Consistent pattern usage between search and filter extraction

### Parentheses in Search Queries
- Fixed issue where parentheses in queries like `("father*")` were breaking wildcard matching
- Parentheses are now properly stripped during query parsing

---

## 📚 Documentation Updates

### SEARCH_OPERATORS.md
- Updated to document automatic possessive form matching
- Added examples showing `"father*"` matches father's
- Clarified wildcard behavior with apostrophes

---

## 🔧 Technical Improvements

### Code Architecture
- Implemented two-stage highlighting system:
  1. `bible_search.py` adds bracket notation: `[base]{variation}`
  2. `widgets.py` converts brackets to HTML with colors
- Separated highlighting logic from display logic for better maintainability
- Added comprehensive word extraction patterns supporting possessives

### Performance
- Optimized bracket notation processing
- Efficient regex patterns for apostrophe handling
- Smart re-highlighting only when filtering is applied

---

## 📦 Database Updates

### Cleaned Verse Text
- All verses in the database have been processed to remove:
  - Square brackets `[` `]`
  - Curly braces `{` `}`
- Ensures clean text for accurate highlighting
- Total verses processed: 31,102+ across all translations

---

## 🎯 User Experience Improvements

### Visual Clarity
- Two-color highlighting makes word variations instantly recognizable
- Filtered search results only highlight relevant words
- Clean, uncluttered highlighting without extraneous brackets

### Intuitive Workflow
- "Select All" translations button respects user preference for modern vs. old English
- Filter window clearly shows all word variations with counts
- Smart filtering maintains search context while focusing on selected words

---

## 📝 Files Modified

### Core Search & Highlighting
- `bible_search.py` - Bracket notation, possessive matching, two-color logic
- `bible_search_lite.py` - Filter extraction, re-highlighting, word pattern matching
- `bible_search_ui/ui/widgets.py` - HTML rendering for two-color highlighting
- `bible_search_ui/ui/dialogs.py` - Translation selector grouping

### Documentation
- `SEARCH_OPERATORS.md` - Possessive matching documentation
- `VERSION.txt` - Updated to v1.1.4

### Database
- `database/bibles.db` - Cleaned all verse text (verse_texts table)

---

## 🚀 Upgrade Instructions

### From Previous Versions
1. Download the new release package
2. Extract to your desired location
3. **Important:** The database has been updated - use the new `database/bibles.db` file
4. Run `python3 bible_search_lite.py` (Linux/Mac) or `bible_search_lite.py` (Windows)
5. Your configuration and search history will be preserved

### New Installation
1. Extract the release package
2. Ensure Python 3.8+ is installed
3. Install dependencies: `pip install PyQt6`
4. Run `python3 bible_search_lite.py`

---

## 💡 Usage Examples

### Two-Color Highlighting
Search: `"father*"`
Results show:
- father (green)
- father**'s** (green + **blue**)
- father**s** (green + **blue**)

### Filtering with Re-Highlighting
1. Search: `"father*"` → all variations highlighted
2. Open Filter → uncheck all except "Father's"
3. Click Search → only "father's" highlighted

### Contraction Search
Search: `"?'*" AND "*'*"`
Matches: it's, I'm, isn't, don't, etc.
All highlighted in green

---

## 🙏 Acknowledgments

Special thanks to users who provided feedback on highlighting behavior and suggested the filter re-highlighting feature!

---

## 📞 Support

- **GitHub Issues:** https://github.com/yourusername/bible-search-lite/issues
- **Documentation:** See README.md and SEARCH_OPERATORS.md

---

**Full Changelog:** v1.1.3...v1.1.4
