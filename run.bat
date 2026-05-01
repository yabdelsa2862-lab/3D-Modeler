@echo off
cd /d "%~dp0"

:: Check Python is on PATH
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Install from https://python.org
    pause & exit /b 1
)

:: Create virtual environment on first run
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Launch with pythonw.exe — no console window, errors go to forge3d.log
:: "start """ returns immediately so this window closes right away.
if exist "%~dp0venv\Scripts\pythonw.exe" (
    start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0bootstrap.py"
) else (
    :: Fallback: pythonw not found, use python (shows a brief console)
    start "" python "%~dp0bootstrap.py"
)
