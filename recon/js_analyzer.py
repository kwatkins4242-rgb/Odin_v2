"""
ODIN-Hunter | JS Analyzer
Extracts secrets, API keys, endpoints from JavaScript files
"""

import aiohttp
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Patterns to find in JS
SECRET_PATTERNS = {
    "aws_access_key":     r"AKIA[0-9A-Z]{16}",
    "aws_secret":         r"(?i)aws.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]",
    "google_api_key":     r"AIza[0-9A-Za-z\-_]{35}",
    "stripe_key":         r"sk_live_[0-9a-zA-Z]{24}",
    "stripe_pub_key":     r"pk_live_[0-9a-zA-Z]{24}",
    "github_token":       r"ghp_[0-9a-zA-Z]{36}",
    "jwt_token":          r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*",
    "private_key":        r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    "api_key_generic":    r"(?i)(api[_-]?key|apikey|api_secret)['\"\s:=]+['\"]([a-zA-Z0-9_\-]{20,})['\"]",
    "password_in_js":     r"(?i)(password|passwd|pwd)['\"\s:=]+['\"]([^'\"]{8,})['\"]",
    "basic_auth":         r"(?i)authorization:\s*basic\s+[a-zA-Z0-9+/=]{10,}",
    "bearer_token":       r"(?i)bearer\s+[a-zA-Z0-9\-._~+/=]{20,}",
    "internal_ip":        r"(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d+\.\d+",
    "firebase_config":    r"apiKey:\s*['\"][A-Za-z0-9_-]{39}['\"]",
    "slack_token":        r"xox[baprs]-[0-9A-Za-z\-]{10,}",
    "twilio_sid":         r"AC[a-z0-9]{32}",
    "sendgrid_key":       r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}",
}

API_PATTERNS = [
    r"['\"`](/api/v?\d*/[^'\"` ]+)['\"`]",
    r"['\"`](https?://[^'\"` ]+/api/[^'\"` ]+)['\"`]",
    r"fetch\(['\"`]([^'\"` ]+)['\"`]",
    r"axios\.(get|post|put|delete|patch)\(['\"`]([^'\"` ]+)['\"`]",
    r"url:\s*['\"`]([^'\"` ]+)['\"`]",
    r"endpoint:\s*['\"`]([^'\"` ]+)['\"`]",
]

class JSAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def analyze(self, target: str) -> dict:
        """Find and analyze all JS files on target"""
        js_files = await self._find_js_files(target)
        secrets = []
        api_endpoints = []
        source_maps = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for js_url in js_files[:50]:  # Cap at 50 files
                try:
                    async with session.get(js_url, ssl=False) as resp:
                        if resp.status == 200:
                            content = await resp.text(errors="ignore")

                            # Find secrets
                            for secret_type, pattern in SECRET_PATTERNS.items():
                                matches = re.findall(pattern, content)
                                for match in matches:
                                    if isinstance(match, tuple):
                                        match = match[-1]
                                    secrets.append({
                                        "type": secret_type,
                                        "value": match[:50] + "..." if len(match) > 50 else match,
                                        "file": js_url,
                                        "severity": "critical" if secret_type in ["aws_access_key", "stripe_key", "private_key"] else "high"
                                    })

                            # Find API endpoints
                            for pattern in API_PATTERNS:
                                matches = re.findall(pattern, content)
                                for match in matches:
                                    ep = match if isinstance(match, str) else match[-1]
                                    if ep and len(ep) > 1:
                                        api_endpoints.append(ep)

                            # Check for source maps
                            if js_url.endswith(".js"):
                                map_url = js_url + ".map"
                                try:
                                    async with session.get(map_url, ssl=False) as map_resp:
                                        if map_resp.status == 200:
                                            source_maps.append(map_url)
                                except Exception:
                                    pass

                except Exception:
                    pass

        result = {
            "js_files_analyzed": len(js_files),
            "secrets": secrets,
            "api_endpoints": list(set(api_endpoints)),
            "source_maps": source_maps
        }

        if secrets:
            print(f"[JSAnalyzer] 🚨 {len(secrets)} SECRETS found in {target}")
        print(f"[JSAnalyzer] {target}: {len(js_files)} JS files, {len(api_endpoints)} API endpoints")
        return result

    async def _find_js_files(self, target: str) -> list:
        """Find all JS file URLs on the target"""
        js_files = []
        base_url = f"https://{target}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(base_url, ssl=False) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors="ignore")
                        soup = BeautifulSoup(html, "html.parser")
                        for script in soup.find_all("script", src=True):
                            src = script.get("src", "")
                            if src:
                                full_url = urljoin(base_url, src)
                                if target in full_url or full_url.startswith("/"):
                                    js_files.append(full_url)
        except Exception as e:
            print(f"[JSAnalyzer] Error finding JS files: {e}")

        return js_files
