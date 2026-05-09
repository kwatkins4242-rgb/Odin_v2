"""
ODIN-Hunter | HackerOne Integration
HackerOne API v1
"""

import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

H1_BASE = "https://api.hackerone.com/v1"

class HackerOne:
    def __init__(self):
        self.token = os.getenv("HACKERONE_API_TOKEN", "")
        self.username = os.getenv("HACKERONE_USERNAME", "")
        if not self.token or not self.username:
            raise ValueError("HackerOne credentials not configured")
        self.auth = aiohttp.BasicAuth(self.username, self.token)
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def get_programs(self) -> list:
        """Get list of bug bounty programs"""
        programs = []
        try:
            async with aiohttp.ClientSession(auth=self.auth, timeout=self.timeout) as session:
                url = f"{H1_BASE}/hackers/programs?page[size]=100"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for prog in data.get("data", []):
                            attrs = prog.get("attributes", {})
                            programs.append({
                                "id": prog.get("id"),
                                "handle": attrs.get("handle"),
                                "name": attrs.get("name"),
                                "submission_state": attrs.get("submission_state"),
                                "offers_bounties": attrs.get("offers_bounties"),
                                "platform": "hackerone"
                            })
        except Exception as e:
            print(f"[HackerOne] get_programs error: {e}")
        return programs

    async def get_scope(self, program_handle: str) -> list:
        """Get in-scope targets for a program"""
        scope = []
        try:
            async with aiohttp.ClientSession(auth=self.auth, timeout=self.timeout) as session:
                url = f"{H1_BASE}/programs/{program_handle}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        relationships = data.get("data", {}).get("relationships", {})
                        structured_scope = relationships.get("structured_scope", {}).get("data", [])
                        for item in structured_scope:
                            attrs = item.get("attributes", {})
                            if attrs.get("eligible_for_submission") and not attrs.get("eligible_for_bounty") == False:
                                scope.append({
                                    "value": attrs.get("asset_identifier"),
                                    "type": attrs.get("asset_type", "url").lower(),
                                    "max_severity": attrs.get("max_severity")
                                })
        except Exception as e:
            print(f"[HackerOne] get_scope error: {e}")
        return scope

    async def submit_report(self, program_handle: str, report: dict) -> dict:
        """Submit a vulnerability report"""
        try:
            payload = {
                "data": {
                    "type": "report",
                    "attributes": {
                        "team_handle": program_handle,
                        "title": report.get("title"),
                        "vulnerability_information": report.get("body"),
                        "severity_rating": report.get("severity", "medium"),
                        "impact": report.get("impact", ""),
                    }
                }
            }
            async with aiohttp.ClientSession(auth=self.auth, timeout=self.timeout) as session:
                async with session.post(f"{H1_BASE}/reports", json=payload) as resp:
                    data = await resp.json()
                    if resp.status == 201:
                        report_id = data.get("data", {}).get("id")
                        print(f"[HackerOne] ✅ Report submitted: #{report_id}")
                        return {"success": True, "report_id": report_id, "platform": "hackerone"}
                    else:
                        return {"success": False, "error": str(data), "platform": "hackerone"}
        except Exception as e:
            print(f"[HackerOne] submit_report error: {e}")
            return {"success": False, "error": str(e)}

    async def get_report_status(self, report_id: str) -> dict:
        """Check status of a submitted report"""
        try:
            async with aiohttp.ClientSession(auth=self.auth, timeout=self.timeout) as session:
                async with session.get(f"{H1_BASE}/reports/{report_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        attrs = data.get("data", {}).get("attributes", {})
                        return {
                            "report_id": report_id,
                            "state": attrs.get("state"),
                            "bounty_amount": attrs.get("bounty_amount"),
                            "platform": "hackerone"
                        }
        except Exception as e:
            return {"error": str(e)}

    async def get_my_reports(self) -> list:
        """Get all reports submitted by this user"""
        reports = []
        try:
            async with aiohttp.ClientSession(auth=self.auth, timeout=self.timeout) as session:
                url = f"{H1_BASE}/reports?filter[reporter]={self.username}&page[size]=100"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for r in data.get("data", []):
                            attrs = r.get("attributes", {})
                            reports.append({
                                "id": r.get("id"),
                                "title": attrs.get("title"),
                                "state": attrs.get("state"),
                                "created_at": attrs.get("created_at"),
                                "bounty": attrs.get("bounty_amount", 0),
                                "platform": "hackerone"
                            })
        except Exception as e:
            print(f"[HackerOne] get_my_reports error: {e}")
        return reports
