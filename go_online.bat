@echo off
REM Bilka Price Monitor - Quick Online Setup Script
REM This script helps you get your dashboard online quickly using ngrok

echo ========================================
echo  Bilka Price Monitor - Online Setup
echo ========================================
echo.

echo Step 1: Checking if Docker is running...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running.
    echo Please install Docker Desktop and start it.
    pause
    exit /b 1
)
echo ✓ Docker is available
echo.

echo Step 2: Starting your dashboard...
cd /d "%~dp0"
docker-compose up --build -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start dashboard.
    echo Check docker-compose logs for details.
    pause
    exit /b 1
)
echo ✓ Dashboard started successfully
echo.

echo Step 3: Checking if ngrok is installed...
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ngrok is not installed.
    echo.
    echo To install ngrok:
    echo 1. Download from: https://ngrok.com/download
    echo 2. Extract ngrok.exe to a folder in your PATH
    echo 3. Run: ngrok authtoken YOUR_AUTH_TOKEN
    echo.
    echo Or install via Chocolatey: choco install ngrok
    echo.
    pause
    exit /b 1
)
echo ✓ ngrok is available
echo.

echo Step 4: Creating secure tunnel...
echo Opening ngrok tunnel to your dashboard...
echo.
echo ========================================
echo  YOUR DASHBOARD IS NOW ONLINE!
echo ========================================
echo.
ngrok http 8501
echo.
echo Press Ctrl+C to stop the tunnel
pause