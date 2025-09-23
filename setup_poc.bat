@echo off
REM Bilka Price Monitor - POC Setup
REM Installs minimal dependencies for the web-based POC

echo ========================================
echo  Bilka Price Monitor - POC Setup
echo ========================================
echo.

echo This will install the minimal dependencies needed for the POC.
echo No external applications required - everything runs locally!
echo.

echo Step 1: Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo ✓ Python is available
echo.

echo Step 2: Installing dependencies...
echo This may take a few minutes...
echo.

pip install -r requirements_poc.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ✓ Dependencies installed successfully!
echo.

echo Step 3: Setting up data directory...
if not exist "data" mkdir data
echo ✓ Data directory created
echo.

echo ========================================
echo  SETUP COMPLETE!
echo ========================================
echo.
echo 🎉 Your Bilka Price Monitor POC is ready!
echo.
echo 📋 To run the application:
echo    Double-click: run_poc.bat
echo    Or run: streamlit run simple_poc.py
echo.
echo 🌐 Then open: http://localhost:8501
echo.
echo ✨ Features:
echo    • Real-time scraping from BILKA.dk
echo    • Web-based dashboard
echo    • Limited to ~2000 records
echo    • No external dependencies
echo.
pause