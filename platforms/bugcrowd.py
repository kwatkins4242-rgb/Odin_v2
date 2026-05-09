"""
ODIN-Hunter | Bugcrowd Integration
"""

import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

BC_BASE = "https://api.bugcrowd.com"

class Bugcrowd:
    def __init__(self):
        self.token = os.getenv("BUGCROWD_API_TOKEN", "")
        if not self.token:
            raise ValueError("Bugcrowd token not configured")
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Accept": "application/vnd.bugcrowd.v4+json",
            "Content-Type": "application/json"
        }
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def get_programs(self) -> list:
        programs = []
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(f"{BC_BASE}/programs") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for prog in data.get("data", []):
                            attrs = prog.get("attributes", {})
                            programs.append({
                                "id": prog.get("id"),
                                "name": attrs.get("name"),
                                "code": attrs.get("code"),
                                "status": attrs.get("status"),
                                "offers_bounties": attrs.get("offers_bounties"),
                                "platform": "bugcrowd"
                            })
        except Exception as e:
            print(f"[Bugcrowd] get_programs error: {e}")
        return programs

    async def get_scope(self, program_code: str) -> list:
        scope = []
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(f"{BC_BASE}/programs/{program_code}/scope_groups") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for group in data.get("data", []):
                            for target in group.get("attributes", {}).get("targets", []):
                                if target.get("in_scope"):
                                    scope.append({
                                        "value": target.get("target"),
                                        "type": target.get("target_type", "url").lower()
                                    })
        except Exception as e:
            print(f"[Bugcrowd] get_scope error: {e}")
        return scope

    async def submit_report(self, program_code: str, report: dict) -> dict:
        try:
            payload = {
                "data": {
                    "type": "submission",
                    "attributes": {
                        "title": report.get("title"),
                        "description": report.get("body"),
                        "severity": report.get("severity", "P3"),
                        "target": report.get("target", "")
                    }
                }
            }
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.post(f"{BC_BASE}/submissions", json=payload) as resp:
                    data = await resp.json()
                    if resp.status in [200, 201]:
                        return {"success": True, "submission_id": data.get("data", {}).get("id"), "platform": "bugcrowd"}
                    return {"success": False, "error": str(data)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_report_status(self, submission_id: str) -> dict:
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(f"{BC_BASE}/submissions/{submission_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        attrs = data.get("data", {}).get("attributes", {})
                        return {
                            "submission_id": submission_id,
                            "state": attrs.get("state"),
                            "payout": attrs.get("payout", 0),
                            "platform": "bugcrowd"
                        }
        except Exception as e:
            return {"error": str(e)}
