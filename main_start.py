import sys
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

app = FastAPI(title="ODIN M3 — Control")

@app.get("/health")
async def health():
    return {
        "status": "online",
        "module": "M3-Control",
        "port": settings.port_control
    }

if __name__ == "__main__":
    print(f"[CTRL] Starting ODIN Control on port {settings.port_control}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.port_control, log_level="warning")
