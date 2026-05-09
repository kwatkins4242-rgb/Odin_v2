"""
 — Core
==============
Location: C:\AI\MyOdin\M1\core\main.py
Port: 8050

Independent Core Processing Engine for ODIN.
"""

import sys
import logging
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

app = FastAPI(title="Core", version=settings.odin_version)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "online", "module": "core", "port": settings.port_core}

if __name__ == "__main__":
    print("\n" + "="*52)
    print("Core")
    print(f"  Port : {settings.port_core}")
    print("="*52 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=settings.port_core, log_level="warning")
