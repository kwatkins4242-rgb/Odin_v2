# agents/engineer_agent.py
"""
ODIN Engineer Agent
Client for odin-engineer (vehicle diagnostics, OBD, faults).
"""

import os
import requests
from typing import Dict, Any, List

ENGINEER_URL = os.getenv("ENGINEER_URL", "http://localhost:8025")
TIMEOUT      = 3

class EngineerAgent:
    def __init__(self, base_url: str = None):
        self.base = base_url or f"{ENGINEER_URL}/engineer"

    def faults(self, active_only: bool = True) -> List[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.base}/faults?active_only={active_only}", timeout=TIMEOUT)
            return r.json().get("faults", []) if r.status_code == 200 else []
        except:
            return []

    def clear_fault(self, code: str) -> bool:
        try:
            r = requests.post(f"{self.base}/clear_fault", json={"code": code}, timeout=TIMEOUT)
            return r.status_code == 200
        except:
            return False

    def live_data(self, pid: str = None) -> Dict[str, Any]:
        try:
            url = f"{self.base}/live"
            if pid:
                url += f"?pid={pid}"
            r = requests.get(url, timeout=TIMEOUT)
            return r.json() if r.status_code == 200 else {}
        except:
            return [] # This was returning {} in some places, but let's be consistent or follow original

    def is_online(self) -> bool:
        try:
            r = requests.get(ENGINEER_URL + "/health", timeout=2)
            return r.status_code == 200
        except:
            return False
