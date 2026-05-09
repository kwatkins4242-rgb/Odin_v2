"""
ODIN-Hunter | IDOR Tester
Tests for Insecure Direct Object Reference vulnerabilities
"""
import aiohttp
import asyncio
import re

class IDORTester:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def test(self, target: str, endpoints: list) -> list:
        findings = []
        base_url = f"https://{target}"

        # Find endpoints with IDs
        id_endpoints = [ep for ep in endpoints if re.search(r'/\d+|/[a-f0-9-]{36}', ep.get("path", ""))]

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for ep in id_endpoints[:15]:
                path = ep.get("path", "")
                result = await self._test_idor(session, base_url, path, target)
                if result:
                    findings.append(result)

            # Test predictable IDs on common API patterns
            api_patterns = ["/api/users/{id}", "/api/accounts/{id}", "/api/orders/{id}",
                           "/api/invoices/{id}", "/api/documents/{id}"]
            for pattern in api_patterns:
                for test_id in [1, 2, 3, 100, 1000]:
                    url = f"{base_url}{pattern.replace('{id}', str(test_id))}"
                    result = await self._check_accessible(session, url, target, str(test_id))
                    if result:
                        findings.append(result)

        return findings

    async def _test_idor(self, session, base_url: str, path: str, target: str) -> dict:
        """Test numeric IDs by incrementing/decrementing"""
        match = re.search(r'/(\d+)', path)
        if not match:
            return None

        original_id = int(match.group(1))
        test_ids = [original_id - 1, original_id + 1, original_id + 100, 1, 2, 3]

        original_url = f"{base_url}{path}"
        try:
            async with session.get(original_url, ssl=False) as orig_resp:
                if orig_resp.status != 200:
                    return None
                orig_body = await orig_resp.text(errors="ignore")
                orig_len = len(orig_body)

            for test_id in test_ids:
                new_path = re.sub(r'/\d+', f'/{test_id}', path, count=1)
                test_url = f"{base_url}{new_path}"
                async with session.get(test_url, ssl=False) as test_resp:
                    if test_resp.status == 200:
                        test_body = await test_resp.text(errors="ignore")
                        # Different content = different object = IDOR
                        if len(test_body) != orig_len and len(test_body) > 50:
                            return {
                                "target": target,
                                "type": "idor",
                                "title": "Insecure Direct Object Reference (IDOR)",
                                "severity": "high",
                                "description": f"IDOR at {path} — accessing ID {test_id} returns different user data",
                                "proof": {
                                    "original_url": original_url,
                                    "test_url": test_url,
                                    "original_id": original_id,
                                    "accessed_id": test_id
                                },
                                "confidence": 0.70,
                                "remediation": "Verify authorization on every object access — check user owns resource"
                            }
        except Exception:
            pass
        return None

    async def _check_accessible(self, session, url: str, target: str, test_id: str) -> dict:
        """Check if an API endpoint returns data without auth"""
        try:
            async with session.get(url, ssl=False) as resp:
                if resp.status == 200:
                    body = await resp.text(errors="ignore")
                    if len(body) > 20 and "{" in body:
                        return {
                            "target": target,
                            "type": "idor",
                            "title": "Unauthenticated API Object Access",
                            "severity": "high",
                            "description": f"API returns data for ID {test_id} without authentication: {url}",
                            "proof": {"url": url, "status": 200, "response_snippet": body[:200]},
                            "confidence": 0.65,
                            "remediation": "Require authentication on all API endpoints"
                        }
        except Exception:
            pass
        return None
