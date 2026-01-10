# Bible Search Lite - Distribution Guide

Technical documentation for the distribution system used in Bible Search Lite v1.0.

---

## Overview

Bible Search Lite uses a two-part distribution system:

1. **Developer Tool** (`export_bible_data.py`) - Exports database for releases
2. **End User Installer** (`setup.py`) - Downloads and installs application

This approach solves the GitHub repository size limit (100 MB) while distributing a 453 MB database.

---

## Architecture

### Distribution Workflow

```
┌─────────────────┐
│  Developer      │
│  (You)          │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  export_bible_data.py                   │
│  • Exports SQLite → SQL dump            │
│  • Compresses with gzip -9              │
│  • Generates SHA256 checksum            │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Files Created:                         │
│  • data/bible_data.sql.gz (90 MB)       │
│  • data/checksums.txt                   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Upload to GitHub Release v1.0          │
│  (2 GB size limit vs 100 MB repo limit) │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  End Users run:                         │
│  python3 setup.py                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  setup.py                               │
│  • Downloads bible_data.sql.gz          │
│  • Verifies checksum                    │
│  • Decompresses                         │
│  • Imports to SQLite                    │
│  • Downloads app files                  │
│  • Installs dependencies                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Installed Application                  │
│  • database/bibles.db (453 MB)          │
│  • All Python files                     │
│  • Ready to run                         │
└─────────────────────────────────────────┘
```

---

## File Size Breakdown

### Source Database
- **File:** `database/bibles.db`
- **Size:** 453 MB
- **Content:** 44 Bible translations, 1.3M+ verses
- **Format:** SQLite 3

### Export Process

**Step 1: SQL Dump**
```bash
sqlite3 database/bibles.db .dump > bible_data.sql
```
- **Size:** ~1.2 GB (text format)
- **Format:** SQL statements (CREATE TABLE, INSERT)
- **Advantage:** Preserves schema, indexes, data

**Step 2: Compression**
```bash
gzip -9 bible_data.sql
```
- **Size:** ~90 MB (92.5% compression)
- **Format:** gzip compressed
- **Compression level:** Maximum (-9)

**Step 3: Checksum**
```bash
sha256sum bible_data.sql.gz > checksums.txt
```
- **Purpose:** Verify download integrity
- **Algorithm:** SHA256

### GitHub Distribution
- **Method:** GitHub Releases
- **Limit:** 2 GB per file (plenty of headroom)
- **Files:**
  - `bible_data.sql.gz` (90 MB)
  - `checksums.txt` (173 bytes)

### End User Download
- **Download:** 90 MB
- **Decompressed:** 1.2 GB (temporary)
- **Final database:** 453 MB
- **Temp files removed:** Yes

---

## Developer Workflow

### Creating a Release

**1. Export Database**
```bash
python3 export_bible_data.py
```

Output:
```
======================================================================
Bible Search Lite - Database Exporter
======================================================================

📊 Database size: 452.5 MB

📤 Step 1/3: Creating SQL dump...
   ✅ Created: data/bible_data.sql (1.2 GB)

🗜️  Step 2/3: Compressing SQL dump...
   ✅ Created: data/bible_data.sql.gz
   📦 Compressed size: 89.3 MB
   💾 Compression ratio: 92.8%

🔒 Step 3/3: Generating checksums...
   ✅ Created: data/checksums.txt
   🔑 SHA256: 9a4ca8d69427aabe...

======================================================================
✅ Export Complete!
======================================================================
```

**2. Create GitHub Release**
- Go to https://github.com/andyinva/bible-search-lite/releases
- Click "Draft a new release"
- Tag: `v1.0`
- Title: `Bible Search Lite v1.0 - Initial Release`
- Description: Paste from RELEASE_NOTES_v1.0.md
- Upload files:
  - `data/bible_data.sql.gz`
  - `data/checksums.txt`
- Click "Publish release"

**3. Test Installation**
```bash
# In a test directory
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py
```

**4. Verify**
- Check database created
- Check translations count
- Launch application
- Perform test search

---

## End User Installation Flow

### 1. Download Installer
```bash
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
```

### 2. Run Installer
```bash
python3 setup.py
```

### 3. Installation Steps

**A. Check Requirements**
- Verify Python 3.7+
- Check for sqlite3 (offer to install if missing)
- Check for gunzip

**B. Download Database**
```
URL: https://github.com/andyinva/bible-search-lite/releases/download/v1.0/bible_data.sql.gz
```

**C. Verify Checksum**
- Download checksums.txt
- Calculate SHA256 of downloaded file
- Compare hashes
- Fail if mismatch

**D. Decompress**
```bash
gunzip bible_data.sql.gz
```

**E. Import to SQLite**
```bash
sqlite3 database/bibles.db < bible_data.sql
```

**F. Download Application Files**
```
https://raw.githubusercontent.com/andyinva/bible-search-lite/main/[filename]
```

Files downloaded:
- `bible_search_lite.py`
- `bible_search.py`
- `bible_search_service.py`
- `subject_manager.py`
- `subject_verse_manager.py`
- `subject_comment_manager.py`
- `run_bible_search.sh`
- `bible_search_ui/` directory
- Documentation files

**G. Install Dependencies**
```bash
pip install PyQt6
```

**H. Cleanup**
- Remove temporary files
- Remove compressed SQL dump

---

## Technical Details

### export_bible_data.py

**Purpose:** Developer tool to prepare database for distribution

**Key Features:**
- Exports full SQLite database to SQL dump
- Maximum compression (gzip -9)
- SHA256 checksum generation
- Progress reporting
- Error handling

**Output:**
- `data/bible_data.sql.gz` - Compressed database
- `data/checksums.txt` - SHA256 hash

### setup.py

**Purpose:** End user one-command installer

**Key Features:**
- Dependency checking
- Auto-install SQLite3 (with permission)
- Download with progress indicator
- Checksum verification
- Cross-platform support (Linux, macOS, Windows)
- Error handling and rollback
- File integrity checks

**Supported Platforms:**
- Ubuntu/Debian (apt-get)
- Fedora/RHEL (dnf)
- Arch Linux (pacman)
- macOS (Homebrew)

---

## Why This Approach?

### Problem: Large Database
- Database is 453 MB
- GitHub repo limit: 100 MB
- Git tracks binary files inefficiently
- Cloning would download entire history

### Solution: GitHub Releases
- Releases have 2 GB limit
- Files are attachments, not in git history
- One-time download
- Can be updated without repo bloat

### Alternative Approaches Considered

**1. Git LFS (Large File Storage)**
- ❌ Requires special setup
- ❌ Bandwidth limits on free tier
- ❌ Complex for end users

**2. External Hosting (Dropbox, Google Drive)**
- ❌ Requires separate account
- ❌ Link rot risk
- ❌ Bandwidth limits
- ❌ Not integrated with GitHub

**3. Split Database**
- ❌ Complex to manage multiple files
- ❌ Users must download all parts
- ❌ More error-prone

**4. GitHub Releases** ✅
- ✅ Integrated with repository
- ✅ 2 GB limit per file
- ✅ Reliable CDN
- ✅ Version tracking
- ✅ Free for open source

---

## Checksum Verification

### Why Checksums?

1. **Detect corruption** - Network errors, incomplete downloads
2. **Verify integrity** - File wasn't modified
3. **Security** - Ensure official release

### How It Works

**Generate (Developer):**
```bash
sha256sum bible_data.sql.gz > checksums.txt
```

**Verify (End User - automated in setup.py):**
```python
import hashlib

def verify_checksum(file_path, expected):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b''):
            sha256.update(block)
    return sha256.hexdigest() == expected
```

---

## Updating the Distribution

### For New Releases (v1.1, v2.0, etc.)

**1. Update Version**
Edit `setup.py`:
```python
RELEASE_VERSION = "v1.1"
```

**2. Export Database**
```bash
python3 export_bible_data.py
```

**3. Create New Release**
- Tag: `v1.1`
- Upload new `bible_data.sql.gz` and `checksums.txt`

**4. Update setup.py in Repository**
Commit updated RELEASE_VERSION to main branch.

---

## Troubleshooting Distribution

### Export Fails

**Error:** Database not found

**Solution:** Check `db_path` in export_bible_data.py points to correct database.

### Upload Fails

**Error:** File too large for GitHub

**Solution:** Check file size. Should be ~90 MB. If larger, check compression.

### Download Fails (End User)

**Error:** 404 Not Found

**Solution:** Verify release exists and files are uploaded.

### Checksum Mismatch

**Error:** Checksum verification failed

**Solution:** Re-upload files to GitHub Release. File may be corrupted.

---

## Future Improvements

### Potential Enhancements

1. **Delta Updates**
   - Only download changes between versions
   - Reduces bandwidth for updates

2. **Multiple Compression Formats**
   - Offer .zip for Windows users
   - Offer .xz for better compression

3. **Torrent Distribution**
   - P2P distribution for large files
   - Reduces server bandwidth

4. **Cloud Storage Backup**
   - Mirror on S3/CDN
   - Fallback if GitHub is slow

5. **Installer GUI**
   - Graphical installer for non-technical users
   - Progress bars, error dialogs

---

## Summary

The distribution system provides:

✅ **Simple for users** - One command install
✅ **Efficient** - 90 MB download for 453 MB database
✅ **Reliable** - Checksum verification
✅ **Integrated** - Uses GitHub infrastructure
✅ **Scalable** - Can handle 2 GB files
✅ **Maintainable** - Easy to update releases

**For installation help, see [INSTALLATION.md](INSTALLATION.md)**
**For usage help, see [README.md](README.md)**
