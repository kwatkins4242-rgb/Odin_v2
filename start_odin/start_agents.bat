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
    set VENV=%ROOT%.venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found. 
    pause
    exit /b
)

echo ======================================================
echo   ODIN — PHASE 2: THE AGENTS (Automation)
echo   Resolved Root:  %ROOT%
echo ======================================================

:: ── M4 AGENTS ────────────────────────────────────────
echo [1/2] M4 — Starting Agent Tom Service (Port 8060)...
start "ODIN-Tom" cmd /k ""%VENV%" && python M4\agents\main_start.py || pause"

:: ── n8n DASHBOARD ────────────────────────────────────
echo [2/2] Note: n8n should be started manually in its own terminal.
echo       n8n Dashboard:  http://localhost:5678

echo ======================================================
echo   PHASE 2 DEPLOYED. Agents are active.
echo   n8n Dashboard:  http://localhost:5678
echo ======================================================
timeout /t 5
