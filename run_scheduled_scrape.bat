@echo off
REM =====================================================
REM Bilka Price Monitor - Scheduled Scrape
REM For use with Windows Task Scheduler
REM =====================================================

cd /d "%~dp0"

REM Create log directory if it doesn't exist
if not exist "logs" mkdir logs

REM Log start time
echo ================================== >> logs\scheduled_scrape.log
echo Scheduled scrape started: %date% %time% >> logs\scheduled_scrape.log

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run scrape for electronics category (most common)
python main.py --category electronics --max-products 100 >> logs\scheduled_scrape.log 2>&1

REM Log completion
echo Scheduled scrape completed: %date% %time% >> logs\scheduled_scrape.log
echo ================================== >> logs\scheduled_scrape.log
echo. >> logs\scheduled_scrape.log
