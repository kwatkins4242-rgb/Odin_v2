"""ODIN-Hunter | CVE Matcher"""
import aiohttp, asyncio

class CVEMatcher:
    async def match(self, tech_stack: dict) -> list:
        findings = []
        for tech, info in tech_stack.items():
            findings.append({"tech": tech, "note": f"Check NVD for known CVEs in {tech}"})
        return findings
