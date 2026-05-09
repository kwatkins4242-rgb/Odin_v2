"""
ODIN-Hunter | API Tester
Tests API-specific vulnerabilities
"""
import aiohttp
import asyncio
import json

class APITester:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def test(self, target: str, recon_data: dict) -> list:
        findings = []
        base_url = f"https://{target}"
        endpoints = recon_data.get("endpoints", [])
        js_apis = recon_data.get("js_findings", {}).get("api_endpoints", [])

        all_api_paths = (
            [ep.get("path") for ep in endpoints if "/api" in ep.get("path", "")]
            + [p for p in js_apis if "/api" in p]
        )

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # GraphQL introspection
            for gql_path in ["/graphql", "/api/graphql", "/graphiql"]:
                result = await self._test_graphql(session, f"{base_url}{gql_path}", target)
                if result:
                    findings.append(result)

            # Mass assignment
            for path in all_api_paths[:10]:
                result = await self._test_mass_assignment(session, f"{base_url}{path}", target)
                if result:
                    findings.append(result)

            # API versioning issues (v1 accessible when v2 is current)
            result = await self._test_api_versioning(session, base_url, target)
            if result:
                findings.extend(result)

            # HTTP method override
            for path in all_api_paths[:5]:
                result = await self._test_method_override(session, f"{base_url}{path}", target)
                if result:
                    findings.append(result)

        return findings

    async def _test_graphql(self, session, url: str, target: str) -> dict:
        introspection_query = {"query": "{__schema{types{name fields{name}}}}"}
        try:
            async with session.post(url, json=introspection_query, ssl=False) as resp:
                body = await resp.text(errors="ignore")
                if resp.status == 200 and "__schema" in body:
                    return {
                        "target": target,
                        "type": "graphql_introspection",
                        "title": "GraphQL Introspection Enabled",
                        "severity": "medium",
                        "description": f"GraphQL introspection enabled at {url} — full schema exposed",
                        "proof": {"url": url, "response_snippet": body[:300]},
                        "confidence": 0.95,
                        "remediation": "Disable introspection in production environments"
                    }
        except Exception:
            pass
        return None

    async def _test_mass_assignment(self, session, url: str, target: str) -> dict:
        test_payload = {"role": "admin", "is_admin": True, "admin": True, "is_superuser": True}
        try:
            async with session.post(url, json=test_payload, ssl=False) as resp:
                body = await resp.text(errors="ignore")
                if resp.status in [200, 201]:
                    if any(kw in body.lower() for kw in ["admin", "role", "superuser", "privilege"]):
                        return {
                            "target": target,
                            "type": "mass_assignment",
                            "title": "Potential Mass Assignment Vulnerability",
                            "severity": "high",
                            "description": f"API at {url} may accept unintended fields including privilege escalation fields",
                            "proof": {"url": url, "payload": test_payload},
                            "confidence": 0.60,
                            "remediation": "Whitelist allowed fields; never bind request body directly to model"
                        }
        except Exception:
            pass
        return None

    async def _test_api_versioning(self, session, base_url: str, target: str) -> list:
        findings = []
        for v_old, v_new in [("v1", "v2"), ("v1", "v3"), ("v2", "v3")]:
            old_url = f"{base_url}/api/{v_old}/users"
            new_url = f"{base_url}/api/{v_new}/users"
            try:
                async with session.get(old_url, ssl=False) as old_resp:
                    async with session.get(new_url, ssl=False) as new_resp:
                        if old_resp.status == 200 and new_resp.status == 200:
                            old_body = await old_resp.text(errors="ignore")
                            if len(old_body) > 50 and "{" in old_body:
                                findings.append({
                                    "target": target,
                                    "type": "deprecated_api",
                                    "title": f"Deprecated API Version {v_old} Still Accessible",
                                    "severity": "medium",
                                    "description": f"Old API version {v_old} still active — may lack security fixes",
                                    "proof": {"url": old_url},
                                    "confidence": 0.80,
                                    "remediation": f"Deprecate {v_old} API; redirect to {v_new}"
                                })
            except Exception:
                pass
        return findings

    async def _test_method_override(self, session, url: str, target: str) -> dict:
        try:
            headers = {"X-HTTP-Method-Override": "DELETE", "X-Method-Override": "DELETE"}
            async with session.get(url, headers=headers, ssl=False) as resp:
                if resp.status in [200, 204]:
                    return {
                        "target": target,
                        "type": "http_method_override",
                        "title": "HTTP Method Override Accepted",
                        "severity": "medium",
                        "description": f"Server at {url} honors X-HTTP-Method-Override header",
                        "proof": {"url": url, "override_header": "X-HTTP-Method-Override: DELETE"},
                        "confidence": 0.65,
                        "remediation": "Validate HTTP method against allowed methods; ignore override headers"
                    }
        except Exception:
            pass
        return None
