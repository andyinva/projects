#!/bin/bash
# Inventory all documentation and archive files in bible-search-lite project

echo "================================================"
echo "Bible Search Lite - File Inventory"
echo "================================================"
echo ""

# Change to project directory
cd ~/projects/bible-search-lite 2>/dev/null || {
    echo "ERROR: Project directory not found at ~/projects/bible-search-lite"
    echo "Please update the path in this script and run again."
    exit 1
}

echo "Current directory: $(pwd)"
echo ""

# Documentation files
echo "=== DOCUMENTATION FILES (.md, .txt) ==="
find . -maxdepth 2 -type f \( -name "*.md" -o -name "*.txt" \) ! -path "*/\.*" | sort
echo ""

# Archive files
echo "=== ARCHIVE FILES (.zip, .gz, .tar) ==="
find . -maxdepth 2 -type f \( -name "*.zip" -o -name "*.gz" -o -name "*.tar" -o -name "*.tar.gz" \) ! -path "*/\.*" | sort
echo ""

# Phase-related files
echo "=== PHASE-RELATED FILES ==="
find . -maxdepth 2 -type f -name "*PHASE*" ! -path "*/\.*" | sort
find . -maxdepth 2 -type f -name "*phase*" ! -path "*/\.*" | sort
echo ""

# Guide files
echo "=== GUIDE FILES ==="
find . -maxdepth 2 -type f \( -name "*GUIDE*" -o -name "*guide*" \) ! -path "*/\.*" | sort
echo ""

# README files
echo "=== README FILES ==="
find . -maxdepth 2 -type f -name "*README*" ! -path "*/\.*" | sort
echo ""

# Implementation files
echo "=== IMPLEMENTATION FILES ==="
find . -maxdepth 2 -type f \( -name "*IMPLEMENTATION*" -o -name "*implementation*" \) ! -path "*/\.*" | sort
echo ""

# Backup directories
echo "=== BACKUP DIRECTORIES ==="
find . -maxdepth 2 -type d -name "*backup*" ! -path "*/\.*" | sort
echo ""

# File sizes summary
echo "=== FILE SIZES ==="
echo "Documentation files total:"
find . -maxdepth 2 -type f \( -name "*.md" -o -name "*.txt" \) ! -path "*/\.*" -exec du -ch {} + 2>/dev/null | tail -1
echo ""
echo "Archive files total:"
find . -maxdepth 2 -type f \( -name "*.zip" -o -name "*.gz" -o -name "*.tar" -o -name "*.tar.gz" \) ! -path "*/\.*" -exec du -ch {} + 2>/dev/null | tail -1
echo ""

echo "================================================"
echo "Inventory complete!"
echo "================================================"
