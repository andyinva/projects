#!/usr/bin/env python3
"""
setup.py - Bible Search Lite Installer

One-command installer that downloads and sets up Bible Search Lite:
  • Downloads compressed Bible database from GitHub Releases
  • Verifies download integrity with SHA256 checksum
  • Creates SQLite database with all indexes
  • Installs Python dependencies
  • Downloads all application files

Usage:
    python3 setup.py

Requirements:
    • Python 3.7 or higher
    • Internet connection
    • sqlite3 command-line tool
    • gzip utility

Author: Andrew Hopkins
"""

import os
import subprocess
import urllib.request
import urllib.error
import hashlib
import sys
import platform
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

def install_sqlite3():
    """Attempt to install sqlite3 based on the platform"""
    system = platform.system()

    if system == 'Linux':
        # Detect Linux distribution
        try:
            with open('/etc/os-release') as f:
                os_info = f.read().lower()

            if 'debian' in os_info or 'ubuntu' in os_info:
                print("\n  Installing SQLite3 on Debian/Ubuntu...")
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'sqlite3'], check=True)
            elif 'fedora' in os_info or 'rhel' in os_info or 'centos' in os_info:
                print("\n  Installing SQLite3 on Fedora/RHEL/CentOS...")
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'sqlite'], check=True)
            elif 'arch' in os_info:
                print("\n  Installing SQLite3 on Arch Linux...")
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'sqlite'], check=True)
            else:
                print("\n  ⚠️  Unknown Linux distribution")
                return False

            return True

        except Exception as e:
            print(f"  ❌ Installation failed: {e}")
            return False

    elif system == 'Darwin':  # macOS
        print("\n  Installing SQLite3 on macOS...")
        try:
            subprocess.run(['brew', 'install', 'sqlite3'], check=True)
            return True
        except Exception as e:
            print(f"  ❌ Installation failed: {e}")
            print("  Note: You may need to install Homebrew first:")
            print("    /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False

    elif system == 'Windows':
        print("\n  Windows Installation Instructions:")
        print("\n  SQLite3 is typically included with Python on Windows.")
        print("  However, you need the sqlite3.exe command-line tool.")
        print("\n  Option 1: Install via Chocolatey (if you have it)")
        print("    choco install sqlite")
        print("\n  Option 2: Manual Download")
        print("    1. Visit: https://www.sqlite.org/download.html")
        print("    2. Download: 'sqlite-tools-win32-x86-*.zip'")
        print("    3. Extract and add to PATH")
        print("\n  Option 3: Use WSL2 (Recommended)")
        print("    Windows Subsystem for Linux provides full Linux environment.")
        print("    Run: wsl --install")
        print("    Then install from Ubuntu within WSL2")
        return False
    else:
        print(f"\n  ⚠️  Automatic installation not supported on {system}")
        return False

def check_requirements():
    """Check if required tools are installed"""
    print("Checking requirements...")

    required_tools = ['sqlite3', 'gunzip']
    missing = []

    for tool in required_tools:
        try:
            subprocess.run([tool, '--version'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         check=True)
            print(f"  ✅ {tool} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ❌ {tool} not found")
            missing.append(tool)

    if missing:
        print(f"\n❌ Missing required tools: {', '.join(missing)}")

        # Special handling for sqlite3 - offer to install
        if 'sqlite3' in missing:
            print("\nSQLite3 is required to run Bible Search Lite.")
            response = input("Would you like to install SQLite3 now? (Y/n): ").strip().lower()

            if response == '' or response == 'y' or response == 'yes':
                if install_sqlite3():
                    print("  ✅ SQLite3 installed successfully!")
                    missing.remove('sqlite3')
                else:
                    print("\n  Please install SQLite3 manually:")
                    if platform.system() == 'Linux':
                        print("    sudo apt-get install sqlite3")
                    elif platform.system() == 'Darwin':
                        print("    brew install sqlite3")
            else:
                print("\n  Please install SQLite3 manually before continuing:")
                if platform.system() == 'Linux':
                    print("    sudo apt-get install sqlite3")
                elif platform.system() == 'Darwin':
                    print("    brew install sqlite3")

        # If still missing tools, show instructions and exit
        if missing:
            print(f"\n❌ Still missing: {', '.join(missing)}")
            print("\nPlease install the missing tools:")
            if platform.system() == 'Linux':
                print(f"  sudo apt-get install {' '.join(missing)}")
            elif platform.system() == 'Darwin':
                print(f"  brew install {' '.join(missing)}")
            elif platform.system() == 'Windows':
                print("\n⚠️  Windows Native Installation Not Supported")
                print("\nBible Search Lite requires Unix tools (sqlite3, gunzip) that are not")
                print("natively available on Windows.")
                print("\n📌 RECOMMENDED: Use WSL2 (Windows Subsystem for Linux)")
                print("\n  WSL2 provides a full Linux environment on Windows 11:")
                print("  1. Open PowerShell as Administrator")
                print("  2. Run: wsl --install")
                print("  3. Restart your computer")
                print("  4. Open Ubuntu from Start Menu")
                print("  5. Run the installer in Ubuntu:")
                print("     python3 setup.py")
                print("\n  WSL2 Documentation:")
                print("  https://docs.microsoft.com/en-us/windows/wsl/install")
                print("\n📌 ALTERNATIVE: Manual Installation")
                print("\n  If you prefer not to use WSL2, you'll need to:")
                print("  1. Download sqlite3.exe from https://www.sqlite.org/download.html")
                print("  2. Install 7-Zip or WinRAR to extract .gz files")
                print("  3. Manually download and extract the database")
                print("  4. Install PyQt6: pip install PyQt6")
                print("  5. Download the application files from GitHub")
            sys.exit(1)

    print()

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
    with open(checksums_path) as f:
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

    # Decompress
    print("\nDecompressing database...")
    try:
        subprocess.run(['gunzip', '-f', db_compressed_path], check=True)
        db_sql_path = db_compressed_path.replace('.gz', '')
        print(f"  ✅ Decompressed to {db_sql_path}")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Decompression failed: {e}")
        sys.exit(1)

    # Import to SQLite
    print("\nCreating SQLite database (this may take a few minutes)...")
    db_path = 'database/bibles.db'

    try:
        with open(db_sql_path, 'r') as f:
            subprocess.run(['sqlite3', db_path], stdin=f, check=True)

        db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"  ✅ Created {db_path} ({db_size_mb:.1f} MB)")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Database creation failed: {e}")
        sys.exit(1)

    # Verify database
    print("\nVerifying database...")
    try:
        result = subprocess.run(
            ['sqlite3', db_path, 'SELECT COUNT(*) FROM translations;'],
            capture_output=True,
            text=True,
            check=True
        )
        translation_count = result.stdout.strip()
        print(f"  ✅ Database verified ({translation_count} translations found)")
    except subprocess.CalledProcessError:
        print(f"  ❌ Database verification failed")
        sys.exit(1)

    # Cleanup
    print("\nCleaning up temporary files...")
    try:
        os.remove(db_sql_path)
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

    # Make scripts executable
    if os.path.exists('run_bible_search.sh'):
        os.chmod('run_bible_search.sh', 0o755)
        print("  ✅ Made run_bible_search.sh executable")

    # Create user data database with schema
    print("\nCreating user data database...")
    os.makedirs('database', exist_ok=True)

    # SQL schema for subjects database (current schema)
    schema_sql = '''
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);

CREATE INDEX IF NOT EXISTS idx_subject_verses_subject_id ON subject_verses(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_verses_order ON subject_verses(subject_id, order_index);
CREATE INDEX IF NOT EXISTS idx_subjects_name ON subjects(name);
'''

    # Execute schema
    subprocess.run(['sqlite3', 'database/subjects.db', schema_sql], check=True)
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
    """Install Python dependencies using multiple fallback methods"""
    print_header("Step 3: Install Python Dependencies")

    # First, check if PyQt6 is already installed
    try:
        import PyQt6
        print("  ✅ PyQt6 is already installed")
        return
    except ImportError:
        print("  PyQt6 not found, attempting installation...")

    system = platform.system()

    # Method 1: Try system package manager (Linux only)
    if system == 'Linux':
        print("\n  Method 1: Trying system package manager (apt/dnf/pacman)...")
        try:
            with open('/etc/os-release') as f:
                os_info = f.read().lower()

            if 'debian' in os_info or 'ubuntu' in os_info:
                print("  Installing python3-pyqt6 on Debian/Ubuntu...")
                result = subprocess.run(
                    ['sudo', 'apt-get', 'install', '-y', 'python3-pyqt6'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("  ✅ Installed PyQt6 via apt")
                    return
                else:
                    print(f"  ⚠️  apt install failed: {result.stderr}")

            elif 'fedora' in os_info or 'rhel' in os_info or 'centos' in os_info:
                print("  Installing python3-qt6 on Fedora/RHEL/CentOS...")
                result = subprocess.run(
                    ['sudo', 'dnf', 'install', '-y', 'python3-qt6'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("  ✅ Installed PyQt6 via dnf")
                    return
                else:
                    print(f"  ⚠️  dnf install failed: {result.stderr}")

            elif 'arch' in os_info:
                print("  Installing python-pyqt6 on Arch Linux...")
                result = subprocess.run(
                    ['sudo', 'pacman', '-S', '--noconfirm', 'python-pyqt6'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("  ✅ Installed PyQt6 via pacman")
                    return
                else:
                    print(f"  ⚠️  pacman install failed: {result.stderr}")
        except Exception as e:
            print(f"  ⚠️  System package manager failed: {e}")

    # Method 2: Try pip install (works if PEP 668 not enforced)
    print("\n  Method 2: Trying pip install...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'PyQt6'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  ✅ Installed PyQt6 via pip")
            return
        else:
            print(f"  ⚠️  pip install failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"  ⚠️  pip install failed: {e}")

    # Method 3: Try pip install with --user flag
    print("\n  Method 3: Trying pip install --user...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--user', 'PyQt6'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  ✅ Installed PyQt6 via pip --user")
            return
        else:
            print(f"  ⚠️  pip --user install failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"  ⚠️  pip --user install failed: {e}")

    # Method 4: Instructions for manual installation
    print("\n  ❌ All automatic installation methods failed")
    print("\n  Please install PyQt6 manually using one of these methods:")

    if system == 'Linux':
        try:
            with open('/etc/os-release') as f:
                os_info = f.read().lower()

            if 'debian' in os_info or 'ubuntu' in os_info:
                print("\n  For Ubuntu/Debian:")
                print("    sudo apt-get update")
                print("    sudo apt-get install python3-pyqt6")
            elif 'fedora' in os_info or 'rhel' in os_info or 'centos' in os_info:
                print("\n  For Fedora/RHEL/CentOS:")
                print("    sudo dnf install python3-qt6")
            elif 'arch' in os_info:
                print("\n  For Arch Linux:")
                print("    sudo pacman -S python-pyqt6")
        except:
            pass

        print("\n  Or use a virtual environment:")
        print("    python3 -m venv bible-search-env")
        print("    source bible-search-env/bin/activate")
        print("    pip install PyQt6")

    elif system == 'Darwin':  # macOS
        print("\n  For macOS:")
        print("    pip3 install --user PyQt6")
        print("  Or with Homebrew:")
        print("    brew install pyqt@6")

    elif system == 'Windows':
        print("\n  For Windows:")
        print("    python -m pip install PyQt6")

    print("\n  After manual installation, you can run the application with:")
    print("    ./run_bible_search.sh")

    # Don't exit - let the installation continue, user can install PyQt6 later

def check_directory_empty():
    """Check if directory contains files other than the installer"""
    print("Checking installation directory...")

    # Get list of all files and directories in current directory
    current_files = set(os.listdir('.'))

    # Files that are OK to have (installer and temp files)
    allowed_files = {
        'setup.py',
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
        print(f"    1. Delete all files except setup.py")
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
    print_header("Bible Search Lite - Setup Installer")

    # EARLY CHECKS - before user confirmation
    print("Running pre-installation checks...\n")

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
    print()
    input("Press Enter to continue...")

    try:
        # Check requirements (tools like sqlite3, gunzip)
        check_requirements()

        # Setup database
        setup_database()

        # Download application files
        download_application_files()

        # Install dependencies
        install_dependencies()

        # Success!
        print_header("✅ Installation Complete!")

        print("Bible Search Lite is now installed!")
        print()
        print("To run the application:")
        print("  ./run_bible_search.sh")
        print("  or")
        print("  python3 bible_search_lite.py")
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
