@echo off
cls
echo ============================================
echo   MLC Blade Analysis Application
echo ============================================
echo.

:: Change to the backend directory
cd /d "%~dp0backend"

:: Check if virtual environment exists
echo [1/3] Checking virtual environment...
if not exist "env\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment not found!
    echo Location checked: %CD%\env\Scripts\python.exe
    echo.
    echo Please create a virtual environment first by running:
    echo   python -m venv env
    echo   env\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo       Virtual environment found: OK

:: Check if uvicorn is installed
echo [2/3] Checking dependencies...
env\Scripts\python.exe -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: uvicorn not found!
    echo Please install dependencies:
    echo   env\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo       Dependencies installed: OK

:: Start the server
echo [3/3] Starting FastAPI server...
echo.
echo ============================================
echo   Server Starting...
echo   URL: http://localhost:8000
echo ============================================
echo.
echo The browser will open in 5 seconds...
echo Press Ctrl+C to stop the server
echo.

:: Wait 5 seconds then open browser
timeout /t 5 /nobreak >nul
start http://localhost:8000

:: Start the server
env\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo.
echo Server stopped.
pause
