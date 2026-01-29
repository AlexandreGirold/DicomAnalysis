@echo off

set PYTHON_EXE=%~dp0python\python.exe

:: Check if Python is installed
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    msg * "Python n'est pas installe! Contactez le support technique."
    exit /b 1
)

:: Change to backend directory
cd /d "%~dp0backend"

:: First time setup (silent)
if not exist "env\Scripts\python.exe" (
    "%PYTHON_EXE%" -m venv env
    env\Scripts\python.exe -m pip install --upgrade pip --quiet
    env\Scripts\python.exe -m pip install -r requirements.txt --quiet
    if not exist "data" mkdir data
    if not exist "uploads" mkdir uploads
)

:: Open browser after 5 seconds
start /b timeout /t 5 /nobreak >nul && start http://localhost:8000

:: Start server (hidden console)
start /min "" env\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
