@echo off
echo ====================================
echo Starting TARRA QC Application
echo ====================================

set PYTHON_EXE=%~dp0python\python.exe

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "env\Scripts\activate.bat" (
    echo Virtual environment not found. Creating it...
    "%PYTHON_EXE%" -m venv env
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please make sure Python is installed and in your PATH
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

echo Activating Python environment...
call env\Scripts\activate.bat

REM Check if uvicorn is installed
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install --upgrade pip setuptools wheel
    pip install -r ..\requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
    echo Packages installed successfully.
)

echo Starting backend server...
start "TARRA Backend" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Opening frontend...
cd /d "%~dp0frontend"
start "" "http://localhost:8000"

echo.
echo ====================================
echo Application started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8000/index.html
echo ====================================
echo.
echo Press any key to exit this window...
pause >nul