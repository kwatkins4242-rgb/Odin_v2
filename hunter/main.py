"""
Hunter — lightweight watchdog (health pings). Port :8500.
"""

import asyncio
import logging
import sys
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings

settings = get_settings()
log = logging.getLogger("hunter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TARGETS = [
    ("brain", f"http://127.0.0.1:{settings.port_brain}/health"),
    ("memory", f"http://127.0.0.1:{settings.port_memory}/health"),
    ("sense", f"http://127.0.0.1:{settings.port_sense}/health"),
    ("bridge", f"http://127.0.0.1:{settings.port_bridge}/health"),
]

app = FastAPI(title="Hunter", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "hunter"}


@app.get("/api/status/all")
async def status_all():
    out = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in TARGETS:
            try:
                r = await client.get(url)
                out[name] = {"ok": r.status_code < 500, "code": r.status_code}
            except Exception as e:
                out[name] = {"ok": False, "error": str(e)}
    return out


async def _watch_loop():
    while True:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, url in TARGETS:
                try:
                    r = await client.get(url)
                    if r.status_code >= 500:
                        log.warning("%s unhealthy HTTP %s", name, r.status_code)
                except Exception as e:
                    log.warning("%s unreachable: %s", name, e)
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup():
    asyncio.create_task(_watch_loop())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.port_hunter, log_level="info")
