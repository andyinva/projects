#!/bin/bash
# Installation script for refactored Bible Search

echo "==================================================="
echo "Bible Search - Refactoring Installation"
echo "==================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "bible_search_lite.py" ]; then
    echo "ERROR: bible_search_lite.py not found in current directory"
    echo "Please run this script from ~/projects/bible-search/"
    exit 1
fi

echo "Step 1: Creating backup of original files..."
cp bible_search_lite.py bible_search_lite.py.backup
echo "✓ Backup created: bible_search_lite.py.backup"
echo ""

echo "Step 2: Creating bible_search module directory..."
mkdir -p bible_search/ui
echo "✓ Created: bible_search/ui/"
echo ""

echo "Step 3: Ready to copy refactored files..."
echo ""
echo "Please copy these files from the refactored version:"
echo "  1. bible_search/__init__.py"
echo "  2. bible_search/ui/__init__.py"
echo "  3. bible_search/ui/widgets.py"
echo "  4. bible_search_lite.py (replaces current version)"
echo ""
echo "After copying, test with: python3 bible_search_lite.py"
echo ""
echo "If there are any issues, restore with:"
echo "  mv bible_search_lite.py.backup bible_search_lite.py"
echo "  rm -rf bible_search/"
echo ""
echo "==================================================="
