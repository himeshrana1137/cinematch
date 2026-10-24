@echo off
cd /d "%~dp0"
echo ========================================
echo        CineMatch Movie Recommender
echo ========================================

if exist "venv\Scripts\python.exe" goto usevenv
if exist "backend\venv\Scripts\python.exe" goto usebackendvenv
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 goto fail
:usevenv
set PYEXE=%~dp0venv\Scripts\python.exe
goto installpy
:usebackendvenv
set PYEXE=%~dp0backend\venv\Scripts\python.exe

:installpy
echo Installing backend packages...
"%PYEXE%" -m pip install -q -r backend\requirements.txt
if errorlevel 1 goto fail

if not exist "backend\data\ratings.csv" "%PYEXE%" backend\download_data.py

if not exist "frontend\node_modules" call npm install --prefix frontend

echo Starting servers...
start "CineMatch Backend" cmd /k "cd /d %~dp0backend && %PYEXE% app.py"
start "CineMatch Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 10 >nul
start http://localhost:5173
echo Done. Keep the two black windows open.
pause
exit /b 0

:fail
echo.
echo Something failed. Read the message above.
pause
exit /b 1