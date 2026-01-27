# Bible Search Lite v1.1.1 Release Notes

**Release Date:** January 27, 2026

This maintenance release includes critical bug fixes for Windows installations, database compatibility improvements, and important copyright compliance updates.

## 🐛 Critical Bug Fixes

### Window 5 Subject Comments
- **Fixed:** Add Comment button not working on fresh installations
- **Fixed:** Missing `comments` column in subject_verses table
- **Fixed:** "no such column: modified_data" error when saving comments
- **Fixed:** Invisible text and font dropdown in comment editor on Windows
- **Solution:** Added automatic database schema migration and proper text styling

### Setup Scripts (Windows Installation)
- **Fixed:** setup.py and setup_win11.py creating outdated database schema
- **Fixed:** Missing comments column causing Window 5 to malfunction
- **Impact:** Fresh Windows installations now work correctly without manual fixes

### PowerShell Installer
- **Fixed:** Execution policy errors on Windows
- **Fixed:** Parser errors with here-string syntax
- **Fixed:** Unix/Windows line ending compatibility
- **Added:** Clear documentation for execution policy workarounds

## ✨ New Features

### Visual Feedback
- **Added:** Green flash effect on Create button when subject is saved
- **Added:** Visual confirmation for successful subject creation in Windows 3 & 4
- **Duration:** 500ms green flash, then returns to original appearance

### Translation Selector
- **Changed:** Translation list layout from 4 columns to 2 columns
- **Benefit:** Better readability with longer translation names and publication dates

## 📄 Copyright Compliance

### NET Bible® Copyright
- **Added:** NET Bible® copyright notice to LICENSE file
- **Added:** NET Bible® copyright display in Help menu
- **Required:** Proper attribution for NET Bible® translation included in bibles.db
- **Reference:** https://netbible.org/copyright/

## 🔧 Technical Improvements

### Database Migration
- **Added:** Automatic migration for missing `comments` column
- **Added:** Automatic fix for `modified_data` → `modified_date` typo
- **Added:** Transaction safety and rollback on errors
- **Benefit:** Seamless upgrades from older database versions

### Text Visibility (Windows)
- **Fixed:** Black text explicitly set on white background in comment editor
- **Fixed:** Font size dropdown now visible with proper styling
- **Issue:** Windows themes causing white-on-white invisible text

### Database Distribution
- **Added:** DATABASE_UPDATE_NOTICE.md for users with old database
- **Added:** database/DOWNLOAD_DATABASE.md with download instructions
- **Note:** bibles.db (406 MB) must be downloaded separately from GitHub Releases

## 📝 Files Modified

### Core Files
- `bible_search_lite.py` - Green flash effect, license display
- `subject_manager.py` - Database migration logic
- `subject_comment_manager.py` - Text visibility fixes
- `subject_verse_manager.py` - Green flash effect
- `LICENSE` - NET Bible® copyright added
- `VERSION.txt` - Updated to v1.1.1

### Setup Scripts
- `setup.py` - Updated database schema
- `setup_win11.py` - Updated database schema

### UI Components
- `bible_search_ui/ui/dialogs.py` - 2-column translation layout
- `.gitignore` - Updated for subjects.db tracking

## 🔄 Upgrade Path

### From v1.1.0
Simply pull the latest code or download v1.1.1:
- Database migrations run automatically
- No manual intervention required
- All fixes applied on first run

### From v1.0.x
1. Pull latest code or download v1.1.1
2. Download new bibles.db (37 translations) from Releases
3. Database migrations handle schema updates automatically

## ⚠️ Known Issues

- Blue focus border around active windows not visible on Windows 11 (cosmetic only)
- Function works correctly, just visual indicator missing

## 📊 Statistics

- **Commits since v1.1.0:** 15
- **Files changed:** 10
- **Bug fixes:** 8
- **New features:** 2
- **Documentation:** 3

## 🙏 Acknowledgments

This release includes the NET Bible® translation:
- Copyright ©1996, 2019 by Biblical Studies Press, L.L.C.
- Used with permission for non-commercial use
- http://netbible.com

---

**Full Changelog:** https://github.com/andyinva/bible-search-lite/compare/v1.1.0...v1.1.1
