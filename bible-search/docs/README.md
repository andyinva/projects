# Bible Search Interface

A comprehensive Bible search program with advanced search capabilities, built with Python and tkinter, following object-oriented programming principles.

## Features

### Window Layout
- **6 window sections** arranged vertically with proper borders and titles
- **Synchronized width resizing** - all windows maintain the same width
- **Independent height resizing** for the bottom 4 windows
- **Static height** for the top 2 windows

### Window Sections
1. **Search Settings** - Search options with Case Sensitive, Unique Verse, and Abbreviate Results checkboxes, plus gear button for translation settings
2. **Message Window** - Displays program messages and search status updates
3. **Search Results** - Search entry field, Search/Export buttons, and formatted search results display
4. **Reading Window** - Continuous verse reading with dynamic translation header
5. **Subject Verses** - Subject management with verse acquisition from search results
6. **Verse Comments** - Comment editor for annotating verses with Add/Edit/Save/Delete functionality

### Search Capabilities
- **Word Search** with wildcards: `*` (any characters), `?` (single character), `!` (NOT operator)
- **Boolean operators**: AND, OR with proper precedence
- **Exact phrase search** using quotes: "exact phrase"
- **Verse reference search**: Gen 1:1, Genesis 1:1, Gen 1:1-9 (range support)
- **Automatic detection** between word searches and verse references
- **Highlighted results** with search terms enclosed in [ ] brackets
- **Case sensitive** search option
- **Unique verse** filtering (shows only highest priority translation per verse)
- **Result abbreviation** for space-efficient display

### Translation Management
- **17+ Bible translations** loaded from database
- **Translation settings dialog** with enable/disable checkboxes
- **Custom sort order** for result display priority
- **3-letter abbreviations** for space-efficient display
- **Full translation names** in reading window headers

### Configuration Management
- **JSON-based settings** stored in `bible_search_config.json`
- **Automatic persistence** of window dimensions and heights
- **Default configuration** created automatically if file doesn't exist

## Usage

### Running the Application

```bash
python3 bible_search_interface.py
```

### Running the Enhanced Demo

```bash
python3 test_interface.py
```

### Testing Resize Functionality

1. **Width Resizing**: Drag the main window from the left or right edge - all 6 windows will resize together
2. **Height Resizing**: Drag the bottom border of windows 3-6 to resize their height independently
3. **Settings Persistence**: Close and reopen the application - your window sizes will be remembered

### Search Examples
- **Word searches**: `love`, `form*` (finds forming, formerly), `?od` (finds God, nod), `!evil` (excludes evil)
- **Boolean searches**: `love AND mercy`, `faith OR hope`, `"eternal life"` (exact phrase)
- **Verse references**: `Gen 1:1`, `Genesis 1:1`, `Matthew 5:3-12` (verse range)
- **Complex searches**: `love* AND mercy !hate` (love words with mercy, excluding hate)

### Using the Interface

#### Window 1 - Search Settings
- **Checkboxes**: Case Sensitive, Unique Verse, Abbreviate Results
- **Gear button (⚙)**: Access translation settings dialog
- **Translation Settings**: Enable/disable translations, set display priority order

#### Window 2 - Message Window
- Displays search status, result counts, and program messages

#### Window 3 - Search Results
- **Search field**: Enter search terms (left side)
- **Search button**: Execute search (next to field)
- **Export button**: Save results to text file (right side)
- **Results list**: Formatted as "KJV Gen 1:1 In the beginning God created..." 
- **Multiple selection**: Select verses for subject management

#### Window 4 - Reading Window
- **Dynamic header**: Shows full translation name of selected verse
- **Continuous reading**: Displays selected verse plus following verses
- **Automatic update**: Changes when you select different search results

#### Window 5 - Subject Verses
- **Subject field**: Enter/select subject name
- **Create Subject**: Add new subject to database
- **Acquire Verses**: Move selected verses from search results to current subject
- **Subject list**: View verses organized by subject

#### Window 6 - Verse Comments
- **Comment editor**: Add personal notes to verses
- **Button controls**: Add Comment, Edit, Save, Delete
- **Automatic activation**: Buttons enable when verse is selected in Subject window

## Code Structure

### Main Classes

- `BibleSearchInterface`: Main application class managing the entire interface
- `ConfigManager`: Handles JSON configuration loading, saving, and management
- `ResizableFrame`: Custom frame widget with drag-to-resize functionality

### Key Methods

- `create_window_sections()`: Sets up all 6 window sections
- `on_window_resize()`: Handles synchronized width resizing
- `on_closing()`: Saves configuration when application closes
- `add_message()`: Adds messages to the message window

## Configuration File

The `bible_search_config.json` file stores:

```json
{
  "window_width": 800,
  "window_height": 600,
  "window_heights": {
    "search_window": 150,
    "reading_window": 200,
    "subject_verses": 150,
    "verse_comments": 150
  },
  "static_heights": {
    "search_settings": 100,
    "message_window": 60
  }
}
```

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- Standard library modules: json, os, typing

## Future Enhancements

This interface provides the foundation for:
- SQLite database integration
- Bible verse search functionality
- Advanced search filtering
- Verse highlighting and bookmarking
- Export functionality
- Custom themes and styling

## Architecture Notes

The design follows object-oriented principles with:
- Clear separation of concerns
- Configurable and maintainable components
- Event-driven architecture for user interactions
- Proper resource management and cleanup