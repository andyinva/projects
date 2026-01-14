#!/bin/bash
# Launch Bible Search Lite in the background
cd "$(dirname "$0")"
python3 bible_search_lite.py &>/dev/null &
disown
