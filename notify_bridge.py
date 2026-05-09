"""
ODIN-Hunter → odin-face notification bridge
Pushes real-time alerts to your dashboard
"""

import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FACE_URL = os.getenv("ODIN_FACE_URL", "http://localhost:5000")
CORE_URL = os.getenv("ODIN_CORE_URL", "http://localhost:8000")

class NotifyBridge:
    def __init__(self):
        self.face_url = FACE_URL
        self.core_url = CORE_URL
        self.client = httpx.AsyncClient(timeout=5.0)
        self.notify_on_find   = os.getenv("NOTIFY_ON_FIND", "true").lower() == "true"
        self.notify_on_submit = os.getenv("NOTIFY_ON_SUBMIT", "true").lower() == "true"
        self.notify_on_payout = os.getenv("NOTIFY_ON_PAYOUT", "true").lower() == "true"

    async def send(self, message: str, level: str = "info", data: dict = None):
        """Send notification to odin-face"""
        payload = {
            "source": "odin-hunter",
            "message": message,
            "level": level,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        # Try odin-face first, fall back to odin-core
        for url in [f"{self.face_url}/api/notify", f"{self.core_url}/api/notify"]:
            try:
                await self.client.post(url, json=payload)
                return
            except Exception:
                continue
        print(f"[NotifyBridge] {level.upper()}: {message}")

    async def finding_found(self, finding: dict):
        if not self.notify_on_find:
            return
        severity = finding.get("severity", "unknown").upper()
        title = finding.get("title", "Unknown finding")
        target = finding.get("target", "")
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
        await self.send(
            f"{emoji} [{severity}] {title} on {target}",
            level="warning" if severity in ["CRITICAL", "HIGH"] else "info",
            data=finding
        )

    async def report_submitted(self, submission: dict):
        if not self.notify_on_submit:
            return
        await self.send(
            f"📤 Report submitted to {submission.get('platform')}: {submission.get('title')}",
            level="success",
            data=submission
        )

    async def payout_received(self, payout: dict):
        if not self.notify_on_payout:
            return
        amount = payout.get("amount", 0)
        await self.send(
            f"💰 PAYOUT RECEIVED: ${amount:.2f} from {payout.get('platform')}!",
            level="success",
            data=payout
        )

    async def hunt_complete(self, target: str, finding_count: int):
        await self.send(
            f"✅ Hunt complete on {target} — {finding_count} findings",
            level="info"
        )

    async def error(self, message: str):
        await self.send(f"❌ Error: {message}", level="error")
