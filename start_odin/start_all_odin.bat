@echo off
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

echo ======================================================
echo   ODIN — MASTER BOOT SEQUENCE
echo ======================================================

:: Phase 1: The Head
echo.
echo [1/2] BOOTING PHASE 1: THE HEAD...
call start_head.bat

:: Wait for Head to stabilize
timeout /t 10

:: Phase 2: The Agents
echo.
echo [2/2] BOOTING PHASE 2: THE AGENTS...
call start_agents.bat

echo.
echo ======================================================
echo   ODIN ECOSYSTEM DEPLOYED.
echo   Monitoring ports: 8000, 8001, 8002, 7002, 8010, 8099, 8080, 8060, 5678
echo ======================================================
pause
