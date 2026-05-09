"""
ODIN-Hunter | Tech Fingerprinter
Identifies technology stack from headers, cookies, HTML
"""

import aiohttp
import re

TECH_SIGNATURES = {
    "WordPress":    {"headers": [], "html": [r"wp-content", r"wp-includes", r"WordPress"]},
    "Drupal":       {"headers": ["X-Generator: Drupal"], "html": [r"Drupal"]},
    "Joomla":       {"headers": [], "html": [r"/components/com_", r"Joomla"]},
    "Laravel":      {"headers": [], "cookies": ["laravel_session"], "html": [r"Laravel"]},
    "Django":       {"headers": [], "cookies": ["csrftoken", "sessionid"], "html": []},
    "Rails":        {"headers": ["X-Powered-By: Phusion Passenger"], "cookies": ["_session_id"], "html": []},
    "Express":      {"headers": ["X-Powered-By: Express"], "html": []},
    "ASP.NET":      {"headers": ["X-Powered-By: ASP.NET", "X-AspNet-Version"], "cookies": ["ASP.NET_SessionId", "__RequestVerificationToken"], "html": []},
    "PHP":          {"headers": ["X-Powered-By: PHP"], "html": [r"\.php"]},
    "Apache":       {"headers": ["Server: Apache"], "html": []},
    "Nginx":        {"headers": ["Server: nginx"], "html": []},
    "IIS":          {"headers": ["Server: Microsoft-IIS"], "html": []},
    "Cloudflare":   {"headers": ["CF-Ray", "cf-cache-status"], "html": []},
    "AWS":          {"headers": ["x-amz-request-id", "x-amz-id-2"], "html": []},
    "React":        {"html": [r"__REACT_DEVTOOLS", r"react-dom", r"_reactFiber"]},
    "Angular":      {"html": [r"ng-version", r"angular", r"\[_nghost"]},
    "Vue":          {"html": [r"__vue__", r"vue\.js", r"vuejs"]},
    "jQuery":       {"html": [r"jquery", r"jQuery"]},
    "Bootstrap":    {"html": [r"bootstrap\.css", r"bootstrap\.min\.js"]},
    "GraphQL":      {"html": [r"graphql", r"__typename"]},
    "Elasticsearch":{"html": [], "paths": ["/elasticsearch", "/_search", "/_cat"]},
    "Kubernetes":   {"headers": ["x-kubernetes-pf-prioritylevel-uid"], "html": []},
}

class TechFingerprint:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def fingerprint(self, target: str) -> dict:
        """Identify tech stack of a target"""
        detected = {}
        urls = [f"https://{target}", f"http://{target}"]

        for url in urls:
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, allow_redirects=True, ssl=False) as resp:
                        headers = dict(resp.headers)
                        cookies = {c.key: c.value for c in resp.cookies.values()}
                        html = await resp.text(errors="ignore")

                        for tech, sigs in TECH_SIGNATURES.items():
                            # Check headers
                            for h_sig in sigs.get("headers", []):
                                key = h_sig.split(":")[0].strip()
                                if key.lower() in {k.lower() for k in headers}:
                                    detected[tech] = {"confidence": "high", "method": "header"}

                            # Check cookies
                            for c_sig in sigs.get("cookies", []):
                                if c_sig in cookies:
                                    detected[tech] = {"confidence": "high", "method": "cookie"}

                            # Check HTML patterns
                            for pattern in sigs.get("html", []):
                                if re.search(pattern, html, re.IGNORECASE):
                                    if tech not in detected:
                                        detected[tech] = {"confidence": "medium", "method": "html"}

                        # Security headers audit
                        security_headers = self._check_security_headers(headers)
                        break  # Got a response, stop trying
            except Exception:
                continue

        result = {
            "target": target,
            "technologies": detected,
            "security_headers": security_headers if 'security_headers' in locals() else {}
        }
        print(f"[TechFingerprint] {target}: {list(detected.keys())}")
        return result

    def _check_security_headers(self, headers: dict) -> dict:
        """Check for missing security headers — often leads to findings"""
        required = {
            "Strict-Transport-Security": "HSTS missing — possible SSL stripping",
            "X-Frame-Options": "Clickjacking possible",
            "X-Content-Type-Options": "MIME sniffing possible",
            "Content-Security-Policy": "XSS protection may be missing",
            "X-XSS-Protection": "XSS filter disabled",
            "Referrer-Policy": "Information disclosure via Referrer",
            "Permissions-Policy": "Browser feature exposure"
        }
        lower_headers = {k.lower(): v for k, v in headers.items()}
        missing = {}
        for header, risk in required.items():
            if header.lower() not in lower_headers:
                missing[header] = risk
        return {"missing": missing, "present": [h for h in required if h.lower() in lower_headers]}
