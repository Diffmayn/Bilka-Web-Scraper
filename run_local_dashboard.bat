@echo off
REM =====================================================
REM Bilka Price Monitor - Local Dashboard
REM =====================================================

echo Starting Bilka Price Monitor Dashboard...
echo.
echo Dashboard will open at: http://localhost:8501
echo Press CTRL+C to stop the dashboard
echo.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run Streamlit with local settings
streamlit run streamlit_app.py --server.port 8501 --server.address localhost

pause
