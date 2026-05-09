"""
ODIN-Hunter | Auth Tester
Tests authentication weaknesses
"""
import aiohttp
import asyncio

WEAK_CREDS = [
    ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
    ("admin", "admin123"), ("root", "root"), ("root", "password"),
    ("test", "test"), ("user", "user"), ("guest", "guest"),
    ("admin", ""), ("administrator", "administrator"),
]

class AuthTester:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def test(self, target: str, recon_data: dict) -> list:
        findings = []
        base_url = f"https://{target}"
        endpoints = recon_data.get("endpoints", [])

        # Find login endpoints
        login_endpoints = [
            ep for ep in endpoints
            if any(kw in ep.get("path", "").lower() for kw in
                   ["login", "signin", "auth", "admin", "wp-admin", "phpmyadmin"])
            and ep.get("status") in [200, 302, 301]
        ]

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Test default creds
            for ep in login_endpoints[:5]:
                path = ep.get("path", "")
                url = f"{base_url}{path}"
                result = await self._test_default_creds(session, url, target)
                if result:
                    findings.append(result)

            # Check for JWT issues
            jwt_result = await self._check_jwt_issues(session, base_url, target)
            if jwt_result:
                findings.append(jwt_result)

            # Check for missing auth on admin paths
            for admin_path in ["/admin", "/api/admin", "/dashboard", "/api/users"]:
                result = await self._check_auth_required(session, f"{base_url}{admin_path}", target)
                if result:
                    findings.append(result)

        return findings

    async def _test_default_creds(self, session, url: str, target: str) -> dict:
        for username, password in WEAK_CREDS[:5]:
            try:
                async with session.post(url, data={"username": username, "password": password},
                                        ssl=False, allow_redirects=False) as resp:
                    if resp.status in [200, 302]:
                        body = await resp.text(errors="ignore")
                        if any(kw in body.lower() for kw in ["dashboard", "welcome", "logout", "signout"]):
                            return {
                                "target": target,
                                "type": "auth_bypass",
                                "title": f"Default Credentials Work: {username}/{password}",
                                "severity": "critical",
                                "description": f"Login at {url} accepts default credentials {username}/{password}",
                                "proof": {"url": url, "username": username, "password": password},
                                "confidence": 0.95,
                                "remediation": "Remove default credentials immediately"
                            }
            except Exception:
                pass
        return None

    async def _check_jwt_issues(self, session, base_url: str, target: str) -> dict:
        """Look for JWT none algorithm or weak signing"""
        # A none-algorithm JWT (unsigned)
        none_jwt = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ."
        try:
            async with session.get(f"{base_url}/api/me",
                                   headers={"Authorization": f"Bearer {none_jwt}"},
                                   ssl=False) as resp:
                body = await resp.text(errors="ignore")
                if resp.status == 200 and len(body) > 10:
                    return {
                        "target": target,
                        "type": "jwt_none_algorithm",
                        "title": "JWT None Algorithm Accepted",
                        "severity": "critical",
                        "description": "Server accepts unsigned JWTs (alg=none) — authentication bypass possible",
                        "proof": {"url": f"{base_url}/api/me", "jwt": none_jwt},
                        "confidence": 0.90,
                        "remediation": "Reject JWTs with alg=none; always verify signature"
                    }
        except Exception:
            pass
        return None

    async def _check_auth_required(self, session, url: str, target: str) -> dict:
        try:
            async with session.get(url, ssl=False) as resp:
                body = await resp.text(errors="ignore")
                if resp.status == 200 and len(body) > 100:
                    if any(kw in body.lower() for kw in ["user", "admin", "email", "password", "token"]):
                        return {
                            "target": target,
                            "type": "auth_missing",
                            "title": f"Unauthenticated Access to Admin/Sensitive Endpoint",
                            "severity": "high",
                            "description": f"Sensitive endpoint accessible without authentication: {url}",
                            "proof": {"url": url, "status": 200},
                            "confidence": 0.70,
                            "remediation": "Require authentication on all sensitive endpoints"
                        }
        except Exception:
            pass
        return None
