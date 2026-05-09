"""
ODIN-Hunter | Platform Manager
Coordinates HackerOne, Bugcrowd, Intigriti, YesWeHack
"""

import os
from dotenv import load_dotenv

load_dotenv()

class PlatformManager:
    def __init__(self):
        from platforms.hackerone import HackerOne
        from platforms.bugcrowd import Bugcrowd
        self.platforms = {}
        try:
            self.platforms["hackerone"] = HackerOne()
        except Exception as e:
            print(f"[PlatformManager] HackerOne init failed: {e}")
        try:
            self.platforms["bugcrowd"] = Bugcrowd()
        except Exception as e:
            print(f"[PlatformManager] Bugcrowd init failed: {e}")

    async def get_connected_platforms(self) -> list:
        return list(self.platforms.keys())

    async def get_all_programs(self) -> dict:
        all_programs = {}
        for name, platform in self.platforms.items():
            try:
                programs = await platform.get_programs()
                all_programs[name] = programs
            except Exception as e:
                all_programs[name] = {"error": str(e)}
        return all_programs

    async def get_programs(self, platform_name: str) -> list:
        platform = self.platforms.get(platform_name)
        if not platform:
            return []
        return await platform.get_programs()

    async def get_scope(self, platform_name: str, program_id: str) -> list:
        platform = self.platforms.get(platform_name)
        if not platform:
            return []
        return await platform.get_scope(program_id)

    async def submit_report(self, platform_name: str, program_id: str, report: dict) -> dict:
        platform = self.platforms.get(platform_name)
        if not platform:
            return {"error": f"Platform {platform_name} not connected"}
        return await platform.submit_report(program_id, report)

    async def get_submission_status(self, platform_name: str, report_id: str) -> dict:
        platform = self.platforms.get(platform_name)
        if not platform:
            return {"error": "Platform not found"}
        return await platform.get_report_status(report_id)
