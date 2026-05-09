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

app = FastAPI(title="ODIN M3 — Info")

@app.get("/health")
async def health():
    return {
        "status": "online",
        "module": "M3-Info",
        "port": settings.port_info
    }

if __name__ == "__main__":
    print(f"[INFO] Starting ODIN Info on port {settings.port_info}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.port_info, log_level="warning")
