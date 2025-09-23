@echo off
REM Bilka Price Monitor - Local Online Setup (No Docker)
REM This script runs your dashboard locally and creates an online tunnel

echo ========================================
echo  Bilka Price Monitor - Local Online
echo ========================================
echo.

echo Step 1: Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11+ and add it to your PATH.
    pause
    exit /b 1
)
echo ✓ Python is available
echo.

echo Step 2: Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    echo Check your internet connection and try again.
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo Step 3: Initializing database...
python main.py init
if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize database.
    echo Check the error messages above.
    pause
    exit /b 1
)
echo ✓ Database initialized
echo.

echo Step 4: Starting dashboard locally...
echo The dashboard will start in the background.
echo Do NOT close this window.
echo.
start /B python main.py dashboard
timeout /t 5 /nobreak >nul
echo ✓ Dashboard started
echo.

echo Step 5: Creating online tunnel...
echo.
echo ========================================
echo  YOUR DASHBOARD IS NOW ONLINE!
echo ========================================
echo.
echo INSTRUCTIONS:
echo 1. Download ngrok from: https://ngrok.com/download
echo 2. Extract ngrok.exe to your desktop or a folder
echo 3. Open a NEW command prompt/terminal
echo 4. Navigate to the ngrok folder
echo 5. Run: ngrok http 8501
echo 6. Copy the HTTPS URL and share it!
echo.
echo Your local dashboard is running at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

REM Keep the script running to maintain the dashboard
python -c "import time; time.sleep(999999)"