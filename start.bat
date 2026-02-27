@echo off
:: ============================================================
:: start.bat — Starts the Real Estate Marketing AI Agent
::
:: What it does:
::   1. Installs Python dependencies (if not already installed)
::   2. Starts the Flask backend server
::   3. Opens the app in your default browser
:: ============================================================

echo.
echo   Real Estate Marketing AI Agent
echo   ================================
echo.

:: Check that Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check that .env file exists
if not exist "%~dp0.env" (
    echo [ERROR] .env file not found.
    echo         Copy .env.example to .env and add your API keys:
    echo           GOOGLE_MAPS_API_KEY=your_key_here
    echo           GEMINI_API_KEY=your_key_here
    echo.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r "%~dp0requirements.txt" --quiet
echo       Done.
echo.

:: Open the browser after a short delay (gives Flask time to start)
echo [2/3] Opening browser in 3 seconds...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:5000"

:: Start Flask
echo [3/3] Starting Flask server...
echo       Press Ctrl+C to stop.
echo.
python "%~dp0app.py"
