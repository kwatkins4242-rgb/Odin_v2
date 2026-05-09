@echo off
REM ══════════════════════════════════════════════════
REM  ODIN — One-Click Setup
REM  Double-click this file OR run from Command Prompt
REM  Place this file at C:\AI\MyOdin\SETUP.bat
REM ══════════════════════════════════════════════════

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║        ODIN SETUP — FRESH WINDOWS     ║
echo  ╚═══════════════════════════════════════╝
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found!
    echo  Please install Python first:
    echo  https://python.org/downloads
    echo.  IMPORTANT: Check "Add Python to PATH" during install
    pause
    exit /b 1
)

echo  [OK] Python found:
echo.  python --version


REM Create folders
echo  [CREATE] Making ODIN folders...
mkdir C:\AI\MyOdin\M1\core       2>nul
mkdir C:\AI\MyOdin\M1\memory     2>nul
mkdir C:\AI\MyOdin\M1\sense      2>nul
mkdir C:\AI\MyOdin\M1\vision     2>nul
mkdir C:\AI\MyOdin\M1\hunter     2>nul
mkdir C:\AI\MyOdin\M1\mobile     2>nul
echo.  [OK] Folders ready

REM Create venv
echo  [VENV] Creating virtual environment...
cd /d F:\ODIN
if not exist .venv (
    python -m venv .venv
    echo  [OK] .venv created
) else (
    echo  [OK] .venv already exists
)
echo.

REM Activate and install packages
echo  [PIP] Installing packages (this takes a minute)...
call .venv\Scripts\activate.bat

pip install --quiet fastapi
pip install --quiet "uvicorn[standard]"
pip install --quiet python-dotenv
pip install --quiet httpx
pip install --quiet requests
pip install --quiet openai
pip install --quiet google-generativeai
pip install --quiet python-multipart
pip install --quiet aiofiles
pip install --quiet websockets
pip install --quiet pyttsx3
pip install --quiet SpeechRecognition

echo  [PIP] Installing PyAudio...
pip install --quiet pipwin
pipwin install pyaudio

echo.
echo  [OK] All packages installed
echo.

REM Verify key packages
echo  [CHECK] Verifying installs...
python -c "import fastapi; print('  fastapi:', fastapi.__version__)"
python -c "import uvicorn; print('  uvicorn:', uvicorn.__version__)"
python -c "import dotenv; print('  python-dotenv: OK')('pyaudio', pipwin',)"
python -c "import google.generativeai; print('  google-generativeai: OK')" 
2>nul ||
echo.     "google-generativeai: check manually"

echo.  ══════════════════════════════════════════
echo.   SETUP COMPLETE
echo.  ══════════════════════════════════════════
pause
