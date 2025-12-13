# Duplicate File Finder

A Windows PowerShell GUI application for finding and deleting duplicate files in a directory.

## Features

- **Multiple Detection Methods:**
  - Finds exact duplicates (same name, size, and content hash)
  - Detects version files (e.g., "file.txt" and "file (1).txt")
  - Identifies copies (e.g., "file.txt" and "file - Copy.txt")

- **Content Verification:** Uses MD5 hash to verify files are truly identical, not just similar names
- **User-Friendly GUI:** Windows Forms interface with scrollable file list
- **Safe Deletion:** Checkboxes allow you to select which files to delete
- **Confirmation Dialog:** Warns before deleting with file count and total size

## Requirements

- Windows 11 (or Windows 10)
- PowerShell 5.1 or later (included with Windows)

## Usage

### Running the Script

1. Open PowerShell in the directory you want to scan
2. Run the script:
   ```powershell
   .\Find-DuplicateFiles.ps1
   ```

### Using the Application

1. **Scan for Duplicates:**
   - Click the "Scan" button to search the current directory (including subdirectories)
   - The status bar shows progress and results

2. **Review Results:**
   - The list shows all detected duplicate files with:
     - File path
     - Size in KB
     - Original file path (what it's a duplicate of)
     - Reason for detection

3. **Select Files to Delete:**
   - Check the boxes next to files you want to delete
   - Use "Select All" or "Deselect All" for bulk selection
   - Review carefully - originals are kept, only duplicates are shown

4. **Delete Files:**
   - Click "Delete Selected"
   - Confirm the deletion dialog
   - Files are permanently removed (cannot be undone)

5. **Exit:**
   - Click "Exit" to close the application

## How It Works

The script identifies duplicates using a multi-step process:

1. **Size Grouping:** Groups files by size (fast initial filter)
2. **Name Analysis:** Checks for exact name matches and similar names
3. **Content Verification:** Calculates MD5 hash to confirm identical content
4. **Pattern Recognition:** Detects common duplicate patterns:
   - `filename (1).txt`, `filename (2).txt`
   - `filename - Copy.txt`
   - `filename_v2.txt`, `filename_v3.txt`
   - `filename_1.txt`, `filename_2.txt`

## Safety Features

- Only files with identical content (verified by hash) are marked as duplicates
- Confirmation dialog before deletion shows count and total size
- The original file is never marked for deletion, only subsequent duplicates
- Failed deletions are reported

## Examples

The script will detect duplicates in these scenarios:

- **Exact duplicates:** Multiple copies of `photo.jpg` with identical content
- **Numbered copies:** `document.docx`, `document (1).docx`, `document (2).docx`
- **Windows copies:** `report.pdf`, `report - Copy.pdf`
- **Versioned files:** `presentation_v1.pptx`, `presentation_v2.pptx` (if content is identical)

## Notes

- The script scans recursively through all subdirectories
- Large directories may take time to scan
- Files must have identical content (hash) to be marked as duplicates, not just similar names
- Deletion is permanent - files are not moved to Recycle Bin

## Troubleshooting

If the script doesn't run:
1. Make sure you're in PowerShell (not Command Prompt)
2. You may need to adjust execution policy:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
