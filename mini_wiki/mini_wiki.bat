@echo off
REM mini_wiki - Universal Research Assistant
REM Self-bootstrapping entry point for Windows

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python is not installed or not in PATH
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo ✓ Python %PYTHON_VERSION% detected

REM Run the Python bootstrap script
python "%SCRIPT_DIR%run.py" %*
if errorlevel 1 (
    echo ✗ Bootstrap failed
    exit /b 1
)

endlocal
