# DOCX Index Search

A simple Windows application to index and search through DOCX files using a SQLite database.

## Features

- **Automatic Dependency Checking**: Checks for required packages on startup
- **Easy Installation**: Offers to install missing dependencies automatically
- **SQLite Database**: Fast and reliable local database for indexing
- **Full-Text Search**: Search through document content and filenames
- **Simple GUI**: Clean tkinter-based interface
- **MS Word Integration**: Double-click results to open files in Microsoft Word
- **Configurable Path**: Set custom directory for DOCX files
- **Recursive Indexing**: Finds all DOCX files in subdirectories
- **Single File**: Entire application in one Python file

## Requirements

- Python 3.7 or higher
- Windows 11 (or Windows 10)
- Microsoft Word (for opening documents)

### Python Dependencies

The program will check for these automatically:

- `python-docx` - For reading DOCX files

## Installation

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Download the program**:
   - Copy `docx_index_search.py` to your desired location

3. **Run the program**:
   ```
   python docx_index_search.py
   ```

4. **Install dependencies** (if prompted):
   - The program will detect missing packages
   - Click "Yes" to install automatically, or
   - Install manually: `pip install python-docx`

## Usage

### First Run

On first run, the program will:
1. Check if the database exists
2. If not, ask if you want to scan for DOCX files in the current directory
3. Create an index of all found DOCX files

### Main Window

The main window includes:

- **Search Box**: Type to search through document content and filenames
- **Search Button**: Execute the search
- **Show All Button**: Display all indexed documents
- **Re-index Button**: Scan and re-index all DOCX files
- **Settings Button**: Configure application settings

### Searching Documents

1. Type your search query in the search box
2. Click "Search" or press Enter
3. Results appear in the scrollable list
4. Double-click any result to open the document in MS Word

**Advanced Search:**

- **Simple Search**: Type any word or phrase (e.g., "James")
  - Finds documents containing that term anywhere in content or filename

- **Multi-Word Search**: Type multiple words separated by spaces (e.g., "Abraham prophecy")
  - Finds documents where ALL words appear together in the content OR all in the filename
  - Both words must be in the same field (not split between filename and content)
  - Words can appear in any order within the document

- **Exact Phrase Search**: Use quotes for exact phrases (e.g., "The Abrahamic Prophecy")
  - Finds documents containing that exact phrase

- **AND Operator**: Use AND to search for multiple terms (e.g., "James AND John")
  - Finds documents that contain BOTH terms
  - Case-insensitive (AND, and, And all work)
  - Can chain multiple terms: "James AND John AND Peter"
  - Each term can appear anywhere in the document (don't need to be adjacent)

### Sorting Results

Click on any column header to sort the results:

- **Filename**: Sort alphabetically by filename
- **Modified**: Sort by last modification date
- **Size**: Sort by file size
- **Path**: Sort alphabetically by file path

**Sort Direction:**
- First click: Sort ascending (▲)
- Second click: Sort descending (▼)
- Click a different column: Sort by that column in ascending order

The sort order persists as you work with the current result set. When you perform a new search, the sort is reset.

### Settings

Access via the "Settings" button:

- **DOCX Files Directory**: Set the path where your DOCX files are located
  - Default is the current directory
  - Can browse to select a different folder
- **Database Info**: View database location and document count
- **Clear Index**: Remove all indexed documents (files are not deleted)

### Re-indexing

Click "Re-index" to:
1. Scan the configured directory for DOCX files
2. Extract text content from each file
3. Update the database with new/changed files

The indexer will:
- Skip temporary Word files (starting with ~$)
- Process all subdirectories
- Show progress during indexing

## File Structure

When running, the program creates:

- `docx_index.db` - SQLite database file (in the same directory as the script)

## Troubleshooting

### "Missing Dependencies" Error

If you see this error:
1. Click "Yes" to install automatically, or
2. Open Command Prompt and run:
   ```
   pip install python-docx
   ```
3. Restart the application

### "File Not Found" When Opening Document

If a document has been moved or deleted:
1. Click "Re-index" to update the database
2. Or remove the entry via "Settings" → "Clear Index" and re-index

### No Documents Found

If the index is empty:
1. Check the path in Settings
2. Ensure DOCX files exist in that directory
3. Click "Re-index" to scan again

### Permission Errors

If you get permission errors:
1. Run as Administrator (right-click → "Run as administrator")
2. Or choose a different directory for indexing

## Database Schema

The SQLite database contains:

### documents table
- `id` - Unique document ID
- `filename` - Name of the file
- `filepath` - Full path to the file
- `file_size` - File size in bytes
- `modified_date` - Last modification date
- `indexed_date` - When the file was indexed
- `content` - Extracted text content

### settings table
- `key` - Setting name
- `value` - Setting value

## Tips

1. **Regular Re-indexing**: Re-index periodically to catch new or modified files
2. **Specific Searches**: Use specific terms for better results
3. **Subdirectories**: The indexer searches all subdirectories automatically
4. **Backup**: The database file (`docx_index.db`) can be backed up or copied

## License

Free to use and modify for personal and commercial purposes.

## Version

Version 1.0 - January 2025
