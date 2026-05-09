"""
Master Launcher
File: C:\AI\MyOdin\start.py
Run:  python start.py   (.\start_odin.bat)
"""

import subprocess
import sys
import os
import time

# ── Always use the Python that is running THIS script ──
# This is what fixes the _execute_child error.
# Never hardcode a path like "C:\Python3.10.11\python.exe"
PYTHON = sys.executable

# ── Module list ────────────────────────────────────────
# (name, folder, start script)
# Add or comment out modules as needed
MODULES = [
    ("CORE",    r"C:\AI\MyOdin\M1\CORE",     "start.py"),
    ("MEMORY",  r"C:\AI\MyOdin\M1\MEMORY",   "start.py"),
    ("HUNTER",  r"C:\AI\MyOdin\P1\HUNTER",   "start.py"),
    ("SENSE",   r"C:\AI\MyOdin\M2\SENSE",    "start.py"),
    ("FACE",    r"C:\AI\MyOdin\M2\FACE",     "start.py"),
    ("BRIDGE",  r"C:\AI\MyOdin\BRIDGE",      "start.py"),
    ("VISION",  r"C:\AI\MyOdin\P2\VISION",   "start.py"),
    ("MOBILE",  r"C:\AI\MyOdin\P2\MOBILE",   "start.py"),
    ("COMMS",   r"C:\AI\MyOdin\M3\COMMS",    "start.py"),
    ("N8N",     r"C:\AI\MyOdin\N8N",         "start.py"),
]
processes = []

print()
print("╔══════════════════════════════════════════╗")
print("║           ODIN SYSTEM LAUNCHER           ║")
print(f"║  Python: {PYTHON[:34]:<34}║")
print("╚══════════════════════════════════════════╝")
print()

for name, folder, script in MODULES:
    full_script = os.path.join(folder, script)

    # Skip if folder or script doesn't exist — don't crash
    if not os.path.isdir(folder):
        print(f"  [SKIP]  {name} — folder not found: {folder}")
        continue
    if not os.path.isfile(full_script):
        print(f"  [SKIP]  {name} — start.py not found in {folder}")
        continue

    print(f"  [START] {name}...")

    try:
        proc = subprocess.Popen(
            [PYTHON, script],
            cwd=folder,
            # Each module gets its own console window on Windows
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
        )
        processes.append((name, proc))
        time.sleep(1.5)
        print(f"  [OK]    {name} running  (PID {proc.pid})")

    except FileNotFoundError:
        print(f"  [ERROR] {name} — Python not found at: {PYTHON}")
        print(f"          Make sure you activated .venv before running start.py")

    except Exception as e:
        print(f"  [ERROR] {name} — {e}")

print()
print(f"  {len(processes)}/{len(MODULES)} module(s) started.")
print()
print("  ODIN_IDE.html  →  open in your browser")
print("  Ctrl+C         →  stop everything")
print()

try:
    while True:
        time.sleep(3)
        for name, proc in processes:
            if proc.poll() is not None:
                print(f"  [WARN]  {name} stopped (exit code {proc.returncode})")
except KeyboardInterrupt:
    print()
    print("  Stopping all modules...")
    for name, proc in processes:
        try:
            proc.terminate()
            print(f"  [STOP]  {name}")
        except Exception:
            pass
    print()
    print("  ODIN offline. Goodbye.")
    print()
