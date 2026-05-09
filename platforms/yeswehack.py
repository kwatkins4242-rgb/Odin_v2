"""ODIN-Hunter | YesWeHack Integration"""
import os
class YesWeHack:
    def __init__(self):
        self.email = os.getenv("YESWEHACK_EMAIL", "")
    async def get_programs(self): return []
    async def get_scope(self, program_id): return []
    async def submit_report(self, program_id, report): return {"error": "Not implemented"}
    async def get_report_status(self, report_id): return {}
