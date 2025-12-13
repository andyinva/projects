#!/bin/bash
# Shell script to run Bridge Test Tool on Linux/Mac

echo "Starting Bridge Test Tool..."
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

# Run the tool
python3 run.py

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo
    echo "Error: Failed to run Bridge Test Tool"
    echo "Exit code: $exit_code"
fi

exit $exit_code
