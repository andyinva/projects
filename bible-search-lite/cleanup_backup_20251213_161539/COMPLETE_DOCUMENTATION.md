# Bible Search Lite - Complete Documentation
**Last Updated:** December 13, 2024
**Version:** Phase 1 Complete

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Installation & Setup](#installation--setup)
3. [Current Features](#current-features)
4. [Architecture](#architecture)
5. [Phase 1: Groups & Subjects](#phase-1-groups--subjects)
6. [Database Schema](#database-schema)
7. [Development Guide](#development-guide)
8. [Future Phases](#future-phases)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

Bible Search Lite is a PyQt6-based Bible search and study application designed for verse-centric Bible study with hierarchical organization through Groups and Subjects.

### Design Philosophy
- **Verse-Centric**: All interactions revolve around verse selection and organization
- **Context-Aware**: Actions respond to which window is currently active
- **Study-Focused**: Built for collecting verses into topical subject studies
- **Hierarchical**: Groups → Subjects → Verses → Comments

### Technology Stack
- **Language**: Python 3.8+
- **UI Framework**: PyQt6
- **Database**: SQLite3 (two databases: bibles.db for Bible text, user_data.db for user studies)
- **Architecture**: MVC pattern with service layer

---

## Installation & Setup

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip

# Install PyQt6
pip install PyQt6
```

### Running the Application
```bash
cd ~/projects/bible-search-lite
python3 bible_search_lite.py

# Or use the launcher script
./run_bible_search.sh
```

### First-Time Setup
On first launch:
1. `user_data.db` database is automatically created
2. Sample groups and subjects are added:
   - Group: "New Testament" with subjects: Faith, Prayer, Love
   - Group: "Old Testament" with subjects: Creation, Covenant, Prophecy
3. Configuration file `bible_search_lite_config.json` is created

---

## Current Features

### ✅ Working Functionality

**Section 1: Message Window**
- Status messages and feedback
- Settings gear icon (font size adjustment)

**Section 2: Search Results**
- Full-text Bible search across 17 translations
- Wildcard support (*, ?) and Boolean operators (AND, OR, !)
- Verse reference search (e.g., "Gen 1:1", "John 3:16")
- Checkboxes for verse selection
- Click verses to navigate to Reading Window

**Section 3: Reading Window**
- Shows context verses around selected passage
- Loads entire chapter for continuous reading
- Highlighted verse from search/subject selection
- Checkboxes for selecting additional verses

**Section 4: Subject Verses** (Phase 1 - NEW!)
- **Row 1 - Groups**: [Group Dropdown ▼] [New Group] [Delete Group]
- **Row 2 - Subjects**: [Subject Dropdown ▼] [New Subject] [Delete Subject] [Find]
- **Row 3 - Operations**: [Acquire] [Clear] [Tips] [Copy] [Export]
- Display of verses organized under selected subject
- Navigate to Reading Window by clicking verses

**Section 5: Comments**
- Placeholder (ready for Phase 3 implementation)

### Window Management
- Active window highlighting (blue border + light blue background)
- Click anywhere in a window to make it active
- Resizable sections via splitter controls

### Verse Acquisition Workflow
1. Search for verses in Section 2
2. Check desired verses with checkboxes
3. Select Group and Subject in Section 4
4. Click "Acquire" - verses are saved to database
5. Verses appear in Section 4 under selected subject

---

## Architecture

### Directory Structure
```
bible-search-lite/
├── bible_search_lite.py          # Main application (UI layer)
├── bible_search.py                # Bible search engine
├── bible_search_service.py        # Search service for PyQt6
├── bible_search_lite_config.json  # User configuration
├── run_bible_search.sh            # Launcher script
├── database/
│   └── bibles.db                  # Bible text (read-only, 627MB)
├── user_data.db                   # User studies (created on first run)
└── bible_search_ui/               # Modular architecture
    ├── config/
    │   └── config_manager.py      # Configuration management
    ├── controllers/
    │   ├── search_controller.py   # Search business logic
    │   └── user_data_controller.py # Groups/subjects business logic
    ├── services/
    │   └── user_data_service.py   # Database operations
    └── ui/
        ├── widgets.py             # Reusable UI components
        └── dialogs.py             # Dialog windows
```

### MVC Pattern
- **Model**: `user_data_service.py` (database operations)
- **View**: `bible_search_lite.py` (PyQt6 UI)
- **Controller**: `user_data_controller.py` (business logic, signals/slots)

### Signal-Driven Architecture
All operations use PyQt6 signals:
- `groups_loaded` - Group list updated
- `subjects_loaded` - Subject list updated
- `verses_loaded` - Verse list updated
- `operation_success` - Success message
- `operation_failed` - Error message

---

## Phase 1: Groups & Subjects

### Features Implemented
1. **Group Management**
   - Create groups to organize study topics
   - Delete groups (cascades to subjects and verses)
   - Select active group from dropdown
   - Persistent selection across sessions

2. **Subject Management**
   - Create subjects within groups
   - Same subject name allowed in different groups
   - Delete subjects (cascades to verses and comments)
   - Select active subject from dropdown
   - Persistent selection across sessions

3. **Verse Acquisition**
   - Select verses in Search or Reading windows
   - Acquire into current group/subject
   - Duplicate detection (same verse not added twice)
   - Automatic clearing of checkboxes after acquisition

4. **Data Persistence**
   - All data saved to `user_data.db` SQLite database
   - Current selections saved in config file
   - Restored on application restart

### Usage Examples

**Create a Study Topic:**
1. Click "New Group" → Enter "Doctrine" → OK
2. Select "Doctrine" from group dropdown
3. Click "New Subject" → Enter "Trinity" → OK
4. Subject "Trinity" is now active

**Collect Verses:**
1. Search for "God Father Son Spirit"
2. Check relevant verses
3. Ensure "Doctrine" group and "Atonement" subject are selected
4. Click "Acquire"
5. Verses appear in Section 4

**Organize Studies:**
- Group: "New Testament" → Subjects: Faith, Hope, Love, Prayer
- Group: "Old Testament" → Subjects: Creation, Prophets, Covenant
- Group: "Doctrine" → Subjects: Trinity, Salvation, Sanctification

---

## Database Schema

### user_data.db Tables

**groups** - Top-level organization
```sql
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL
);
```

**subjects** - Topics within groups
```sql
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    UNIQUE(group_id, name)
);
```

**subject_verses** - Verses collected under subjects
```sql
CREATE TABLE subject_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    verse_reference TEXT NOT NULL,
    translation TEXT NOT NULL,
    verse_text TEXT NOT NULL,
    order_index INTEGER DEFAULT 0,
    added_at TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);
```

**verse_comments** - Comments for verses (ready for Phase 3)
```sql
CREATE TABLE verse_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_verse_id INTEGER NOT NULL,
    comment_text TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (subject_verse_id) REFERENCES subject_verses(id) ON DELETE CASCADE
);
```

### bibles.db Tables (Read-Only)
- **books** - 66 Bible books with canonical ordering
- **verses** - 32,584 unique verse references
- **verse_texts** - 475,055 verse texts across 17 translations
- **translations** - 17 Bible versions (KJV, ASV, NIV, ESV, etc.)

---

## Development Guide

### Code Organization
- Keep database logic in service layer (`user_data_service.py`)
- Keep business logic in controllers (`user_data_controller.py`)
- Keep UI logic in main application (`bible_search_lite.py`)
- Follow existing patterns for consistency

### Adding New Features
1. **Service Layer** - Add database methods
2. **Controller Layer** - Add business logic with signals
3. **UI Layer** - Add UI components and connect signals
4. **Test** - Verify end-to-end functionality

### Naming Conventions
- Methods: `snake_case`
- Classes: `PascalCase`
- Database columns: `snake_case`
- Constants: `UPPER_CASE`
- Signals: `signal_name` (lowercase with underscores)

### Error Handling Pattern
```python
try:
    result = self.user_data_service.create_group(name, description)
    self.operation_success.emit(f"Group '{name}' created")
except sqlite3.IntegrityError:
    self.operation_failed.emit(f"Group '{name}' already exists")
except Exception as e:
    self.operation_failed.emit(f"Error: {str(e)}")
```

---

## Future Phases

### Phase 2: Verse Management (Planned)
- Verse reordering (drag & drop)
- Verse deletion from subjects
- Verse editing (change translation/reference)
- "Find Subject" search implementation

### Phase 3: Comments System (Planned)
- Rich text editor in Section 5
- Save/load comments for verses
- Formatting toolbar (bold, italic, colors)
- HTML storage in database

### Phase 4: Export/Import (Planned)
- Export groups/subjects to JSON
- Import shared studies
- Merge strategies (append vs replace)
- Backup/restore functionality

### Phase 5: Sharing Features (Planned)
- Email contacts database
- Pre-made email templates
- Installation guide generation
- Cloud sync (optional)

---

## Troubleshooting

### Database Issues

**Problem: "user_data.db not found"**
- Solution: Delete `user_data.db` and restart app (will recreate with sample data)

**Problem: "Duplicate verses not being detected"**
- Solution: Verse reference must match exactly (translation + reference)

**Problem: "Group/Subject not saving"**
- Check: Ensure unique names within scope
- Check: Verify `user_data.db` has write permissions

### UI Issues

**Problem: "Acquire button not enabled"**
- Ensure: Group AND subject are selected
- Ensure: At least one verse is checked in Search/Reading window
- Check: Active window has selections (blue border)

**Problem: "Verses not appearing in Section 4"**
- Check: Correct subject is selected
- Check: Database saved successfully (look for success message)
- Try: Reselect subject to refresh display

### Performance Issues

**Problem: "Slow search with many results"**
- Solution: Use more specific search terms
- Solution: Enable "Unique Verse" to reduce duplicates
- Note: First 100 results load quickly, more load on scroll

**Problem: "Application slow to start"**
- Check: `bibles.db` location (should be in database/ folder)
- Check: Disk space available
- Check: No database corruption

### Configuration Issues

**Problem: "Lost group/subject selections on restart"**
- Check: `bible_search_lite_config.json` exists
- Check: File has write permissions
- Solution: Manually edit config to restore selections

**Problem: "Window sizes not saving"**
- Solution: Close app normally (don't kill process)
- Check: Config file has splitter_sizes section

---

## Quick Reference

### Search Syntax
- **Wildcard**: `love*` (love, loved, loving)
- **Single char**: `lo?e` (love, lose)
- **Phrase**: `"in the beginning"`
- **Boolean**: `faith AND hope` or `love OR charity`
- **Exclude**: `!sin` (exclude verses with "sin")
- **Reference**: `Gen 1:1` or `John 3:16`
- **Range**: `Gen 1:1-5`

### Keyboard Shortcuts
- `Ctrl+F` - Focus search box (planned)
- `Ctrl+G` - Create new group (planned)
- `Ctrl+S` - Create new subject (planned)

### File Locations
- **Bible Database**: `database/bibles.db` (627MB)
- **User Database**: `user_data.db` (created on first run)
- **Configuration**: `bible_search_lite_config.json`
- **Backups**: `backups/` directory (if created)

---

## Credits & License

**Project**: Bible Search Lite  
**Developer**: Andrew Hopkins (ajhinva@gmail.com)  
**Python Version**: 3.8+  
**PyQt Version**: PyQt6  
**License**: Personal project - not licensed for distribution

---

**End of Documentation**
**Last Updated**: December 13, 2024
**Version**: Phase 1 Complete (Groups & Subjects feature implemented)
