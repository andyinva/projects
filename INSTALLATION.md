# Bible Search Lite - Installation Guide

Complete installation instructions for Bible Search Lite v1.0.

---

## Quick Install (Recommended)

### One-Command Installation

```bash
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py
```

This will:
1. Check for SQLite3 (offer to install if missing)
2. Download the Bible database (~90 MB)
3. Verify download integrity
4. Create SQLite database with all translations
5. Download all application files
6. Install Python dependencies (PyQt6)

### Running the Application

```bash
./run_bible_search.sh
```

Or:

```bash
python3 bible_search_lite.py
```

---

## System Requirements

### Required
- **Python**: 3.7 or higher
- **SQLite3**: Command-line tool (auto-installed if missing)
- **Internet**: For initial download
- **Disk Space**: ~500 MB

### Automatically Installed
- **PyQt6**: GUI framework (installed by setup.py)
- **gzip**: Decompression (usually pre-installed)

---

## Detailed Installation Steps

### Step 1: Check Python Version

```bash
python3 --version
```

Should show Python 3.7 or higher. If not:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3
```

**macOS:**
```bash
brew install python3
```

### Step 2: Download Installer

```bash
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
```

Or download manually from:
https://github.com/andyinva/bible-search-lite/blob/main/setup.py

### Step 3: Run Installer

```bash
python3 setup.py
```

The installer will:
- Check for required tools
- Offer to install SQLite3 if missing (requires sudo)
- Download and verify the Bible database
- Set up the application files

### Step 4: Launch Application

```bash
./run_bible_search.sh
```

---

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

```bash
# Install Python if needed
sudo apt-get update
sudo apt-get install python3 python3-pip

# Run installer
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py

# Launch
./run_bible_search.sh
```

### macOS

```bash
# Install Python if needed
brew install python3

# Run installer
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py

# Launch
./run_bible_search.sh
```

### WSL2 (Windows Subsystem for Linux)

```bash
# Install Python and required packages
sudo apt-get update
sudo apt-get install python3 python3-pip

# Install X11 dependencies for GUI
sudo apt-get install python3-pyqt6

# Run installer
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py

# Launch
./run_bible_search.sh
```

**Note:** You'll need an X server running on Windows (e.g., VcXsrv, Xming).

---

## Manual Installation

If the automated installer doesn't work, you can install manually:

### 1. Install Dependencies

```bash
# Install SQLite3
sudo apt-get install sqlite3    # Ubuntu/Debian
brew install sqlite3            # macOS

# Install PyQt6
pip3 install PyQt6
```

### 2. Download Database

Download from GitHub Release v1.0:
- `bible_data.sql.gz` (~90 MB)
- `checksums.txt`

### 3. Verify and Extract

```bash
# Verify checksum
sha256sum bible_data.sql.gz
# Compare with checksums.txt

# Extract
gunzip bible_data.sql.gz
```

### 4. Create Database

```bash
mkdir -p database
sqlite3 database/bibles.db < bible_data.sql
```

### 5. Download Application Files

Clone the repository or download individual files:

```bash
git clone https://github.com/andyinva/bible-search-lite.git
cd bible-search-lite
```

Or download:
- `bible_search_lite.py`
- `bible_search.py`
- `bible_search_service.py`
- `subject_manager.py`
- `subject_verse_manager.py`
- `subject_comment_manager.py`
- `bible_search_ui/` directory
- `run_bible_search.sh`

### 6. Make Launcher Executable

```bash
chmod +x run_bible_search.sh
```

### 7. Run

```bash
./run_bible_search.sh
```

---

## Troubleshooting

### Installation Fails - Missing SQLite3

**Error:** `sqlite3 not found`

**Solution:**
```bash
sudo apt-get install sqlite3      # Ubuntu/Debian
brew install sqlite3              # macOS
sudo dnf install sqlite           # Fedora/RHEL
sudo pacman -S sqlite             # Arch
```

### Installation Fails - Download Error

**Error:** `HTTP Error 404: Not Found`

**Solution:** Ensure GitHub Release v1.0 exists and contains:
- `bible_data.sql.gz`
- `checksums.txt`

### Application Won't Start - Missing PyQt6

**Error:** `ModuleNotFoundError: No module named 'PyQt6'`

**Solution:**
```bash
pip3 install PyQt6
```

### Application Won't Start - Database Not Found

**Error:** `database/bibles.db not found`

**Solution:** Re-run setup.py or manually create database (see Manual Installation).

### Cursor Disappears (WSL2)

**Issue:** Cursor vanishes when hovering over application.

**Solution:** This is a known WSL2/X11 issue. Use native Linux or:
- Try different X server (VcXsrv, Xming)
- Update X server settings

### Slow Download

**Issue:** Database download is slow.

**Solution:** The 90MB file may take time on slow connections. The installer shows progress percentage. You can also manually download from GitHub and place in `temp/` directory before running setup.py.

---

## Verifying Installation

After installation completes, verify:

### 1. Check Files Exist

```bash
ls -la bible_search_lite.py
ls -la database/bibles.db
ls -la run_bible_search.sh
```

### 2. Check Database

```bash
sqlite3 database/bibles.db "SELECT COUNT(*) FROM translations;"
```

Should show `44` (number of Bible translations).

### 3. Test Launch

```bash
python3 bible_search_lite.py
```

Application should open with 5 windows.

### 4. Test Search

In the application:
1. Type `love` in search box
2. Click **Search** button
3. Should see hundreds of results

---

## Uninstalling

To remove Bible Search Lite:

```bash
# Remove application directory
rm -rf bible-search-lite/

# Remove config file (optional - saves your settings)
rm bible_search_lite_config.json
```

---

## Updating

To update to a newer version:

```bash
cd bible-search-lite
git pull
```

Or download the latest setup.py and run it again. It will preserve your subject database and configuration.

---

## Developer Setup

For development work:

### Clone Repository

```bash
git clone https://github.com/andyinva/bible-search-lite.git
cd bible-search-lite
```

### Install Development Dependencies

```bash
pip3 install PyQt6
```

### Download Database

Run setup.py to get the database, or manually download from releases.

### Run from Source

```bash
python3 bible_search_lite.py
```

---

## Support

If installation fails:

1. Check the [Troubleshooting](#troubleshooting) section
2. Create an issue: https://github.com/andyinva/bible-search-lite/issues
3. Include:
   - Operating system and version
   - Python version (`python3 --version`)
   - Full error message
   - Steps you followed

---

**For usage instructions, see [README.md](README.md) and [SEARCH_OPERATORS.md](SEARCH_OPERATORS.md)**
