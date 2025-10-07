@echo off
REM =====================================================
REM Bilka Price Monitor - Manual Scrape (Command Line)
REM Use this when Streamlit scraping doesn't work
REM =====================================================

echo.
echo ========================================================
echo    Bilka Price Monitor - Manual Scrape
echo ========================================================
echo.
echo This will scrape products from Bilka.dk using command line
echo (Works better than Streamlit for web scraping)
echo.

cd /d "%~dp0"

REM Get user input for category
echo Select category:
echo   1) Electronics (recommended)
echo   2) Home
echo   3) Fashion
echo   4) Sports
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" set category=electronics
if "%choice%"=="2" set category=home
if "%choice%"=="3" set category=fashion
if "%choice%"=="4" set category=sports

if not defined category (
    echo Invalid choice, using electronics
    set category=electronics
)

echo.
echo Selected category: %category%
echo.

REM Get number of products
set /p max_products="How many products to scrape? (10-200, default 50): "
if "%max_products%"=="" set max_products=50

echo.
echo ========================================================
echo Starting scrape: %category% - %max_products% products
echo ========================================================
echo.

REM Run the scraper
python main.py scrape --category %category% --max-products %max_products%

echo.
echo ========================================================
echo Scrape complete!
echo ========================================================
echo.
echo Now you can:
echo   1. Open the dashboard to view results
echo   2. Run this script again for more products
echo.

pause
