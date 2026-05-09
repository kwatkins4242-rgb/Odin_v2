"""
ODIN-Hunter → odin-memory bridge
Stores and retrieves findings, patterns, and intelligence
"""

import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MEMORY_URL = os.getenv("ODIN_MEMORY_URL", "http://localhost:8001")

class MemoryBridge:
    def __init__(self):
        self.base_url = MEMORY_URL
        self.client = httpx.AsyncClient(timeout=10.0)

    async def store_finding(self, finding_type: str, target: str, data: dict):
        """Store a finding in odin-memory"""
        try:
            memory_entry = {
                "type": "hunter_finding",
                "finding_type": finding_type,
                "target": target,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "tags": ["bug-bounty", finding_type, target]
            }
            response = await self.client.post(f"{self.base_url}/api/memory/store", json=memory_entry)
            return response.json()
        except Exception as e:
            print(f"[MemoryBridge] store_finding failed: {e}")
            return {"error": str(e)}

    async def get_past_findings(self, target: str) -> list:
        """Retrieve past findings for a target to avoid duplicates"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/memory/search",
                params={"query": f"hunter_finding {target}", "limit": 50}
            )
            return response.json().get("results", [])
        except Exception as e:
            print(f"[MemoryBridge] get_past_findings failed: {e}")
            return []

    async def store_recon(self, target: str, recon_data: dict):
        """Store recon data for future hunts"""
        try:
            await self.client.post(f"{self.base_url}/api/memory/store", json={
                "type": "hunter_recon",
                "target": target,
                "data": recon_data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[MemoryBridge] store_recon failed: {e}")

    async def get_patterns(self) -> list:
        """Get learned vulnerability patterns from memory"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/memory/search",
                params={"query": "hunter_pattern", "limit": 100}
            )
            return response.json().get("results", [])
        except Exception as e:
            print(f"[MemoryBridge] get_patterns failed: {e}")
            return []

    async def store_pattern(self, pattern: dict):
        """Store a successful pattern for future use"""
        try:
            await self.client.post(f"{self.base_url}/api/memory/store", json={
                "type": "hunter_pattern",
                "data": pattern,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[MemoryBridge] store_pattern failed: {e}")

    async def store_payout(self, payout_data: dict):
        """Store payout record in odin-memory"""
        try:
            await self.client.post(f"{self.base_url}/api/memory/store", json={
                "type": "hunter_payout",
                "data": payout_data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[MemoryBridge] store_payout failed: {e}")

    async def get_total_earnings(self) -> float:
        """Pull total earnings from memory"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/memory/search",
                params={"query": "hunter_payout", "limit": 1000}
            )
            payouts = response.json().get("results", [])
            total = sum(p.get("data", {}).get("amount", 0) for p in payouts)
            return total
        except Exception as e:
            print(f"[MemoryBridge] get_total_earnings failed: {e}")
            return 0.0
