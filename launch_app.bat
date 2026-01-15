@echo off
echo ====================================
echo Starting TARRA QC Application
echo ====================================

cd /d "%~dp0backend"

echo Activating Python environment...
call env\Scripts\activate.bat

echo Starting backend server...
start "TARRA Backend" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Opening frontend...
cd /d "%~dp0frontend"
start "" "http://localhost:8000/index.html"

echo.
echo ====================================
echo Application started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8000/index.html
echo ====================================
echo.
echo Press any key to exit this window...
pause >nul
