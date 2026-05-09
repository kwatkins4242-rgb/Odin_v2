"""
ODIN — Static HUD Server
========================
Location: C:\\AI\\MyOdin\\dashboards\\server.py
Port: 8080  (separate from M1 on 8000)

Serves all HUDs from static/ and exposes /config for key injection.
LOCALHOST ONLY — never expose /config on a public server.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="ODIN HUD Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve everything in static/ at /static ────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── /config — exposes API keys to frontend HUDs ──────
@app.get("/config")
def get_config():
    """
    Expose config to frontend HUDs.
    LOCALHOST ONLY — never deploy this endpoint publicly.
    """
    return JSONResponse({
        "api_key":   os.getenv("OPENAI_API_KEY", ""),
        "gemini_key": os.getenv("GEMINI_API_KEY", ""),
        "model":     os.getenv("DEFAULT_MODEL", "gpt-4o"),
        "odin_endpoint": os.getenv("ODIN_ENDPOINT", "http://localhost:8000"),
    })


# ── Root: serve the launcher ──────────────────────────
@app.get("/", response_class=HTMLResponse)
def hub():
    path = os.path.join("static", "index.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h2>index.html not found in static/</h2>", status_code=404)


# ── /hud/{name} — serve any HUD by filename ──────────
@app.get("/hud/{hud_id}", response_class=HTMLResponse)
def serve_hud(hud_id: str):
    # Prevent path traversal
    if ".." in hud_id:
        return HTMLResponse("<h2>Invalid HUD name.</h2>", status_code=400)
    path = os.path.join("static", f"{hud_id}.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(f"<h2>HUD '{hud_id}' not found in static/</h2>", status_code=404)


# ── Siri API Integration ────────────────────────────
@app.post("/api/siri")
async def handle_siri(request: dict):
    """Endpoint for Siri Shortcut integration"""
    try:
        user_message = request.get("message", "")
        print(f"Siri Request: {user_message}")
        
        # Call the Bridge/Controller for thinking
        # For now, respond directly to confirm connection
        return JSONResponse({"reply": f"ODIN received your voice command: {user_message}. This is currently a test response."})
    except Exception as e:
        return JSONResponse({"reply": f"Error: {str(e)}"}, status_code=500)

@app.get("/api/siri/ping")
def siri_ping():
    return {"status": "online", "name": "Legacy AI", "message": "JARVIS is ready, sir."}


# ── Health ────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "online", "module": "HUD-Server", "port": 8080}


# ── Boot ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*48)
    print("  ODIN HUD Server")
    print("  Launcher : http://localhost:8080")
    print("  Config   : http://localhost:8080/config")
    print("  HUD      : http://localhost:8080/hud/<name>")
    print("="*48 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")