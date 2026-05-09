"""
ODIN Dashboards — Multi-Port Server
==================================
Launches:
1. Master HUB Dashboard (Port 8080)
2. API Provider HUD (Port 9050)
3. Chatface Portal (Port 5000)
4. Sovereign Dashboard (Port 7080)
"""

import uvicorn
import multiprocessing
import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

# --- Paths ---
DASH_DIR = Path(__file__).resolve().parent
ROOT = DASH_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

STATIC_DIR = DASH_DIR / "static"
SUB_STATIC_DIR = STATIC_DIR / "static" # dashboards/static/static

# --- Utility: Proxy Logic ---
async def proxy_request(request: Request, port: int, path: str):
    try:
        url = f"http://localhost:{port}/{path}"
        method = request.method
        content = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method, url, content=content, headers=headers,
                params=request.query_params
            )
            data = resp.json() if "json" in resp.headers.get("content-type", "") else resp.text
            return JSONResponse(content=data, status_code=resp.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# --- 1. Master HUB Dashboard (8080) ---
app8080 = FastAPI(title="ODIN Master Hub")

@app8080.get("/", response_class=HTMLResponse)
async def hub_root():
    # Priority: Latest IDE index3.html, then standard index.html
    search_paths = [
        STATIC_DIR / "STARTUP.html",
        SUB_STATIC_DIR / "storage" / "index3.html",
        STATIC_DIR / "index.html"
    ]
    for p in search_paths:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return HTMLResponse("No dashboard entry point found in static/.", status_code=404)

# Common Proxies
@app8080.post("/chat")
async def hub_chat(request: Request): return await proxy_request(request, settings.port_brain, "chat")

@app8080.get("/health")
async def hub_health(): return await proxy_request(request=None, port=settings.port_brain, path="health")

# Mount everything for asset resolution
app8080.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static_assets")
app8080.mount("/", StaticFiles(directory=str(STATIC_DIR)), name="static_root")

# --- 2. API Monitor (9050) ---
app9050 = FastAPI(title="ODIN API Monitor")
@app9050.get("/", response_class=HTMLResponse)
async def api_hud():
    p = STATIC_DIR / "Chat" / "6_API.html"
    if p.exists(): return p.read_text(encoding="utf-8")
    return HTMLResponse("API HUD not found.", status_code=404)

# --- 3. Chatface Portal (5000) ---
app5000 = FastAPI(title="ODIN Chatface Portal")
PORTAL_DIR = SUB_STATIC_DIR / "add to 5000"

@app5000.get("/", response_class=HTMLResponse)
async def portal_root():
    p = PORTAL_DIR / "index.html"
    if p.exists(): return p.read_text(encoding="utf-8")
    return HTMLResponse("Portal index.html not found in add to 5000/.", status_code=404)

app5000.mount("/", StaticFiles(directory=str(PORTAL_DIR)), name="portal")

# --- 4. Sovereign Dashboard (7080) ---
app7080 = FastAPI(title="ODIN Sovereign Dashboard")
SOVEREIGN_DIR = SUB_STATIC_DIR / "add to 7080"

@app7080.get("/", response_class=HTMLResponse)
async def sovereign_root():
    p = SOVEREIGN_DIR / "index.html"
    if p.exists(): return p.read_text(encoding="utf-8")
    return HTMLResponse("Sovereign index.html not found in add to 7080/.", status_code=404)

app7080.mount("/", StaticFiles(directory=str(SOVEREIGN_DIR)), name="sovereign")

# --- Server Runners ---
def run_8080(): uvicorn.run(app8080, host="0.0.0.0", port=8080, log_level="warning")
def run_9050(): uvicorn.run(app9050, host="0.0.0.0", port=9050, log_level="warning")
def run_5000(): uvicorn.run(app5000, host="0.0.0.0", port=5000, log_level="warning")
def run_7080(): uvicorn.run(app7080, host="0.0.0.0", port=7080, log_level="warning")

if __name__ == "__main__":
    print(f"Launching ODIN Dashboards (8080, 9050, 5000, 7080)...")
    processes = [
        multiprocessing.Process(target=run_8080),
        multiprocessing.Process(target=run_9050),
        multiprocessing.Process(target=run_5000),
        multiprocessing.Process(target=run_7080)
    ]
    for p in processes: p.start()
    try:
        for p in processes: p.join()
    except KeyboardInterrupt:
        for p in processes: p.terminate()
