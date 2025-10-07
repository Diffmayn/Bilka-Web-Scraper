@echo off
REM =====================================================
REM Bilka Price Monitor - Local Dashboard
REM =====================================================

echo.
echo ========================================================
echo    Bilka Price Monitor - Starting Dashboard...
echo ========================================================
echo.

cd /d "%~dp0"

REM Check if streamlit is installed
echo Checking dependencies...
python -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Streamlit is not installed!
    echo.
    echo Installing required packages...
    python -m pip install streamlit selenium beautifulsoup4 sqlalchemy pyyaml pandas numpy scikit-learn webdriver-manager
    echo.
)

REM Check if sqlalchemy is installed
python -c "import sqlalchemy" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing missing dependencies...
    python -m pip install sqlalchemy beautifulsoup4 pyyaml pandas numpy scikit-learn selenium webdriver-manager lxml
    echo.
)

REM Run Streamlit with auto-open browser
echo.
echo Starting Streamlit dashboard...
echo Browser will open automatically at: http://localhost:8501
echo.
echo Press CTRL+C to stop the dashboard
echo.

python -m streamlit run streamlit_app.py --server.port 8501 --server.address localhost --browser.gatherUsageStats false

pause
