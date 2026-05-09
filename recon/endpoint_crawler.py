"""
ODIN-Hunter | Endpoint Crawler
Maps all accessible endpoints and routes
"""

import aiohttp
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

COMMON_PATHS = [
    "/", "/api", "/api/v1", "/api/v2", "/api/v3", "/graphql", "/graphiql",
    "/admin", "/administrator", "/admin/login", "/wp-admin", "/wp-login.php",
    "/login", "/logout", "/signin", "/signup", "/register", "/dashboard",
    "/user", "/users", "/profile", "/account", "/settings", "/config",
    "/debug", "/test", "/dev", "/staging", "/phpinfo.php", "/info.php",
    "/.env", "/.git", "/.git/config", "/robots.txt", "/sitemap.xml",
    "/swagger", "/swagger-ui.html", "/swagger.json", "/openapi.json",
    "/api-docs", "/docs", "/documentation", "/redoc", "/api/swagger",
    "/health", "/status", "/metrics", "/actuator", "/actuator/health",
    "/actuator/env", "/actuator/mappings", "/server-status", "/server-info",
    "/console", "/h2-console", "/jmx-console", "/web-console", "/manager",
    "/.well-known/security.txt", "/security.txt", "/crossdomain.xml",
    "/clientaccesspolicy.xml", "/.htaccess", "/web.config", "/backup",
    "/backup.zip", "/backup.tar.gz", "/db_backup.sql", "/dump.sql",
    "/upload", "/uploads", "/files", "/assets", "/static", "/media",
    "/api/users", "/api/admin", "/api/config", "/api/debug", "/api/test",
    "/v1/users", "/v1/admin", "/internal", "/private", "/secret"
]

class EndpointCrawler:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.visited = set()
        self.max_pages = 100

    async def crawl(self, target: str) -> list:
        """Crawl target for all endpoints"""
        found = []
        base_url = f"https://{target}"

        # First: check known paths
        path_results = await self._probe_paths(base_url)
        found.extend(path_results)

        # Second: spider from homepage
        spider_results = await self._spider(base_url)
        found.extend(spider_results)

        # Deduplicate
        seen = set()
        unique = []
        for ep in found:
            key = ep.get("path", "")
            if key not in seen:
                seen.add(key)
                unique.append(ep)

        print(f"[EndpointCrawler] {target}: {len(unique)} endpoints found")
        return unique

    async def _probe_paths(self, base_url: str) -> list:
        """Probe common paths"""
        found = []
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for path in COMMON_PATHS:
                url = f"{base_url}{path}"
                try:
                    async with session.get(url, allow_redirects=False, ssl=False) as resp:
                        if resp.status not in [404, 403, 410]:
                            found.append({
                                "path": path,
                                "url": url,
                                "status": resp.status,
                                "content_type": resp.headers.get("Content-Type", ""),
                                "interesting": resp.status in [200, 301, 302, 500]
                            })
                except Exception:
                    pass
        return found

    async def _spider(self, base_url: str) -> list:
        """Spider the site from the homepage"""
        found = []
        to_visit = [base_url]
        domain = urlparse(base_url).netloc

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            while to_visit and len(self.visited) < self.max_pages:
                url = to_visit.pop(0)
                if url in self.visited:
                    continue
                self.visited.add(url)

                try:
                    async with session.get(url, ssl=False) as resp:
                        if resp.status == 200:
                            html = await resp.text(errors="ignore")
                            soup = BeautifulSoup(html, "html.parser")
                            path = urlparse(url).path
                            found.append({"path": path, "url": url, "status": 200, "source": "spider"})

                            # Find all links
                            for tag in soup.find_all(["a", "form", "script", "link"]):
                                href = tag.get("href") or tag.get("src") or tag.get("action", "")
                                if href:
                                    full_url = urljoin(url, href)
                                    if urlparse(full_url).netloc == domain:
                                        if full_url not in self.visited:
                                            to_visit.append(full_url)

                            # Find API calls in JS
                            api_pattern = re.findall(r'["\']/(api/[^"\'?\s]+)', html)
                            for api_path in api_pattern:
                                found.append({"path": f"/{api_path}", "url": f"{base_url}/{api_path}", "status": "unknown", "source": "js_extract"})
                except Exception:
                    pass

        return found
