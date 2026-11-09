@echo off
setlocal
title SynthLeak Local Development Launcher

echo ======================================================================
echo             SynthLeak - Real-Time Acoustic Pipeline Monitoring
echo                    Local Development Environment (Windows)
echo ======================================================================
echo.

:: 1. Verify Repository Directory
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 2. Verify Python Virtual Environment
if not exist "%ROOT_DIR%.venv\Scripts\python.exe" goto :err_no_venv
echo [OK] Python virtual environment detected: .venv

:: 3. Verify Node.js and NPM
where npm >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :npm_found

if exist "C:\nvm4w\nodejs\npm.cmd" (
    set "PATH=C:\nvm4w\nodejs;%PATH%"
    goto :npm_found
)
if exist "C:\Program Files\nodejs\npm.cmd" (
    set "PATH=C:\Program Files\nodejs;%PATH%"
    goto :npm_found
)
if exist "%LOCALAPPDATA%\Programs\nodejs\npm.cmd" (
    set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
    goto :npm_found
)

where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :err_no_npm

:npm_found
echo [OK] Node package manager detected.

:: 4. Verify Frontend Dependencies
if exist "%ROOT_DIR%frontend\node_modules" goto :deps_ok
echo [INFO] Installing frontend dependencies (one-time setup)...
cd /d "%ROOT_DIR%frontend"
call npm install
cd /d "%ROOT_DIR%"

:deps_ok
echo [OK] Frontend dependencies verified.

:: 5. Ensure SQLite Storage Directory Exists
if not exist "%ROOT_DIR%data" (
    mkdir "%ROOT_DIR%data"
)

echo.
echo ======================================================================
echo Starting Services...
echo   - Backend:  http://127.0.0.1:8000
echo   - Frontend: http://localhost:5173
echo   - API Docs: http://127.0.0.1:8000/docs
echo ======================================================================
echo.

:: 6. Launch Backend in a Dedicated Window
start "SynthLeak Backend" cmd /k "title SynthLeak Backend && .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

:: 7. Launch Frontend in a Dedicated Window
start "SynthLeak Frontend" cmd /k "title SynthLeak Frontend && cd frontend && npm run dev"

:: 8. Wait for Services and Open Dashboard in Browser
echo Waiting for services to initialize...
ping 127.0.0.1 -n 4 >nul
start http://localhost:5173

echo.
echo [SUCCESS] SynthLeak is running!
echo Both services are running in their respective command windows with live logs.
echo To stop SynthLeak, double-click stop-dev.bat or close both command windows.
echo ======================================================================
echo.
pause
goto :eof

:err_no_venv
echo.
echo [ERROR] Python virtual environment was not found at:
echo   %ROOT_DIR%.venv
echo.
echo Please create the virtual environment first:
echo   python -m venv .venv
echo   .venv\Scripts\pip install -r requirements.txt
echo.
pause
exit /b 1

:err_no_npm
echo.
echo [ERROR] Node.js / npm was not found on your system.
echo Please install Node.js (version 18 or higher) from https://nodejs.org
echo.
pause
exit /b 1
