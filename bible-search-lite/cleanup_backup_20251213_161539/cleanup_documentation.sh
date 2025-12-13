#!/bin/bash
# Safe cleanup script for bible-search-lite documentation
# Creates backup before removing any files

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR=~/projects/bible-search-lite

echo "================================================"
echo "Bible Search Lite - Safe Cleanup Script"
echo "================================================"
echo ""

# Change to project directory
cd "$PROJECT_DIR" 2>/dev/null || {
    echo -e "${RED}ERROR: Project directory not found at $PROJECT_DIR${NC}"
    echo "Please update PROJECT_DIR in this script and run again."
    exit 1
}

echo -e "${GREEN}Current directory: $(pwd)${NC}"
echo ""

# Create backup directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="cleanup_backup_${TIMESTAMP}"

echo -e "${YELLOW}Step 1: Creating backup directory${NC}"
mkdir -p "$BACKUP_DIR"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Function to backup and list file
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "  Backing up: $file"
        cp "$file" "$BACKUP_DIR/"
        return 0
    fi
    return 1
}

# Function to backup and remove file
remove_file() {
    local file="$1"
    if [ -f "$file" ]; then
        backup_file "$file"
        rm "$file"
        echo -e "  ${GREEN}✓${NC} Removed: $file"
        return 0
    fi
    return 1
}

echo -e "${YELLOW}Step 2: Backing up files that will be removed${NC}"
echo ""

# Files to remove (after backing up)
FILES_TO_REMOVE=(
    # Phase 1 deployment files (now consolidated into COMPLETE_DOCUMENTATION.md)
    "IMPLEMENTATION_GUIDE.txt"
    "QUICK_REFERENCE.txt"
    "PHASE1_SUMMARY.txt"
    "README_PHASE1.txt"
    "install_phase1.sh"
    
    # Deployment archives (already installed)
    "phase1_deployment.tar.gz"
    "phase1_deployment.tar"
    "phase1_deployment.zip"
    
    # Duplicate or temporary documentation
    "PHASE1_*.txt"
    "phase1_*.txt"
    "*_BACKUP_*.txt"
    "temp_*.txt"
    "old_*.md"
    
    # Old installation scripts (if Phase 1 is complete)
    "*install*.sh.backup"
    "*.sh~"
)

# Count backed up files
BACKUP_COUNT=0

# Backup each file that exists
for pattern in "${FILES_TO_REMOVE[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            backup_file "$file"
            ((BACKUP_COUNT++))
        fi
    done
done

echo ""
echo -e "${GREEN}Backed up $BACKUP_COUNT file(s)${NC}"
echo ""

# Ask for confirmation before deletion
echo -e "${YELLOW}Step 3: Confirm deletion${NC}"
echo ""
echo "The following files will be removed:"
echo ""

REMOVE_COUNT=0
for pattern in "${FILES_TO_REMOVE[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo "  - $file"
            ((REMOVE_COUNT++))
        fi
    done
done

echo ""
echo -e "${YELLOW}Total files to remove: $REMOVE_COUNT${NC}"
echo -e "${GREEN}All files have been backed up to: $BACKUP_DIR${NC}"
echo ""

read -p "Do you want to proceed with deletion? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo -e "${YELLOW}Cleanup cancelled. Backup directory preserved: $BACKUP_DIR${NC}"
    echo "You can review the files and run this script again."
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 4: Removing files${NC}"
echo ""

# Remove files
REMOVED_COUNT=0
for pattern in "${FILES_TO_REMOVE[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            rm "$file"
            echo -e "  ${GREEN}✓${NC} Removed: $file"
            ((REMOVED_COUNT++))
        fi
    done
done

echo ""
echo -e "${GREEN}Removed $REMOVED_COUNT file(s)${NC}"
echo ""

# Clean up empty directories
echo -e "${YELLOW}Step 5: Cleaning up empty directories${NC}"
echo ""

# Remove empty backup directories (but not our new backup)
find . -maxdepth 1 -type d -name "backup*" ! -name "$BACKUP_DIR" -empty -exec rmdir {} \; 2>/dev/null || true
find ./backups -maxdepth 1 -type d -empty -exec rmdir {} \; 2>/dev/null || true

echo "Empty directories removed (if any)"
echo ""

# Summary
echo "================================================"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo "================================================"
echo ""
echo "Summary:"
echo "  - Files backed up: $BACKUP_COUNT"
echo "  - Files removed: $REMOVED_COUNT"
echo "  - Backup location: $BACKUP_DIR"
echo ""
echo "Important:"
echo "  1. Review the backup directory to ensure nothing important was removed"
echo "  2. If you need to restore: cp $BACKUP_DIR/* ."
echo "  3. Once satisfied, you can remove the backup: rm -rf $BACKUP_DIR"
echo ""
echo "Recommended next steps:"
echo "  1. Move COMPLETE_DOCUMENTATION.md to your project root"
echo "  2. Update README.md if needed"
echo "  3. Commit changes to git"
echo ""
echo -e "${GREEN}All done!${NC}"
