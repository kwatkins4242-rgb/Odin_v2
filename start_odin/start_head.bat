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
echo   ODIN — PHASE 1: THE HEAD (Core Intelligence)
echo   Resolved Root:  %ROOT%
echo ======================================================

:: ── M1 CORE ──────────────────────────────────────────
echo [1/7] M1 — Starting Brain (Port 8000)...
start "ODIN-Brain" cmd /k ""%VENV%" && python M1\main.py || pause"

echo [2/7] M1 — Starting Memory Pro (Port 8001)...
start "ODIN-Memory" cmd /k ""%VENV%" && python M1\memory_pro\main.py || pause"

echo [3/7] M1 — Starting Core (Port 8002)...
start "ODIN-Core" cmd /k ""%VENV%" && python M1\core\ODIN_CORE_main.py || pause"

:: ── M2 INTERFACE ─────────────────────────────────────
echo [4/7] M2 — Starting Senses (Port 8010)...
start "ODIN-Sense" cmd /k ""%VENV%" && python M2\sense\main.py || pause"

echo [5/8] M2 — Starting Face Pro (Port 7002)...
start "ODIN-Face" cmd /k ""%VENV%" && python M2\chatface_pro\main_start.py || pause"

echo [6/8] M2 — Starting Vision (Port 8015)...
start "ODIN-Vision" cmd /k ""%VENV%" && python M2\vision\main_start.py || pause"

:: ── BRIDGE ───────────────────────────────────────────
echo [7/8] Starting ODIN Bridge (Port 8099)...
start "ODIN-Bridge" cmd /k ""%VENV%" && python odin_bridge.py || pause"

:: ── DASHBOARD ───────────────────────────────────────
echo [8/8] Starting Master Hub Dashboard (Port 8080)...
start "ODIN-Hub" cmd /k ""%VENV%" && python dashboards\start_dashboards.py || pause"

echo ======================================================
echo   PHASE 1 COMPLETE. The Head is online.
echo   Master Hub: http://localhost:8080
echo ======================================================
timeout /t 5
