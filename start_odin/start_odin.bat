@echo off
set SCRIPT_DIR=%~dp0

:: SMART ROOT DETECTION
if exist "C:\AI\MyOdin\settings.py" (
    set ROOT=C:\AI\MyOdin\
) else (
    for %%i in ("%SCRIPT_DIR%..") do set ROOT=%%~fpi\
)

cd /d %ROOT%

:: Environment Detection (Check project root first)
if exist "%ROOT%.venv\Scripts\activate.bat" (
    set VENV=%ROOT%.venv\Scripts\activate.bat
) else if exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    set VENV=%SCRIPT_DIR%.venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    set VENV=venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found. 
    echo Please ensure ODIN is at C:\AI\MyOdin or your .venv is correctly placed.
    pause
    exit /b
)

echo ======================================================
echo   ODIN Modular Launcher — Smart Pathing Edition
echo   Current Script: %SCRIPT_DIR%
echo   Resolved Root:  %ROOT%
echo   Resolved Venv:  %VENV%
echo ======================================================

:: 1. Brain (8000)
echo [1/11] Starting Brain (Port 8000)...
start "Brain" cmd /k "call "%VENV%" && python M1\main.py || pause"

:: 2. Memory Pro (8001)
echo [2/11] Starting Memory (Port 8001)...
start "Memory" cmd /k "call "%VENV%" && python M1\memory_pro\main.py || pause"

:: 3. Core (8002)
echo [3/11] Starting Core (Port 8002)...
start "Core" cmd /k "call "%VENV%" && python M1\core\ODIN_CORE_main.py || pause"

:: 4. Comms (8005)
echo [4/11] Starting Comms (Port 8005)...
if exist M3\comms\main_comms.py (
    start "Comms" cmd /k "call "%VENV%" && python M3\comms\main_comms.py || pause"
) else (
    echo [SKIP] M3 Comms entry point not found.
)

:: 5. Sense (8010)
echo [5/11] Starting Senses (Port 8010)...
start "Senses" cmd /k "call "%VENV%" && python M2\sense\main.py || pause"

:: 6. Agent Tom (8060)
echo [6/11] Starting Agent Tom (Port 8060)...
start "Agent Tom" cmd /k "call "%VENV%" && python M4\agents\main_start.py || pause"

:: 7. Hunter (8030)
echo [7/11] Starting Hunter (Port 8030)...
start "Hunter" cmd /k "call "%VENV%" && python P1\hunter\main.py || pause"

:: 8. Mobile (8040)
echo [8/11] Starting Mobile (Port 8040)...
start "Mobile" cmd /k "call "%VENV%" && python P2\mobile\main.py || pause"

:: 9. Bridge (8099)
echo [9/11] Starting Bridge (Port 8099)...
if exist odin_bridge.py (
    start "Bridge" cmd /k "call "%VENV%" && python odin_bridge.py || pause"
) else (
    echo [SKIP] odin_bridge.py not found.
)

:: 10. Master UI Hub (8080/9050)
echo [10/11] Starting Master Dashboard Hub (Port 8080)...
start "Dashboard Hub" cmd /k "call "%VENV%" && python dashboards\start_dashboards.py || pause"

echo [11/11] n8n (External Port 5678)
echo Ensure n8n is running at http://localhost:5678

echo ======================================================
echo   All systems initializing.
echo   Master Dashboard (Hub): http://localhost:8080
echo   Direct Brain UI:        http://localhost:8000
echo ======================================================
