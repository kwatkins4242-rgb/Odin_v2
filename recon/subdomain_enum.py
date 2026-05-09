"""
ODIN-Hunter | Subdomain Enumerator
Uses DNS brute force + passive sources
"""

import asyncio
import aiohttp
import dns.resolver
import os
from dotenv import load_dotenv

load_dotenv()

MAX_SUBS = int(os.getenv("HUNTER_MAX_SUBDOMAINS", "500"))

# Wordlist for common subdomains
COMMON_SUBDOMAINS = [
    "www", "api", "dev", "staging", "test", "admin", "app", "mail", "smtp",
    "ftp", "ssh", "vpn", "cdn", "static", "assets", "media", "images", "img",
    "portal", "dashboard", "manage", "management", "beta", "alpha", "internal",
    "intranet", "corp", "corporate", "shop", "store", "blog", "forum", "support",
    "help", "docs", "documentation", "wiki", "git", "gitlab", "github", "jenkins",
    "ci", "cd", "build", "deploy", "prod", "production", "stg", "uat", "qa",
    "db", "database", "mysql", "redis", "mongo", "elastic", "kibana", "grafana",
    "monitor", "metrics", "logs", "analytics", "tracking", "auth", "sso", "login",
    "accounts", "user", "users", "account", "members", "member", "signup", "register",
    "checkout", "payment", "pay", "billing", "invoice", "gateway", "v1", "v2", "v3",
    "api-v1", "api-v2", "old", "legacy", "new", "secure", "security", "ssl",
    "mobile", "m", "wap", "search", "news", "events", "jobs", "careers", "partner",
    "partners", "affiliate", "affiliates", "exchange", "upload", "download", "file",
    "files", "backup", "bak", "archive", "data", "report", "reports", "status",
    "health", "ping", "test2", "dev2", "staging2", "sandbox"
]

class SubdomainEnum:
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3
        self.resolver.lifetime = 3

    async def enumerate(self, domain: str) -> list:
        """Enumerate subdomains using multiple methods"""
        found = set()

        # Method 1: DNS brute force
        brute_results = await self._brute_force(domain)
        found.update(brute_results)

        # Method 2: Certificate transparency logs (crt.sh)
        ct_results = await self._cert_transparency(domain)
        found.update(ct_results)

        # Method 3: HackerTarget passive
        ht_results = await self._hackertarget(domain)
        found.update(ht_results)

        result = sorted(list(found))[:MAX_SUBS]
        print(f"[SubdomainEnum] Found {len(result)} subdomains for {domain}")
        return result

    async def _brute_force(self, domain: str) -> list:
        """DNS brute force using wordlist"""
        found = []
        loop = asyncio.get_event_loop()

        async def check(subdomain):
            fqdn = f"{subdomain}.{domain}"
            try:
                await loop.run_in_executor(None, self.resolver.resolve, fqdn, "A")
                return fqdn
            except Exception:
                return None

        tasks = [check(sub) for sub in COMMON_SUBDOMAINS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        found = [r for r in results if isinstance(r, str)]
        return found

    async def _cert_transparency(self, domain: str) -> list:
        """Query crt.sh for certificate transparency logs"""
        found = []
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://crt.sh/?q=%.{domain}&output=json"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        for entry in data:
                            name = entry.get("name_value", "")
                            for n in name.split("\n"):
                                n = n.strip().lstrip("*.")
                                if n.endswith(domain) and n != domain:
                                    found.append(n)
        except Exception as e:
            print(f"[SubdomainEnum] crt.sh error: {e}")
        return list(set(found))

    async def _hackertarget(self, domain: str) -> list:
        """Query HackerTarget for subdomain data"""
        found = []
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        for line in text.splitlines():
                            if "," in line:
                                subdomain = line.split(",")[0].strip()
                                if subdomain.endswith(domain):
                                    found.append(subdomain)
        except Exception as e:
            print(f"[SubdomainEnum] HackerTarget error: {e}")
        return found
