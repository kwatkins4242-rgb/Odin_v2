
"""
ODIN — n8n Agent Bridge
========================
Relays local events and memory updates to the n8n automation engine.
"""

import sys
import os
import time
import requests
import logging
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
import uvicorn

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("odin.n8n_agent")

app = FastAPI(title="ODIN — n8n Agent Bridge")

N8N_WEBHOOK_URL = f"http://localhost:{settings.port_n8n}/webhook/odin-memory"

@app.get("/health")
async def health():
    return {"status": "online", "n8n_target": N8N_WEBHOOK_URL}

@app.post("/trigger")
async def trigger_n8n(data: dict, background_tasks: BackgroundTasks):
    """Bridge an event to n8n."""
    log.info(f"Relaying event to n8n: {data.get('action', 'unknown')}")
    
    def send_to_n8n():
        try:
            r = requests.post(
                N8N_WEBHOOK_URL,
                json=data,
                headers={"x-api-key": settings.odin_bridge_key},
                timeout=10
            )
            log.info(f"n8n response: {r.status_code}")
        except Exception as e:
            log.error(f"Failed to reach n8n: {e}")

    background_tasks.add_task(send_to_n8n)
    return {"status": "relaying"}

if __name__ == "__main__":
    log.info(f"Starting n8n Agent Bridge on port {settings.port_n8n_agent}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.port_n8n_agent, log_level="warning")
