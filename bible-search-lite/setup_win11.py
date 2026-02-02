#!/usr/bin/env python3
"""
setup_win11.py - Bible Search Lite Installer for Windows 11

Native Windows installer that uses pure Python (no Unix tools required).
Works on Windows 10/11 without WSL2.

Usage:
    python setup_win11.py

Requirements:
    • Python 3.7 or higher
    • Internet connection

Author: Andrew Hopkins
"""

import os
import subprocess
import urllib.request
import urllib.error
import hashlib
import sys
import platform
import gzip
import shutil
import sqlite3
import json

# Configuration
GITHUB_USER = "andyinva"
GITHUB_REPO = "bible-search-lite"
RELEASE_VERSION = "v1.1.4"  # Update this to match your release tag

# GitHub URLs
RELEASE_BASE_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/download/{RELEASE_VERSION}"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")

def check_python_version():
    """Check if Python version is sufficient"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"  ❌ Python 3.7+ required, found {version.major}.{version.minor}")
        print("     Download Python from: https://www.python.org/downloads/")
        return False
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def download_file(url, dest, description=None):
    """Download a file with progress indication"""
    if description is None:
        description = os.path.basename(dest)

    print(f"Downloading {description}...")

    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\r  Progress: {percent}%")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest, reporthook)
        print()  # New line after progress

        file_size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"  ✅ Downloaded {description} ({file_size_mb:.1f} MB)")
        return True

    except urllib.error.URLError as e:
        print(f"\n  ❌ Download failed: {e}")
        print(f"     URL: {url}")
        return False
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        return False

def verify_checksum(file_path, expected_checksum):
    """Verify file integrity using SHA256"""
    print(f"Verifying {os.path.basename(file_path)}...")

    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)

    actual_checksum = sha256_hash.hexdigest()

    if actual_checksum == expected_checksum:
        print(f"  ✅ Checksum verified")
        return True
    else:
        print(f"  ❌ Checksum mismatch!")
        print(f"     Expected: {expected_checksum}")
        print(f"     Actual:   {actual_checksum}")
        return False

def decompress_gzip(input_file, output_file):
    """Decompress a gzip file using Python's gzip module"""
    print(f"Decompressing {os.path.basename(input_file)}...")

    try:
        with gzip.open(input_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        output_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ✅ Decompressed to {os.path.basename(output_file)} ({output_size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ❌ Decompression failed: {e}")
        return False

def import_sql_to_sqlite(sql_file, db_path):
    """Import SQL dump into SQLite database using Python sqlite3 module"""
    print(f"Creating SQLite database (this may take a few minutes)...")

    try:
        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Create database and execute SQL
        conn = sqlite3.connect(db_path)
        conn.executescript(sql_script)
        conn.close()

        db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"  ✅ Created {db_path} ({db_size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ❌ Database creation failed: {e}")
        return False

def setup_database():
    """Download and setup the Bible SQLite database"""
    print_header("Step 1: Database Setup")

    # Create directories
    os.makedirs('database', exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    # Download checksums file
    checksums_url = f"{RELEASE_BASE_URL}/checksums.txt"
    checksums_path = "temp/checksums.txt"

    if not download_file(checksums_url, checksums_path, "checksums.txt"):
        print("\n❌ Failed to download checksums file")
        print(f"   Make sure release {RELEASE_VERSION} exists with checksums.txt")
        sys.exit(1)

    # Read expected checksum
    print("\nReading checksums...")
    with open(checksums_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.strip().split(': ')
                if len(parts) == 2 and parts[0] == 'bible_data.sql.gz':
                    expected_checksum = parts[1]
                    print(f"  Expected checksum: {expected_checksum[:16]}...")
                    break
        else:
            print("  ❌ Could not find checksum for bible_data.sql.gz")
            sys.exit(1)

    # Download compressed database
    print()
    db_url = f"{RELEASE_BASE_URL}/bible_data.sql.gz"
    db_compressed_path = "temp/bible_data.sql.gz"

    if not download_file(db_url, db_compressed_path, "Bible database (compressed)"):
        print("\n❌ Failed to download database")
        print(f"   Make sure release {RELEASE_VERSION} has bible_data.sql.gz uploaded")
        sys.exit(1)

    # Verify checksum
    print()
    if not verify_checksum(db_compressed_path, expected_checksum):
        print("\n❌ Download verification failed!")
        print("   The file may be corrupted. Please try again.")
        sys.exit(1)

    # Decompress using Python's gzip module
    print()
    db_sql_path = "temp/bible_data.sql"
    if not decompress_gzip(db_compressed_path, db_sql_path):
        sys.exit(1)

    # Import to SQLite using Python's sqlite3 module
    print()
    db_path = 'database/bibles.db'
    if not import_sql_to_sqlite(db_sql_path, db_path):
        sys.exit(1)

    # Verify database
    print("\nVerifying database...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM translations;')
        translation_count = cursor.fetchone()[0]
        conn.close()
        print(f"  ✅ Database verified ({translation_count} translations found)")
    except Exception as e:
        print(f"  ❌ Database verification failed: {e}")
        sys.exit(1)

    # Cleanup
    print("\nCleaning up temporary files...")
    try:
        os.remove(db_sql_path)
        os.remove(db_compressed_path)
        os.remove(checksums_path)
        print("  ✅ Temporary files removed")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not remove temp files: {e}")

def download_application_files():
    """Download application source files from GitHub"""
    print_header("Step 2: Download Application Files")

    # Files to download from the main branch
    files = [
        'bible_search_lite.py',
        'bible_search.py',
        'bible_search_service.py',
        'subject_manager.py',
        'subject_verse_manager.py',
        'subject_comment_manager.py',
        'export_dialog.py',
        'VERSION.txt',
        'run_bible_search.sh',
        'README.md',
        'SEARCH_OPERATORS.md',
    ]

    # Directories to create
    directories = [
        'bible_search_ui',
        'bible_search_ui/ui',
        'bible_search_ui/config',
        'bible_search_ui/controllers',
    ]

    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Download UI files
    ui_files = [
        'bible_search_ui/__init__.py',
        'bible_search_ui/ui/__init__.py',
        'bible_search_ui/ui/widgets.py',
        'bible_search_ui/ui/dialogs.py',
        'bible_search_ui/config/__init__.py',
        'bible_search_ui/config/config_manager.py',
        'bible_search_ui/controllers/__init__.py',
        'bible_search_ui/controllers/search_controller.py',
    ]

    all_files = files + ui_files

    success_count = 0
    fail_count = 0

    for file_path in all_files:
        url = f"{RAW_BASE_URL}/{file_path}"

        if download_file(url, file_path):
            success_count += 1
        else:
            fail_count += 1
            print(f"  ⚠️  Warning: Could not download {file_path}")

    print(f"\nDownload summary: {success_count} succeeded, {fail_count} failed")

    # Create user data database with schema
    print("\nCreating user data database...")
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect('database/subjects.db')
    cursor = conn.cursor()

    # Create subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create subject_verses table with current schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            verse_reference TEXT NOT NULL,
            verse_text TEXT NOT NULL,
            translation TEXT NOT NULL,
            comments TEXT DEFAULT '',
            order_index INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            UNIQUE(subject_id, verse_reference, translation)
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject_verses_subject_id ON subject_verses(subject_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject_verses_order ON subject_verses(subject_id, order_index)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subjects_name ON subjects(name)')

    conn.commit()
    conn.close()
    print("  ✅ Created database/subjects.db with schema")

    # Create default configuration file
    print("\nCreating default configuration...")
    default_config = {
        "window_geometry": {
            "x": 100,
            "y": 100,
            "width": 1200,
            "height": 800
        },
        "splitter_sizes": [
            100,
            250,
            400
        ],
        "selected_translations": [
            "KJV"
        ],
        "checkboxes": {
            "case_sensitive": False,
            "unique_verse": True,
            "abbreviate_results": False
        },
        "font_settings": {
            "title_font_size": 1,
            "verse_font_size": 2
        },
        "search_history": [],
        "subject_splitter_sizes": [
            300,
            200
        ]
    }

    with open('bible_search_lite_config.json', 'w') as f:
        json.dump(default_config, f, indent=2)
    print("  ✅ Created bible_search_lite_config.json with default settings")

def install_dependencies():
    """Install Python dependencies"""
    print_header("Step 3: Install Python Dependencies")

    dependencies = ['PyQt6']

    print("Installing dependencies with pip...")
    for dep in dependencies:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', dep],
                check=True,
                stdout=subprocess.DEVNULL
            )
            print(f"  ✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"  ❌ Failed to install {dep}")
            print("     You may need to install it manually:")
            print(f"       pip install {dep}")

def create_launcher():
    """Create Windows batch file launcher"""
    print("\nCreating Windows launcher...")

    launcher_content = f"""@echo off
REM Bible Search Lite Launcher for Windows
REM Generated by setup_win11.py

echo Starting Bible Search Lite...
"{sys.executable}" bible_search_lite.py
pause
"""

    try:
        with open('run_bible_search.bat', 'w') as f:
            f.write(launcher_content)
        print("  ✅ Created run_bible_search.bat")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not create launcher: {e}")

def check_directory_empty():
    """Check if directory contains files other than the installer"""
    print("Checking installation directory...")

    # Get list of all files and directories in current directory
    current_files = set(os.listdir('.'))

    # Files that are OK to have (installer and temp files)
    allowed_files = {
        'setup_win11.py',
        '__pycache__',
        '.git',
        '.gitignore'
    }

    # Check for other files
    extra_files = current_files - allowed_files

    if extra_files:
        print(f"  ❌ Directory is not empty!")
        print(f"\n  Found existing files/folders:")
        for item in sorted(extra_files):
            print(f"    • {item}")
        print(f"\n  ⚠️  This installer requires an empty directory to avoid conflicts.")
        print(f"  Please:")
        print(f"    1. Delete all files except setup_win11.py")
        print(f"    2. Or run the installer in a new empty directory")
        print()
        return False

    print(f"  ✅ Directory is empty")
    return True

def check_internet_connection():
    """Check if internet connection is available"""
    print("Checking internet connection...")

    test_urls = [
        "https://raw.githubusercontent.com",
        "https://github.com"
    ]

    for url in test_urls:
        try:
            # Try to connect with a short timeout
            urllib.request.urlopen(url, timeout=5)
            print(f"  ✅ Internet connection available")
            return True
        except urllib.error.URLError:
            continue
        except Exception:
            continue

    print(f"  ❌ No internet connection detected!")
    print(f"\n  This installer requires internet to:")
    print(f"    • Download Bible database from GitHub")
    print(f"    • Download application files")
    print(f"    • Install Python dependencies")
    print(f"\n  Please check your internet connection and try again.")
    print()
    return False

def main():
    """Main installation process"""
    print_header("Bible Search Lite - Windows 11 Installer")

    # Check platform
    if platform.system() != 'Windows':
        print("⚠️  This installer is for Windows only.")
        print("   For Linux/macOS, use: python3 setup.py")
        sys.exit(1)

    # EARLY CHECKS - before user confirmation
    print("Running pre-installation checks...\n")

    # Check Python version
    if not check_python_version():
        sys.exit(1)
    print()

    # Check if directory is empty
    if not check_directory_empty():
        sys.exit(1)
    print()

    # Check internet connection
    if not check_internet_connection():
        sys.exit(1)
    print()

    print(f"All pre-installation checks passed! ✅\n")
    print(f"This installer will:")
    print(f"  • Download Bible database from GitHub Release {RELEASE_VERSION}")
    print(f"  • Set up SQLite database with all translations")
    print(f"  • Download application files")
    print(f"  • Install Python dependencies")
    print(f"  • Create Windows launcher")
    print()
    input("Press Enter to continue...")

    try:

        # Setup database
        setup_database()

        # Download application files
        download_application_files()

        # Install dependencies
        install_dependencies()

        # Create launcher
        create_launcher()

        # Success!
        print_header("✅ Installation Complete!")

        print("Bible Search Lite is now installed!")
        print()
        print("To run the application:")
        print("  • Double-click: run_bible_search.bat")
        print("  or")
        print(f"  • Run: python bible_search_lite.py")
        print()
        print("For help and documentation, see:")
        print("  • README.md - Comprehensive documentation")
        print("  • SEARCH_OPERATORS.md - Search operator reference")
        print()
        print("Enjoy studying the Bible! 📖")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
