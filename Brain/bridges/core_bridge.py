"""
ODIN-Hunter → odin-core bridge
Reports findings, logs activity, sends commands back to ODIN
"""

import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CORE_URL = os.getenv("ODIN_CORE_URL", "http://localhost:8000")

class CoreBridge:
    def __init__(self):
        self.base_url = CORE_URL
        self.client = httpx.AsyncClient(timeout=10.0)

    async def announce(self, message: str):
        """Tell odin-core Hunter is online"""
        try:
            await self.client.post(f"{self.base_url}/api/chat", json={
                "message": f"[ODIN-Hunter] {message}",
                "source": "odin-hunter",
                "type": "system"
            })
        except Exception as e:
            print(f"[CoreBridge] announce failed: {e}")

    async def log(self, message: str, level: str = "info"):
        """Send log entry to odin-core"""
        try:
            await self.client.post(f"{self.base_url}/api/log", json={
                "source": "odin-hunter",
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[CoreBridge] log failed: {e}")

    async def report_finding(self, finding: dict):
        """Push a vulnerability finding to odin-core"""
        try:
            response = await self.client.post(f"{self.base_url}/api/hunter/finding", json={
                "source": "odin-hunter",
                "finding": finding,
                "timestamp": datetime.now().isoformat()
            })
            return response.json()
        except Exception as e:
            print(f"[CoreBridge] report_finding failed: {e}")
            return {"error": str(e)}

    async def report_payout(self, payout: dict):
        """Notify odin-core of a payout received"""
        try:
            response = await self.client.post(f"{self.base_url}/api/hunter/payout", json={
                "source": "odin-hunter",
                "payout": payout,
                "timestamp": datetime.now().isoformat()
            })
            return response.json()
        except Exception as e:
            print(f"[CoreBridge] report_payout failed: {e}")
            return {"error": str(e)}

    async def ask_odin(self, question: str) -> str:
        """Ask odin-core/Claude a question during hunting"""
        try:
            response = await self.client.post(f"{self.base_url}/api/chat", json={
                "message": question,
                "source": "odin-hunter"
            })
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            print(f"[CoreBridge] ask_odin failed: {e}")
            return ""

    async def get_status(self) -> dict:
        """Check if odin-core is alive"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception:
            return {"status": "offline"}
