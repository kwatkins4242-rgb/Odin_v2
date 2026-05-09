import sys
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

app = FastAPI(title="ODIN — Agent Tom")

@app.get("/health")
async def health():
    return {
        "status": "online",
        "module": "Agent-Tom",
        "port": settings.port_agent_tom,
        "mode": "Active Stub"
    }

if __name__ == "__main__":
    print(f"[TOM] Starting ODIN Agent Tom (Static) on port {settings.port_n8n_agent}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.port_n8n_agent, log_level="warning")
