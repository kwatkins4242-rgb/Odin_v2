@echo off
set SCRIPT_DIR=%~dp0

:: SMART ROOT DETECTION
if exist "C:\AI\MyOdin\settings.py" (
    set ROOT=C:\AI\MyOdin\
) else (
    for %%i in ("%SCRIPT_DIR%..") do set ROOT=%%~fpi\
)

cd /d %ROOT%

:: Environment Detection
if exist "%ROOT%.venv\Scripts\activate.bat" (
    set VENV="%ROOT%.venv\Scripts\activate.bat"
) else (
    echo [ERROR] Virtual environment not found. 
    pause
    exit /b
)

echo ======================================================
echo   ODIN — BRIDGE (Standalone Agent Relay)
echo   Resolved Root:  %ROOT%
echo ======================================================

echo [!] Starting Bridge (Port 8099)...
start "ODIN-Bridge" cmd /k "call %VENV% && python odin_bridge.py"

echo ======================================================
echo   Bridge initializing...
echo   Health check: http://localhost:8099/health
echo ======================================================
pause
