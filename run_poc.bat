@echo off
REM Bilka Price Monitor - Simple POC Launcher
REM Runs the web-based price monitor locally

echo ========================================
echo  Bilka Price Monitor - POC Version
echo ========================================
echo.

echo Starting the Bilka Price Monitor web application...
echo This will open in your default web browser.
echo.
echo Features:
echo - Real-time scraping from BILKA.dk
echo - Web-based dashboard (no installation needed)
echo - Limited to ~2000 records for POC
echo - Automatic data cleanup
echo.
echo Press Ctrl+C to stop the application
echo.

REM Run the Streamlit application
streamlit run simple_poc.py --server.headless true --server.address 0.0.0.0 --server.port 8501

echo.
echo Application stopped.
pause