"""ODIN-Hunter | Auto Submitter"""
import os
class AutoSubmitter:
    def __init__(self): self.enabled = os.getenv("HUNTER_AUTO_SUBMIT","false").lower()=="true"
    async def submit(self, platform_mgr, platform, program_id, report):
        if not self.enabled: return {"status": "auto_submit_disabled"}
        return await platform_mgr.submit_report(platform, program_id, report)
