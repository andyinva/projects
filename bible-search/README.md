\# Bible Search - Verse-Centric Study Application



A PyQt6-based Bible search and study application designed around a verse-centric workflow with checkbox selection and subject organization.



\## Project Overview



This application provides an intuitive interface for searching, reading, and organizing Bible verses. The core design principle is verse-centricity: verses can be selected via checkboxes across multiple windows and collected into subject-based studies.



\### Design Philosophy



\- \*\*Verse-Centric\*\*: All interactions revolve around verse selection and organization

\- \*\*Context-Aware\*\*: Actions respond to which window is currently active

\- \*\*Study-Focused\*\*: Built for collecting verses into topical subject studies

\- \*\*Simple \& Clear\*\*: Visual feedback shows active windows and available actions



\## Current Features



\### Working Functionality



✅ \*\*Search Results Window (Window 2)\*\*

\- Full-text Bible search across multiple translations

\- Results displayed with checkboxes for selection

\- Format: `☐ KJV Gen 1:1 In the beginning...`

\- Click verses to navigate to Reading Window



✅ \*\*Reading Window (Window 3)\*\*

\- Shows context verses around selected passages

\- Scrollable Bible reading view

\- Checkboxes for selecting additional verses discovered while browsing

\- Navigates when verses selected in Search Results or Subject Verses



✅ \*\*Subject Verses Window (Window 4)\*\*

\- Collection of verses organized by subject/topic

\- Verses acquired from Search Results or Reading Window

\- Checkboxes for verse management

\- Click verses to navigate to Reading Window for context



✅ \*\*Verse Selection \& Acquisition\*\*

\- Checkbox selection across all verse windows

\- Acquire button moves selected verses from active window to Subject Verses

\- Automatic clearing of selections after successful acquire

\- Visual highlighting shows which window is active (light blue background, blue border)



✅ \*\*Window Management\*\*

\- Active window highlighting (light blue background + blue border)

\- Inactive windows (white background + gray border)

\- Click anywhere in a window to make it active

\- Resizable window heights via splitter controls



\### Verse Display Format



All verses display in consistent format:

```

☐ KJV Gen 1:1  In the beginning God created the heaven and the earth.

```



\- \*\*Checkbox\*\* (20px fixed width)

\- \*\*Translation\*\* (3-letter abbreviation: KJV, NIV, ESV, etc.)

\- \*\*Book\*\* (3-letter abbreviation: Gen, Exo, Mat, Joh, etc.)

\- \*\*Chapter:Verse\*\* (e.g., 1:1, 3:16)

\- \*\*Text\*\* (word-wrapped for readability)



\## File Structure



```

bible-search/

├── README.md                    # This file

├── docs/

│   └── database\_schema.md       # SQLite database documentation

├── interface\*.py                # PyQt6 application files (numbered versions)

├── database/

│   └── bibles.db               # SQLite database (627MB, 507K records)

└── tasks/

&nbsp;   └── todo.md                 # Development tasks and planning

```



\## Database Structure



See `docs/database\_schema.md` for complete database documentation.



\*\*Key Tables:\*\*

\- `verses` - 32,584 unique verse references

\- `verse\_texts` - 475,055 verse texts across 17 translations

\- `books` - 66 Bible books with canonical ordering

\- `translations` - 17 Bible versions (KJV, ASV, NIV, ESV, etc.)

\- `subjects` - User-created subject categories

\- `subject\_verses` - Verses organized under subjects with comments



\## Installation \& Running



\### Prerequisites

\- Python 3.8+

\- PyQt6

\- SQLite3 (included with Python)



\### Setup

```bash

\# Install PyQt6

pip install PyQt6



\# Navigate to project directory

cd ~/projects/bible-search



\# Run the application

python3 interface17.py  # or latest interface version

```



\### Database Location

The SQLite database must be located at `database/bibles.db` relative to the script.



\## Usage Workflow



\### Basic Search Workflow

1\. Enter search terms in Search Results section

2\. Click \*\*Search\*\* to find verses

3\. Results appear with checkboxes

4\. Check desired verses

5\. Click \*\*Acquire\*\* to move to Subject Verses



\### Context Reading Workflow

1\. Click any verse in Search Results

2\. Reading Window shows surrounding context

3\. Browse and select additional relevant verses

4\. Click \*\*Acquire\*\* to collect into Subject Verses



\### Subject Organization

1\. Create or select a subject category

2\. Acquire verses from Search or Reading windows

3\. Add comments to individual verses

4\. Export or print subject collections



\### Active Window Behavior

\- \*\*Acquire button\*\*: Operates only on currently active window

\- \*\*Copy/Export\*\*: Works on active window's selections

\- \*\*Navigation\*\*: Clicking verse in Search/Subject updates Reading Window



\## Architecture



\### Key Components



\*\*VerseItemWidget\*\*

\- Individual verse display with checkbox

\- Handles selection state and formatting

\- Emits signals for selection changes and navigation



\*\*VerseListWidget\*\*

\- Manages collections of verse items

\- Tracks selection state

\- Provides scrolling container

\- Visual feedback for active/inactive state



\*\*SelectionManager\*\*

\- Centralized verse selection tracking

\- Manages active window state

\- Coordinates cross-window operations



\*\*BibleSearchProgram (Main Window)\*\*

\- Coordinates all UI components

\- Handles window activation

\- Manages Acquire/Copy/Export operations

\- Connects navigation between windows



\## Development Status



\### Completed

\- \[x] PyQt6 UI framework with resizable splitters

\- \[x] Verse display widgets with checkboxes

\- \[x] Window highlighting (active/inactive visual feedback)

\- \[x] Acquire functionality from Search Results

\- \[x] Acquire functionality from Reading Window

\- \[x] Automatic selection clearing after acquire

\- \[x] Inter-window navigation (Search/Subject → Reading)

\- \[x] Context-aware button operations



\### In Progress

\- \[ ] Database integration for search functionality

\- \[ ] Subject creation and management

\- \[ ] Comments system for subject verses

\- \[ ] Export/Print implementations



\### Planned

\- \[ ] Advanced search features (Boolean operators, wildcards)

\- \[ ] Multiple translation comparison

\- \[ ] Verse highlighting in search results

\- \[ ] Subject categorization and tagging

\- \[ ] Import/Export subject collections

\- \[ ] Keyboard shortcuts

\- \[ ] User preferences and settings



\## Known Issues



\- QStandardPaths warning on Ubuntu (cosmetic, does not affect functionality)

\- Acquire button highlighting (green color) not yet visible (logic implemented, styling pending)



\## Claude Code Rules



When working on this codebase with Claude, follow these principles:



1\. \*\*First think through the problem\*\*, read the codebase for relevant files, and write a plan to `tasks/todo.md`.

2\. \*\*The plan should have a list of todo items\*\* that you can check off as you complete them.

3\. \*\*Before you begin working\*\*, check in with me and I will verify the plan.

4\. \*\*Then, begin working on the todo items\*\*, marking them as complete as you go.

5\. \*\*Please every step of the way\*\* just give me a high level explanation of what changes you made.

6\. \*\*Make every task and code change you do as simple as possible\*\*. We want to avoid making any massive or complex changes. Every change should respect as little code as possible. Everything is about simplicity.

7\. \*\*Finally, add a review section\*\* to the todo.md file with a summary of the changes you made and any other relevant information.

8\. \*\*DO NOT BE LAZY. NEVER BE LAZY.\*\* IF THERE IS A BUG FIND THE ROOT CAUSE AND FIX IT. NO TEMPORARY FIXES. YOU ARE A SENIOR DEVELOPER. NEVER BE LAZY.

9\. \*\*MAKE ALL FIXES AND CODE CHANGES AS SIMPLE AS HUMANLY POSSIBLE\*\*. THEY SHOULD ONLY IMPACT NECESSARY CODE RELEVANT TO THE TASK SURROUNDING IT OR IT SHOULD IMPACT AS LITTLE CODE AS POSSIBLE. YOUR GOAL IS TO NOT INTRODUCE ANY BUGS. IT'S ALL ABOUT SIMPLICITY!



\## Development Notes



\### Code Versioning

The project uses numbered interface files (`interface1.py`, `interface2.py`, etc.) to track development iterations. This allows easy rollback to previous working versions if needed.



\### Debugging

Console output provides detailed logging of:

\- Window activation events

\- Checkbox selection changes

\- Acquire operations and verse counts

\- Styling application for visual feedback



\### Testing

Manual testing workflow:

1\. Click Search to populate sample verses

2\. Test checkbox selection in Search Results

3\. Navigate to Reading Window by clicking verses

4\. Test checkbox selection in Reading Window

5\. Verify Acquire moves verses to Subject Verses

6\. Confirm selections clear after Acquire

7\. Validate window highlighting shows active window



\## Contributing



This is a personal Bible study tool. Code modifications should prioritize:

\- Simplicity over cleverness

\- Incremental changes over rewrites

\- Clear documentation of changes

\- Preservation of working functionality



\## License



Personal project - not licensed for distribution.



\## Contact \& Support



Project maintained by Andrew Hopkins (ajhinva@gmail.com)

\- Project Path: `~/projects/bible-search/`

\- WSL Ubuntu environment



---



\*\*Last Updated\*\*: December 2024  

\*\*Current Version\*\*: interface17.py  

\*\*Python Version\*\*: 3.13  

\*\*PyQt Version\*\*: PyQt6

