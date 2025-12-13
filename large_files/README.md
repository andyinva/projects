# Large File Manager

A Python GUI application for finding, moving, and managing large files with complete tracking and restore capabilities.

**Cross-Platform Support**: Works on both Windows 11 and Linux (including WSL)!

## Features

- **Cross-platform compatibility**: Works on Windows, Linux, and macOS
- **Automatic platform detection**: Adapts to your operating system
- **USB drive detection**: Automatically finds connected USB drives on both Windows and Linux
- **Skip OS files**: Option to skip operating system directories (C:\Windows, /bin, /usr, etc.)
- **Search for large files** by minimum size across any directory
- **Sortable columns**: Click any column header to sort results by size, path, or date
- **Simple windowing interface** using tkinter (no additional dependencies needed)
- **Move files to USB drive** or any other location
- **Complete tracking** of all file moves with timestamps
- **Restore files** back to their original locations
- **Checkbox selection** for easy file management
- **Move history** saved persistently in JSON format

## Requirements

- Python 3.6 or higher
- tkinter (usually included with Python)

## Installation

No installation required! Just download the `large_file_manager.py` file.

## Usage

### Running the Program

**On Windows:**
- Double-click `run_large_file_manager.bat`, OR
- From Command Prompt: `python large_file_manager.py`

**On Linux/WSL:**
```bash
./run_large_file_manager.sh
```
Or directly:
```bash
python3 large_file_manager.py
```

### Tab 1: Search & Move

1. **Select Search Directory**: Choose where to search for large files (defaults to your home directory)
2. **Set Minimum Size**: Enter the minimum file size in megabytes (MB)
3. **Skip Operating System files**: Check this box (enabled by default) to skip system directories like:
   - **Windows**: C:\Windows, C:\Program Files, $Recycle.Bin, etc.
   - **Linux**: /bin, /usr, /etc, /sys, /proc, etc.
   - Recommended when searching from C:\ or / to avoid system files
4. **Click "Search Files"**: The program will scan the directory and show all files meeting the size criteria
5. **Sort Results**: Click any column header (Size or Path) to sort the results
   - Click once for ascending order (↑)
   - Click again for descending order (↓)
6. **Select Files**: Click checkboxes next to files you want to move, or use "Select All"/"Deselect All" buttons
7. **Move Selected Files**: Click this button and you'll see two options:
   - **Detect USB Drives**: Automatically finds and lists all connected USB drives
   - **Browse**: Manually select any folder on your system
8. **Confirm**: Review the summary and confirm the move operation

### Tab 2: History & Restore

1. **View Move History**: See all previously moved files with:
   - Date and time of move
   - File size
   - Original location
   - Current location (where it was moved to)
   - **Sort by clicking headers**: Click any column to sort by Date/Time, Size, From, or To

2. **Restore Files**:
   - Select files using checkboxes
   - Click "Restore Selected Files"
   - Files will be moved back to their original locations
   - Successfully restored files are removed from the history

## File Move History

All file moves are recorded in `file_move_history.json` in the same directory as the program. This file contains:
- Original file path
- Destination path
- Timestamp of the move
- File size

This history persists between program sessions, so you can always restore files even after closing and reopening the application.

## Safety Features

- **Duplicate filename handling**: If a file with the same name exists at the destination, a number is appended
- **Confirmation dialogs**: All move and restore operations require confirmation
- **Error handling**: Permission errors and missing files are handled gracefully
- **Directory creation**: When restoring, missing directories are automatically created

## USB Drive Detection

The program automatically detects USB drives based on your operating system:

**On Windows:**
- Scans all drive letters (C:, D:, E:, etc.)
- Shows drive type (Removable, Fixed, Network, etc.)
- USB drives typically appear as removable drives

**On Linux:**
- Checks `/media/username/` for user-mounted drives
- Checks `/mnt/` for manually mounted drives
- Identifies mount points automatically

Simply click "Detect USB Drives" when moving files, and the program will show you all available options!

## Tips

- **Searching from C:\ on Windows**: Always keep "Skip Operating System files" checked when searching from C:\ to avoid system directories and speed up searches
- **Use USB Detection**: Click "Detect USB Drives" to automatically find your USB drive instead of browsing manually
- **Sort to find largest files**: Click the "Size (MB)" header to sort by size and quickly find the biggest files
- **Cross-platform file paths**: The program handles Windows (backslashes) and Linux (forward slashes) paths automatically
- **Large searches**: Searching your entire system may take a while and requires appropriate permissions
- **Free up space**: Use this tool to identify and move large files to external storage
- **Safe testing**: Start with a small directory to test the functionality

## Troubleshooting

**Search is slow**:
- Searching large directories takes time. The status updates as files are found
- Consider searching specific directories rather than entire system

**Permission errors**:
- Some system directories require administrator/root access
- Stick to your home directory or user-accessible folders

**Cannot find USB drive**:
- Make sure the USB drive is plugged in and recognized by your OS
- **Windows**: Check File Explorer to verify the drive appears
- **Linux**: Check if mounted with `lsblk` or `mount` commands
- If USB detection doesn't find it, use the "Browse" button to navigate manually

**Program won't start on Windows**:
- Make sure Python is installed and in your PATH
- Try running from Command Prompt: `python large_file_manager.py`
- If using WSL, run from WSL terminal instead

**tkinter not found**:
- **Windows**: Reinstall Python with tkinter option checked
- **Linux**: Install with `sudo apt-get install python3-tk` (Ubuntu/Debian)

## Example Workflow

1. Want to free up space on your laptop
2. Search your home directory for files over 500 MB
3. Review the results and select videos/downloads to move
4. Move them to your USB drive
5. Later, if you need a file back, go to History & Restore tab
6. Select the file and restore it to its original location

## License

Free to use and modify for personal or commercial purposes.
