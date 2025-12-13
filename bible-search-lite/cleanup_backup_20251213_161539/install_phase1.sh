#!/bin/bash
################################################################################
# Phase 1 Installation Script
# Bible Search Lite - Groups and Subjects Feature
#
# This script extracts and installs Phase 1 files into the correct locations
#
# Usage: ./install_phase1.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(pwd)"

# Verify we're in the right place
if [ ! -f "bible_search_lite.py" ]; then
    echo -e "${RED}Error: Must run from ~/projects/bible-search-lite directory${NC}"
    echo "Current directory: $PROJECT_ROOT"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Phase 1 Installation Script                      ║${NC}"
echo -e "${BLUE}║          Groups and Subjects Feature                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Project directory: $PROJECT_ROOT"
echo ""

# Create backup directory
BACKUP_DIR="backups/phase1_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✓${NC} Created backup directory: $BACKUP_DIR"

# Backup existing files
echo ""
echo -e "${BLUE}Creating backups...${NC}"

if [ -f "bible_search_ui/controllers/__init__.py" ]; then
    cp bible_search_ui/controllers/__init__.py "$BACKUP_DIR/"
    echo -e "${GREEN}✓${NC} Backed up controllers/__init__.py"
fi

if [ -f "bible_search_ui/ui/dialogs.py" ]; then
    cp bible_search_ui/ui/dialogs.py "$BACKUP_DIR/"
    echo -e "${GREEN}✓${NC} Backed up ui/dialogs.py"
fi

# Extract the archive
echo ""
echo -e "${BLUE}Extracting files...${NC}"

TEMP_DIR=$(mktemp -d)
tar -xzf "$SCRIPT_DIR/phase1_deployment.tar.gz" -C "$TEMP_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Failed to extract archive"
    exit 1
fi

echo -e "${GREEN}✓${NC} Extracted files to temporary directory"

# Create services directory
echo ""
echo -e "${BLUE}Creating directory structure...${NC}"

mkdir -p bible_search_ui/services
echo -e "${GREEN}✓${NC} Created bible_search_ui/services/"

# Copy services files
echo ""
echo -e "${BLUE}Installing service layer...${NC}"

cp "$TEMP_DIR/user_data_service.py" bible_search_ui/services/
echo -e "${GREEN}✓${NC} Installed user_data_service.py"

cp "$TEMP_DIR/services__init__.py" bible_search_ui/services/__init__.py
echo -e "${GREEN}✓${NC} Installed services/__init__.py"

# Copy controller files
echo ""
echo -e "${BLUE}Installing controller layer...${NC}"

cp "$TEMP_DIR/user_data_controller.py" bible_search_ui/controllers/
echo -e "${GREEN}✓${NC} Installed user_data_controller.py"

cp "$TEMP_DIR/controllers__init__.py" bible_search_ui/controllers/__init__.py
echo -e "${GREEN}✓${NC} Updated controllers/__init__.py"

# Append to dialogs.py
echo ""
echo -e "${BLUE}Updating UI layer...${NC}"

# Check if dialogs already added
if grep -q "class GroupDialog" bible_search_ui/ui/dialogs.py; then
    echo -e "${YELLOW}⚠${NC} GroupDialog already exists in dialogs.py - skipping"
else
    # Add separator and append new dialogs
    echo "" >> bible_search_ui/ui/dialogs.py
    echo "# ============================================================================" >> bible_search_ui/ui/dialogs.py
    echo "# PHASE 1 ADDITIONS - Groups and Subjects Dialogs" >> bible_search_ui/ui/dialogs.py
    echo "# ============================================================================" >> bible_search_ui/ui/dialogs.py
    echo "" >> bible_search_ui/ui/dialogs.py
    
    # Extract just the dialog classes (skip imports and header)
    sed -n '/^class GroupDialog/,$p' "$TEMP_DIR/dialogs_additions.py" >> bible_search_ui/ui/dialogs.py
    
    echo -e "${GREEN}✓${NC} Appended GroupDialog and SubjectDialog to dialogs.py"
fi

# Copy documentation
echo ""
echo -e "${BLUE}Installing documentation...${NC}"

cp "$TEMP_DIR/IMPLEMENTATION_GUIDE.txt" ./
echo -e "${GREEN}✓${NC} Copied IMPLEMENTATION_GUIDE.txt"

cp "$TEMP_DIR/QUICK_REFERENCE.txt" ./
echo -e "${GREEN}✓${NC} Copied QUICK_REFERENCE.txt"

cp "$TEMP_DIR/PHASE1_SUMMARY.txt" ./
echo -e "${GREEN}✓${NC} Copied PHASE1_SUMMARY.txt"

# Cleanup
rm -rf "$TEMP_DIR"

# Verify installation
echo ""
echo -e "${BLUE}Verifying installation...${NC}"

FILES_OK=true

if [ -f "bible_search_ui/services/__init__.py" ]; then
    echo -e "${GREEN}✓${NC} services/__init__.py"
else
    echo -e "${RED}✗${NC} services/__init__.py - MISSING"
    FILES_OK=false
fi

if [ -f "bible_search_ui/services/user_data_service.py" ]; then
    echo -e "${GREEN}✓${NC} services/user_data_service.py"
else
    echo -e "${RED}✗${NC} services/user_data_service.py - MISSING"
    FILES_OK=false
fi

if [ -f "bible_search_ui/controllers/user_data_controller.py" ]; then
    echo -e "${GREEN}✓${NC} controllers/user_data_controller.py"
else
    echo -e "${RED}✗${NC} controllers/user_data_controller.py - MISSING"
    FILES_OK=false
fi

if grep -q "class GroupDialog" bible_search_ui/ui/dialogs.py; then
    echo -e "${GREEN}✓${NC} ui/dialogs.py (GroupDialog added)"
else
    echo -e "${RED}✗${NC} ui/dialogs.py - GroupDialog NOT FOUND"
    FILES_OK=false
fi

# Final summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"

if [ "$FILES_OK" = true ]; then
    echo -e "${BLUE}║${NC}  ${GREEN}✓ Installation Complete!${NC}                               ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}All files installed successfully!${NC}"
    echo ""
    echo "Backups saved to: $BACKUP_DIR"
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  NEXT STEPS                                                ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Read IMPLEMENTATION_GUIDE.txt"
    echo "   cat IMPLEMENTATION_GUIDE.txt"
    echo ""
    echo "2. Modify bible_search_lite.py (Tasks 4-10)"
    echo "   This is the main work - about 4-6 hours"
    echo ""
    echo "3. Test the application"
    echo "   python3 bible_search_lite.py"
    echo ""
    echo -e "${BLUE}Tip:${NC} Open IMPLEMENTATION_GUIDE.txt in your editor alongside"
    echo "     bible_search_lite.py for easy reference"
    echo ""
else
    echo -e "${BLUE}║${NC}  ${RED}✗ Installation Incomplete${NC}                              ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Some files failed to install. Check errors above.${NC}"
    echo ""
    echo "You can restore from backup:"
    echo "  cp $BACKUP_DIR/* bible_search_ui/[appropriate directory]/"
    exit 1
fi

# Show directory structure
echo ""
echo -e "${BLUE}New directory structure:${NC}"
echo ""
tree -L 3 bible_search_ui/ 2>/dev/null || find bible_search_ui/ -maxdepth 3 -type d -print | sed 's|[^/]*/|  |g'

echo ""
echo -e "${GREEN}Ready to begin Phase 1 implementation!${NC}"
echo ""
