@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

where "%PYTHON%" >nul 2>nul
if errorlevel 1 (
    echo Python was not found in the project environment or on PATH.
    echo Install dependencies first with:
    echo   python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting the Research Agent...
start "Research Agent" "%PYTHON%" -m streamlit run front.py --server.headless true --server.port 8502
powershell -NoProfile -Command "Start-Sleep -Seconds 6; Start-Process 'http://localhost:8502'"

echo The app is starting in a browser window.
echo If the browser does not open, visit: http://localhost:8502
pause
