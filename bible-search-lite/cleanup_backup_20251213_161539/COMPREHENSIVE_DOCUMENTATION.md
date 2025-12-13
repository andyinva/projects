# Bible Search Lite - Complete Documentation
## Comprehensive Guide to Installation, Architecture, and Development

**Last Updated:** December 13, 2024  
**Current Version:** All Phases Complete (1-4)  
**Main File:** `bible_search_lite.py` (789 lines)  
**Architecture:** Modular MVC with service layer

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [Installation](#installation)
4. [Architecture](#architecture)
5. [Completed Phases](#completed-phases)
6. [Database Schema](#database-schema)
7. [Development Guide](#development-guide)
8. [Troubleshooting](#troubleshooting)
9. [Future Enhancements](#future-enhancements)

---

## Quick Start

### Prerequisites
- Python 3.8+
- PyQt6
- SQLite3 (included with Python)

### Installation
```bash
cd ~/projects/bible-search-lite
python3 bible_search_lite.py
```

### First Run
1. Application creates `user_data.db` automatically
2. Default translation: KJV
3. Sample verse appears in Subject Verses window
4. Configuration saved to `bible_search_lite_config.json`

---

## Project Overview

Bible Search Lite is a PyQt6-based Bible search and study application with a **verse-centric workflow**. The design emphasizes checkbox-based verse selection, multi-window navigation, and subject-based study organization.

### Core Design Principles
- **Verse-Centric:** All interactions revolve around selecting and organizing verses
- **Context-Aware:** Active window determines which operations are available
- **Study-Focused:** Built for topical Bible study with Groups and Subjects
- **Clean Architecture:** MVC pattern with clear separation of concerns

### Key Features
✅ Multi-translation Bible search (17 translations available)  
✅ Checkbox-based verse selection across windows  
✅ Subject-based verse organization with Groups hierarchy  
✅ Continuous reading with cross-chapter navigation  
✅ Verse comments with formatting  
✅ Context-sensitive window highlighting  
✅ Font size customization  
✅ Persistent configuration  

---

## Installation

### Standard Installation
```bash
# Navigate to project directory
cd ~/projects/bible-search-lite

# Ensure databases exist
ls -l database/bibles.db        # Main Bible database (627MB)
ls -l user_data.db              # User data (auto-created)

# Run application
python3 bible_search_lite.py
```

### Directory Structure
```
bible-search-lite/
├── bible_search_lite.py              # Main application (789 lines)
├── bible_search.py                   # Bible search engine
├── bible_search_service.py           # Search service layer
├── user_data.db                      # User data (auto-created)
├── bible_search_lite_config.json    # Configuration (auto-created)
├── bible_search_ui/                 # Modular package structure
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── widgets.py               # VerseItemWidget, VerseListWidget
│   │   ├── dialogs.py               # TranslationSelector, FontSettings
│   │   └── section_widget.py        # SectionWidget
│   ├── config/
│   │   ├── __init__.py
│   │   └── config_manager.py        # Configuration management
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── search_controller.py     # Search business logic
│   │   └── user_data_controller.py  # Groups/Subjects logic
│   └── services/
│       ├── __init__.py
│       └── user_data_service.py     # Database operations
├── database/
│   └── bibles.db                    # Bible texts (627MB, 17 translations)
└── run_bible_search.sh              # Launch script
```

---

## Architecture

### Design Pattern: MVC with Service Layer

```
┌─────────────────────────────────────────────────────────┐
│                  bible_search_lite.py                   │
│                    (Main Window)                        │
│              - UI Layout & Coordination                 │
│              - Event Handling                           │
│              - Window State Management                  │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  UI Widgets  │  │ Controllers  │  │   Services   │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ VerseItem    │  │ Search       │  │ BibleSearch  │
│ VerseList    │  │ Controller   │  │ Service      │
│ Section      │  │              │  │              │
│ Dialogs      │  │ UserData     │  │ UserData     │
│              │  │ Controller   │  │ Service      │
└──────────────┘  └──────────────┘  └──────────────┘
                          │                 │
                          └────────┬────────┘
                                   ▼
                          ┌──────────────┐
                          │  Databases   │
                          ├──────────────┤
                          │ bibles.db    │
                          │ user_data.db │
                          └──────────────┘
```

### Component Responsibilities

**Main Application (`bible_search_lite.py`)**
- Window layout and splitter management
- Event routing and signal connections
- Active window tracking and highlighting
- Top-level coordination

**UI Layer (`bible_search_ui/ui/`)**
- `widgets.py`: Reusable verse display components
- `dialogs.py`: Translation selector, font settings
- `section_widget.py`: Resizable window sections

**Controller Layer (`bible_search_ui/controllers/`)**
- `search_controller.py`: Search logic, result formatting
- `user_data_controller.py`: Groups/Subjects business logic

**Service Layer (`bible_search_ui/services/`)**
- `user_data_service.py`: Database CRUD operations
- `bible_search_service.py`: Background search operations

**Config Layer (`bible_search_ui/config/`)**
- `config_manager.py`: JSON configuration persistence

---

## Completed Phases

### Phase 1: Groups & Subjects Feature ✅
**Goal:** Add hierarchical organization for Bible study  
**Lines Added:** ~1,150 lines across multiple files

**New Database Tables:**
- `groups` - Subject categories
- `subjects` - Topics within groups  
- `subject_verses` - Verses assigned to subjects
- `verse_comments` - Comments on subject verses

**New Components:**
- `UserDataService` - Database operations
- `UserDataController` - Business logic
- Subject management UI in Window 4
- Comments display in Window 5

**Key Features:**
- Create/edit/delete Groups and Subjects
- Assign verses to Subjects via Acquire button
- Add formatted comments to verses
- Hierarchical organization (Group → Subject → Verses)

### Phase 2: Dialog Extraction ✅
**Goal:** Modularize dialog windows  
**Lines Moved:** 117 lines → `dialogs.py`  
**Reduction:** 992 → 901 lines (-9.2%)

**Extracted Components:**
- `TranslationSelectorDialog` (multi-select translation picker)
- `FontSettingsDialog` (font size customization)

**Benefits:**
- Cleaner main file
- Reusable dialog components
- Better separation of concerns

### Phase 3: Config Manager Extraction ✅
**Goal:** Centralize configuration management  
**New File:** `config_manager.py` (280 lines)  
**Reduction:** 901 → 886 lines

**ConfigManager Features:**
- JSON file operations (load/save)
- Default configuration generation
- Config merging (preserves user settings)
- Config validation and error handling

**Configuration Sections:**
- Window geometry and splitter sizes
- Font settings (title and verse fonts)
- Translation selections
- Checkbox states
- Search history

### Phase 4: Search Controller Extraction ✅
**Goal:** Separate search business logic from UI  
**New File:** `search_controller.py` (398 lines)  
**Reduction:** 886 → 789 lines (-11%)

**SearchController Features:**
- Search execution and result formatting
- Verse formatting for display
- Search history management
- Book abbreviation handling
- Progress tracking

**FormattedVerse Class:**
```python
@dataclass
class FormattedVerse:
    verse_id: str
    translation: str
    book_abbrev: str
    chapter: int
    verse_number: int
    text: str
```

### Refactoring Summary
**Overall Impact:**
- Started: 992 lines (monolithic)
- Ended: 789 lines (modular)
- **Reduction: 203 lines (-20%)**
- **Added:** ~1,800 lines across modules
- **Total codebase:** ~2,600 lines (well-organized)

---

## Database Schema

### Bible Database (`database/bibles.db`)
**Size:** 627MB  
**Records:** 507,055 verse texts across 17 translations

#### Core Tables
```sql
-- Books of the Bible
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL,
    order_index INTEGER NOT NULL
);
-- 66 books, Genesis to Revelation

-- Unique verse references
CREATE TABLE verses (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
-- 32,584 unique verse references

-- Verse texts in each translation
CREATE TABLE verse_texts (
    id INTEGER PRIMARY KEY,
    verse_id INTEGER NOT NULL,
    translation_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (verse_id) REFERENCES verses(id),
    FOREIGN KEY (translation_id) REFERENCES translations(id)
);
-- 475,055 verse texts (32,584 verses × ~15 translations)

-- Bible translations
CREATE TABLE translations (
    id INTEGER PRIMARY KEY,
    abbreviation TEXT NOT NULL,
    name TEXT NOT NULL
);
-- 17 translations: KJV, ASV, DRB, DBT, ERV, WBT, WEB, YLT, etc.
```

### User Database (`user_data.db`)
**Auto-created on first run**  
**Contains:** User's study organization and notes

#### User Tables
```sql
-- Subject groups (categories)
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects within groups
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
);

-- Verses assigned to subjects
CREATE TABLE subject_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    verse_reference TEXT NOT NULL,
    translation TEXT NOT NULL,
    verse_text TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Comments on subject verses
CREATE TABLE verse_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_verse_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_verse_id) REFERENCES subject_verses(id) ON DELETE CASCADE
);
```

---

## Development Guide

### Code Organization Principles

1. **Separation of Concerns**
   - UI: Display and user interaction only
   - Controllers: Business logic and coordination
   - Services: Database and external operations
   - Config: Persistent settings management

2. **Signal-Based Communication**
   - Use PyQt signals for component communication
   - Avoid direct method calls between layers
   - Decouple components for testability

3. **Consistent Naming**
   - `show_*()` - Display dialog/window
   - `on_*()` - Event handler
   - `get_*()` - Retrieve data
   - `set_*()` - Update data
   - `create_*()` - Build UI components

### Adding New Features

#### Example: Adding a New Dialog

1. **Create dialog class in `bible_search_ui/ui/dialogs.py`:**
```python
class MyNewDialog(QDialog):
    """Dialog for [purpose].
    
    Signals:
        data_changed: Emitted when user confirms changes
    """
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My New Feature")
        self.setup_ui()
    
    def setup_ui(self):
        """Create dialog layout."""
        # ... UI code ...
```

2. **Import in main application:**
```python
from bible_search_ui.ui.dialogs import MyNewDialog
```

3. **Add menu/button handler:**
```python
def show_my_feature(self):
    """Show my new feature dialog."""
    dialog = MyNewDialog(self)
    dialog.data_changed.connect(self.on_feature_data_changed)
    dialog.exec()
```

### Testing Guidelines

**Manual Testing Workflow:**
1. Start application fresh
2. Test search functionality
3. Test Groups/Subjects creation
4. Test verse acquisition
5. Test comments
6. Restart and verify persistence

**Key Test Cases:**
- Empty database (first run)
- Configuration persistence
- Window state restoration
- Error handling (missing database)

---

## Troubleshooting

### Database Issues

**Problem:** `database/bibles.db not found`  
**Solution:** Ensure database exists in `database/` subdirectory
```bash
ls -lh database/bibles.db
# Should show ~627MB file
```

**Problem:** `user_data.db` not created  
**Solution:** Check write permissions in project directory
```bash
ls -l user_data.db
# File should auto-create on first run
```

### UI Issues

**Problem:** Windows not resizing  
**Solution:** Delete config and restart
```bash
rm bible_search_lite_config.json
python3 bible_search_lite.py
```

**Problem:** Fonts too small/large  
**Solution:** Use Settings gear icon (⚙) → Font Settings

### Performance Issues

**Problem:** Search is slow  
**Solution:** Limit translations in Translation Settings
- Default: KJV only
- Select fewer translations for faster searches

**Problem:** Large result sets lag  
**Solution:** Use more specific search terms
- Wildcard searches (`love*`) can return thousands of results
- Combine terms with AND for narrower results

---

## Future Enhancements

### Potential Phase 5: Export/Import
- Export subject collections to files
- Share study notes with others
- Import from other Bible study tools

### Potential Phase 6: Advanced Search
- Boolean search operators (AND, OR, NOT)
- Proximity search (words within N verses)
- Regular expression support
- Search within search results

### Potential Phase 7: Study Tools
- Cross-reference lookup
- Original language tools (Strong's numbers)
- Commentary integration
- Verse comparison across translations

### Potential Phase 8: Performance
- Database indexing optimization
- Lazy loading for large result sets
- Search result caching
- Multi-threaded search

---

## Quick Reference

### Keyboard Shortcuts
*Future enhancement - not yet implemented*

### Search Syntax
- **Simple:** `love` - Find "love" in any verse
- **Wildcard:** `love*` - Find love, loved, loving, etc.
- **Exact Phrase:** `"in the beginning"` - Exact phrase match
- **Verse Reference:** `John 3:16` - Find specific verse
- **Range:** `John 3:16-18` - Multiple verses

### Window Layout
1. **Message Window** - Status and search info
2. **Search Results** - Search findings with checkboxes
3. **Reading Window** - Continuous Bible reading context
4. **Subject Verses** - Your organized study collection
5. **Comments** - Notes on subject verses

### File Locations
- **Config:** `bible_search_lite_config.json`
- **User Data:** `user_data.db`
- **Bible Data:** `database/bibles.db`
- **Logs:** Console output only (no log files)

---

## Credits

**Developer:** Andrew Hopkins  
**Email:** ajhinva@gmail.com  
**Repository:** ~/projects/bible-search-lite  
**Platform:** WSL Ubuntu / Windows 11  
**Framework:** PyQt6  
**Database:** SQLite3  

---

## Changelog

**December 13, 2024 - All Phases Complete**
- Phase 4: Search Controller extraction complete
- Codebase: 789 lines main + 1,800 lines modules
- Architecture: Clean MVC with service layer
- Status: Production ready

**December 9, 2024 - Phases 1-3 Complete**
- Phase 3: Config Manager extracted
- Phase 2: Dialogs modularized
- Phase 1: Groups & Subjects implemented

**December 5, 2024 - Project Start**
- Initial PyQt6 implementation
- Bible search functionality
- Multi-window interface

---

**End of Documentation**
