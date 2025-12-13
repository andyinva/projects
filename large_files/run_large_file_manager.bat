@echo off
REM Large File Manager Launcher (Windows Batch File)

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Try to run with python, if that fails try python3
python large_file_manager.py 2>nul
if %errorlevel% neq 0 (
    python3 large_file_manager.py
)
