"""
ODIN M3 — Comms / Control / Engineering / Info
C:\AI\MyOdin\M3\main.py

Port: 8005  (override via .env → M3_PORT)
.env: C:\AI\MyOdin\.env

STATUS: PLACEHOLDER — boots clean, dashboard live, all routes stubbed.
No external module dependencies. Drop real logic into the stubs when ready.

Comms note: old ODIN_PRO comms loaded from Z:\ODIN\ODIN_PRO\ — that path
is dead. Protocol managers (BT/BLE/MQTT/WiFi etc.) are stubbed here until
hardware is confirmed and packages installed on new Python 3.10.11 env.
"""

import os
import sys
import socket
from pathlib import Path

# ── .env (C:\AI\MyOdin\.env) ─────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(env_path, override=True)
except ImportError:
    pass  # dotenv not installed — fall back to os.getenv defaults

# ── Config ────────────────────────────────────────────────────────────────────
from settings import get_settings
settings = get_settings()

M3_PORT    = settings.port_comms
BRIDGE_URL = settings.bridge_url
BRIDGE_KEY = settings.odin_bridge_key
ODIN_VER   = settings.odin_version

# ── Port map (for engineering health checks) ──────────────────────────────────
PORT_MAP = {
    "brain":   settings.port_brain,
    "memory":  settings.port_memory,
    "core":    settings.port_core,
    "face":    settings.port_face,
    "comms":   settings.port_comms,
    "eng_hub": settings.port_engineering,
    "hunter":  settings.port_hunter,
    "mobile":  settings.port_mobile,
    "bridge":  settings.port_bridge,
}

# ── FastAPI ───────────────────────────────────────────────────────────────────
try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("ERROR: fastapi or uvicorn not installed.")
    print("  pip install fastapi uvicorn")
    sys.exit(1)

app = FastAPI(
    title="ODIN M3",
    description="Comms · Control · Engineering · Info",
    version=ODIN_VER
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>ODIN M3 — Systems Core</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#080808;color:#c9a84c;font-family:'Share Tech Mono',monospace;
         display:flex;flex-direction:column;align-items:center;justify-content:center;
         min-height:100vh;gap:1.2rem;padding:2rem}
    h1{font-family:'Bebas Neue',sans-serif;font-size:3.5rem;letter-spacing:0.5em;
       text-shadow:0 0 20px rgba(201,168,76,0.4)}
    .online{color:#4caf50;font-size:0.65rem;letter-spacing:0.4em}
    .sub{color:#555;font-size:0.65rem;letter-spacing:0.35em}
    .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;
          margin-top:1.5rem;width:100%;max-width:700px}
    .card{border:1px solid #1a1a1a;padding:1rem;text-align:center;
          background:#0d0d0d;border-radius:2px}
    .card h3{font-family:'Bebas Neue',sans-serif;font-size:1.1rem;
             letter-spacing:0.3em;color:#c9a84c;margin-bottom:0.4rem}
    .card p{font-size:0.55rem;color:#444;letter-spacing:0.2em}
    .stub{color:#333;font-size:0.5rem;letter-spacing:0.2em;margin-top:0.3rem}
  </style>
</head>
<body>
  <h1>M3 — CORE</h1>
  <div class="online">&#9679; ONLINE</div>
  <div class="sub">ENG &nbsp;&middot;&nbsp; COMMS &nbsp;&middot;&nbsp; CONTROL &nbsp;&middot;&nbsp; INFO</div>
  <div class="grid">
    <div class="card"><h3>COMMS</h3><p>BT &middot; BLE &middot; WiFi &middot; MQTT</p><div class="stub">STUBBED</div></div>
    <div class="card"><h3>CONTROL</h3><p>Modules &middot; Kill &middot; Restart</p><div class="stub">STUBBED</div></div>
    <div class="card"><h3>ENGINEERING</h3><p>Diagnostics &middot; Ports</p><div class="stub">ACTIVE</div></div>
    <div class="card"><h3>INFO</h3><p>Status &middot; Docs &middot; Context</p><div class="stub">STUBBED</div></div>
  </div>
  <div class="sub" style="margin-top:1.5rem">READY FOR EXPANSION</div>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    custom = Path(__file__).resolve().parent / "static" / "index.html"
    if custom.exists():
        return HTMLResponse(content=custom.read_text(encoding="utf-8"))
    return HTMLResponse(content=DASHBOARD_HTML)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":   "online",
        "module":   "M3",
        "port":     M3_PORT,
        "version":  ODIN_VER,
        "services": ["comms", "control", "engineering", "info"],
        "active":   ["engineering"],
        "note":     "placeholder"
    }

@app.get("/api/status")
async def api_status():
    return {
        "comms":       "stubbed",
        "control":     "stubbed",
        "engineering": "active",
        "info":        "stubbed",
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMMS
# Old path Z:\ODIN\ODIN_PRO\ is dead — do not import from there.
# Packages to reinstall under Python 3.10.11: bleak, paho-mqtt, zeroconf
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/comms/status")
async def comms_status():
    return {
        "service":   "comms",
        "status":    "stubbed",
        "protocols": [],
        # TODO: init bt, ble, wifi, mqtt managers
    }

@app.post("/comms/send")
async def comms_send(request: Request):
    body = await request.json()
    # TODO: route body["channel"] -> email / SMS / webhook / MQTT
    return {"received": body, "sent": False}

@app.post("/comms/notify")
async def comms_notify(request: Request):
    body = await request.json()
    # TODO: push to dashboard or mobile
    return {"received": body, "delivered": False}


# ─────────────────────────────────────────────────────────────────────────────
# CONTROL
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_MODULES = ["m1", "m2", "m3", "m4", "bridge", "n8n"]

@app.get("/control/status")
async def control_status():
    return {"service": "control", "status": "stubbed"}

@app.post("/control/restart/{module}")
async def control_restart(module: str):
    if module.lower() not in KNOWN_MODULES:
        return JSONResponse({"error": f"unknown module: {module}"}, status_code=400)
    # TODO: map module -> start script -> subprocess restart
    return {"module": module, "action": "restart", "executed": False}

@app.post("/control/kill/{module}")
async def control_kill(module: str):
    if module.lower() not in KNOWN_MODULES:
        return JSONResponse({"error": f"unknown module: {module}"}, status_code=400)
    # TODO: graceful shutdown
    return {"module": module, "action": "kill", "executed": False}


# ─────────────────────────────────────────────────────────────────────────────
# ENGINEERING  (only section with live logic)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/engineering/status")
async def engineering_status():
    return {"service": "engineering", "status": "active"}

@app.get("/engineering/ports")
async def engineering_ports():
    """Live socket check — tells you which ODIN ports are actually up."""
    results = {}
    for name, port in PORT_MAP.items():
        try:
            s = socket.create_connection(("localhost", port), timeout=0.5)
            s.close()
            results[name] = {"port": port, "status": "open"}
        except OSError:
            results[name] = {"port": port, "status": "closed"}
    return results

@app.get("/engineering/env")
async def engineering_env():
    safe = ["BRIDGE_URL", "M3_PORT", "ODIN_VERSION"]
    return {k: os.getenv(k, "not set") for k in safe}


# ─────────────────────────────────────────────────────────────────────────────
# INFO
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/info/status")
async def info_status():
    return {"service": "info", "status": "stubbed"}

@app.get("/info/modules")
async def info_modules():
    return {
        "M1":     {"role": "Brain / Memory",              "ports": [8000, 8001]},
        "M2":     {"role": "Senses / Vision / Face",      "ports": [8010, 8015, 8003]},
        "M3":     {"role": "Comms / Control / Eng / Info", "ports": [8005, 8006, 8007, 8008]},
        "P1":     {"role": "Hunter",                       "ports": [8030]},
        "P2":     {"role": "Mobile",                       "ports": [8040]},
        "Bridge": {"role": "Gateway",                      "ports": [8099]},
    }

@app.get("/info/portmap")
async def info_portmap():
    return PORT_MAP


# ─────────────────────────────────────────────────────────────────────────────
# BOOT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"""
+--------------------------------------+
|  ODIN M3 -- SYSTEMS CORE             |
|  Comms . Control . Eng . Info       |
|  Port  : {M3_PORT}                        |
|  .env  : C:\\AI\\MyOdin\\.env           |
+--------------------------------------+
""")
    uvicorn.run(
        "main_comms:app",
        host="0.0.0.0",
        port=M3_PORT,
        reload=False,
        log_level="info"
    )