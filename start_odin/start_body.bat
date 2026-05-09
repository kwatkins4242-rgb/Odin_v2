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
echo   ODIN — THE BODY (M3 ^& M4 Extension Systems)
echo   Resolved Root:  %ROOT%
echo ======================================================

:: ── M3 MODULES ──────────────────────────────────────
echo [1/7] M3 — Starting Comms (Port 8005)...
start "ODIN-Comms" cmd /k ""%VENV%" && python M3\comms\main_comms.py || pause"

echo [2/7] M3 — Starting Engineering (Port 8006)...
start "ODIN-Eng" cmd /k ""%VENV%" && python M3\engineering\main_start.py || pause"

echo [3/7] M3 — Starting Info (Port 8007)...
start "ODIN-Info" cmd /k ""%VENV%" && python M3\info\main_start.py || pause"

echo [4/7] M3 — Starting Control (Port 8008)...
start "ODIN-Ctrl" cmd /k ""%VENV%" && python M3\control\main_start.py || pause"

:: ── M4 & PERIPHERALS ────────────────────────────────
echo [5/7] M4 — Starting Agent Tom (Port 8060)...
start "ODIN-Tom" cmd /k ""%VENV%" && python M4\agents\main_start.py || pause"

echo [!] Starting Bridge (Port 8099)...
start "ODIN-Bridge" cmd /k ""%VENV%" && python odin_bridge.py || pause"

echo [6/7] P1 — Starting Hunter (Port 8030)...
start "ODIN-Hunter" cmd /k ""%VENV%" && python P1\hunter\main.py || pause"

echo [7/7] P2 — Starting Mobile (Port 8040)...
start "ODIN-Mobile" cmd /k ""%VENV%" && python P2\mobile\main.py || pause"

echo ======================================================
echo   M3 ^& M4 Online. Systems integrated.
echo   Note: Bridge and n8n are standalone.
echo ======================================================
pause
