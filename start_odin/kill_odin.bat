@echo off
title ODIN SYSTEM KILLSWITCH
echo ======================================================
echo   ODIN SYSTEM KILLSWITCH
echo   Terminating all ODIN Python processes...
echo ======================================================

:: Force kill all python processes
:: WARNING: This will kill ALL python processes on the machine.
:: If you have other unrelated python apps running, they will be closed.
taskkill /F /IM python.exe /T

echo.
echo ======================================================
echo   Cleanup complete.
echo   You can now run start_head.bat or start_all_odin.bat
echo ======================================================
pause
