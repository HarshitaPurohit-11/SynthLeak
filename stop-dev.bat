@echo off
setlocal
title Stop SynthLeak Local Services

echo ======================================================================
echo                 Stopping SynthLeak Local Services
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Close known SynthLeak terminal windows
taskkill /fi "WINDOWTITLE eq SynthLeak Backend*" /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq SynthLeak Frontend*" /f /t >nul 2>&1

:: Terminate processes listening on port 8000 or 5173
if exist "%ROOT_DIR%.venv\Scripts\python.exe" (
    "%ROOT_DIR%.venv\Scripts\python.exe" "%ROOT_DIR%scripts\stop_services.py"
) else (
    python "%ROOT_DIR%scripts\stop_services.py" >nul 2>&1
)

echo.
echo [OK] SynthLeak backend and frontend shutdown complete.
echo ======================================================================
echo.
ping 127.0.0.1 -n 3 >nul
