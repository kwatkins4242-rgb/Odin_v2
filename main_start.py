
import sys
import os
import base64
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from openai import OpenAI

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

# Import shared utils
import utils.vision_utils as vision_utils

app = FastAPI(title="ODIN M2 — Vision")

# Logs directory for screenshots
LOG_DIR = Path(__file__).resolve().parent / "logs"

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
        <head>
            <title>ODIN M2 — VISION</title>
            <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&display=swap" rel="stylesheet">
            <style>
                body { background:#0a0a0a; color:#4dd0e1; font-family:'Share Tech Mono',monospace; margin:0; display:flex; flex-direction:column; height:100vh; }
                .header { padding:2rem; border-bottom:1px solid rgba(77,208,225,0.1); display:flex; justify-content:space-between; align-items:center; }
                .logo { font-family:'Bebas Neue',sans-serif; font-size:2.5rem; letter-spacing:0.4em; }
                .main { flex:1; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:1rem; }
                .btn { background:transparent; border:1px solid #4dd0e1; color:#4dd0e1; padding:10px 20px; cursor:pointer; font-family:inherit; letter-spacing:0.2em; }
                .btn:hover { background:rgba(77,208,225,0.1); }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">ODIN // M2 VISION</div>
                <div style="font-size:0.7rem; color:#4caf50;">VISUAL LINK ACTIVE</div>
            </div>
            <div class="main">
                <button class="btn" onclick="capture()">MANUAL CAPTURE</button>
                <div id="status" style="margin-top:20px; color:#555;">Ready.</div>
            </div>
            <script>
                async function capture() {
                    document.getElementById('status').innerText = 'Capturing...';
                    const r = await fetch('/capture');
                    const d = await r.json();
                    document.getElementById('status').innerText = 'Saved: ' + d.path;
                }
            </script>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    return {
        "status": "online",
        "module": "M2-Vision",
        "port": settings.port_vision
    }

@app.get("/capture")
async def capture():
    path = vision_utils.capture_screen(LOG_DIR, resize_to=settings.tom_max_screen_width)
    return {"status": "success", "path": path}

@app.post("/analyze")
async def analyze(goal: str = "Describe what is on the screen"):
    """Capture a screenshot and analyze it with GPT-4o-mini."""
    path = vision_utils.capture_screen(LOG_DIR, resize_to=settings.tom_max_screen_width)
    
    # 1. Encode
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 2. Call OpenAI (using root settings)
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": goal},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]}
            ],
            max_tokens=300
        )
        return {"status": "success", "analysis": response.choices[0].message.content, "path": path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print(f"[VISION] Starting ODIN Vision on port {settings.port_vision}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.port_vision, log_level="warning")
