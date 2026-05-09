"""
Hunter → odin-core bridge
Reports findings, logs activity, sends commands back to ODIN
Location: C:\\AI\MyOdin\\P1\\hunter\\integrations\\core_bridge.py
"""

import sys
import httpx
from pathlib import Path
from datetime import datetime

# ── Root on path ──────────────────────────────────────────────
HUNTER_DIR = Path(__file__).resolve().parent.parent
ODIN_ROOT  = HUNTER_DIR.parent
if str(ODIN_ROOT) not in sys.path:
    sys.path.insert(0, str(ODIN_ROOT))

from settings import get_settings
settings = get_settings()

CORE_URL = settings.core_url   # http://localhost:8000


class CoreBridge:
    def __init__(self):
        self.base_url = CORE_URL
        self.client   = httpx.AsyncClient(timeout=10.0)

    async def announce(self, message: str):
        try:
            await self.client.post(f"{self.base_url}/api/chat", json={
                "message": f"[ODIN-Hunter] {message}",
                "source":  "odin-hunter",
                "type":    "system"
            })
        except Exception as e:
            print(f"[CoreBridge] announce failed: {e}")

    async def log(self, message: str, level: str = "info"):
        try:
            await self.client.post(f"{self.base_url}/api/log", json={
                "source":    "odin-hunter",
                "level":     level,
                "message":   message,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[CoreBridge] log failed: {e}")

    async def report_finding(self, finding: dict):
        try:
            response = await self.client.post(f"{self.base_url}/api/hunter/finding", json={
                "source":    "odin-hunter",
                "finding":   finding,
                "timestamp": datetime.now().isoformat()
            })
            return response.json()
        except Exception as e:
            print(f"[CoreBridge] report_finding failed: {e}")
            return {"error": str(e)}

    async def report_payout(self, payout: dict):
        try:
            response = await self.client.post(f"{self.base_url}/api/hunter/payout", json={
                "source":    "odin-hunter",
                "payout":    payout,
                "timestamp": datetime.now().isoformat()
            })
            return response.json()
        except Exception as e:
            print(f"[CoreBridge] report_payout failed: {e}")
            return {"error": str(e)}

    async def ask_odin(self, question: str) -> str:
        try:
            response = await self.client.post(f"{self.base_url}/api/chat", json={
                "message": question,
                "source":  "odin-hunter"
            })
            data = response.json()
            return data.get("reply", "")
        except Exception as e:
            print(f"[CoreBridge] ask_odin failed: {e}")
            return ""

    async def get_status(self) -> dict:
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception:
            return {"status": "offline"}