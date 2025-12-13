@echo off
REM Windows Batch file to run Bridge Test Tool
REM Double-click this file to launch the tool

echo Starting Bridge Test Tool...
echo.

python run.py

if errorlevel 1 (
    echo.
    echo Error: Python may not be installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    echo.
    pause
)
