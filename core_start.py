"""
CORE — start.py
File: C:\AI\MyOdin\M1\core\start.py

This is what the master launcher calls.
It just boots uvicorn with main:app
"""

import sys
import os

# Make sure imports resolve from this folder
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn

if __name__ == "__main__":
    print("[core] Booting on port 8050...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8050,
        reload=False,        # set True if you want hot-reload during dev
        log_level="info",
    )
