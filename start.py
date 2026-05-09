#!/usr/bin/env python3
"""
ODIN-CORE — Startup Script
Run this from the odin-core/ directory:
    python start.py
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

procs = []

MODULES = [
    # (label,        command)
    ("odin-core",   [sys.executable, "main.py"]),
]

def log(msg):
    print(f"[ODIN] {msg}")

def start():
    Path("logs").mkdir(exist_ok=True)

    for label, cmd in MODULES:
        log(f"Starting {label}...")
        p = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        p.label = label
        procs.append(p)
        time.sleep(0.5)

    log("Core is up. Ctrl-C to stop.")

def shutdown(sig=None, frame=None):
    log("Shutting down...")
    for p in procs:
        log(f"  stopping {p.label}")
        p.terminate()
    log("Done.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

if __name__ == "__main__":
    start()
    while True:
        time.sleep(1)



# modules/family.py
# class OdinFamily:
#     def __init__(self, core):
#         self.core = core

#     def ask(self, message, history=None):
#         return self.core.chat(message, history=history or [],
#                               module="family",
#                               extra_system="You manage home, family schedules...")