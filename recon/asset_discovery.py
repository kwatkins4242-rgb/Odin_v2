"""
ODIN-Hunter | Asset Discoverer
Finds forgotten endpoints, backup files, exposed configs
"""

import aiohttp
import asyncio

JUICY_PATHS = [
    # Backups
    "/backup.zip", "/backup.tar.gz", "/backup.sql", "/db.sql", "/dump.sql",
    "/database.sql", "/site.tar.gz", "/www.tar.gz", "/backup.bak",
    "/.git/config", "/.git/HEAD", "/.git/COMMIT_EDITMSG", "/.svn/entries",
    # Config files
    "/.env", "/.env.local", "/.env.production", "/.env.backup",
    "/config.php", "/config.js", "/config.json", "/configuration.php",
    "/wp-config.php", "/wp-config.php.bak", "/web.config", "/app.config",
    "/database.yml", "/database.json", "/settings.py", "/local_settings.py",
    # Logs
    "/error.log", "/access.log", "/debug.log", "/application.log",
    "/logs/error.log", "/var/log/error.log", "/log/error.log",
    # AWS / Cloud
    "/.aws/credentials", "/.aws/config", "/s3.json", "/aws.json",
    # Docker / K8s
    "/docker-compose.yml", "/docker-compose.yaml", "/.dockerenv",
    "/k8s.yml", "/kubernetes.yml", "/secrets.yml",
    # Package files
    "/package.json", "/composer.json", "/requirements.txt", "/Gemfile",
    "/yarn.lock", "/package-lock.json",
    # Editor / IDE
    "/.idea/workspace.xml", "/.vscode/settings.json", "/.DS_Store",
    # Admin panels
    "/phpmyadmin", "/phpMyAdmin", "/pma", "/adminer.php", "/adminer",
    "/mysql-admin", "/db-admin", "/database-admin",
    # API docs
    "/swagger.json", "/swagger.yaml", "/openapi.json", "/openapi.yaml",
    "/api-docs.json", "/api/swagger.json",
    # Jenkins / CI
    "/jenkins", "/jenkins/login", "/.jenkins", "/hudson",
    # Spring Boot actuator
    "/actuator", "/actuator/env", "/actuator/beans", "/actuator/mappings",
    "/actuator/health", "/actuator/info", "/actuator/metrics",
    # Misc
    "/CHANGELOG", "/CHANGELOG.md", "/VERSION", "/README.md",
    "/.htpasswd", "/passwd", "/shadow", "/etc/passwd",
]

class AssetDiscoverer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=8)

    async def discover(self, target: str) -> dict:
        """Discover hidden/forgotten assets on target"""
        found_assets = []
        base_url = f"https://{target}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [self._probe(session, base_url, path) for path in JUICY_PATHS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        found_assets = [r for r in results if isinstance(r, dict)]

        if found_assets:
            print(f"[AssetDiscoverer] 🎯 {len(found_assets)} interesting assets on {target}")
        return {
            "target": target,
            "assets": found_assets,
            "count": len(found_assets)
        }

    async def _probe(self, session, base_url: str, path: str) -> dict:
        """Probe a single path"""
        url = f"{base_url}{path}"
        try:
            async with session.get(url, allow_redirects=False, ssl=False) as resp:
                if resp.status in [200, 206, 301, 302, 307, 401, 403, 500]:
                    content_len = resp.headers.get("Content-Length", "0")
                    risk = self._assess_risk(path, resp.status)
                    if risk != "none":
                        return {
                            "path": path,
                            "url": url,
                            "status": resp.status,
                            "content_length": content_len,
                            "risk": risk
                        }
        except Exception:
            pass
        return None

    def _assess_risk(self, path: str, status: int) -> str:
        """Assess the risk level of a found asset"""
        critical_patterns = [".env", ".git", "config", "credentials", "passwd",
                             "secret", "backup", "dump", "sql", "actuator/env",
                             "actuator/beans", "actuator/mappings"]
        high_patterns = [".aws", "docker", "phpMyAdmin", "adminer", "phpmyadmin",
                        "swagger", "openapi", "package.json", "composer.json"]

        path_lower = path.lower()

        if status == 200:
            for p in critical_patterns:
                if p in path_lower:
                    return "critical"
            for p in high_patterns:
                if p in path_lower:
                    return "high"
            return "medium"
        elif status in [401, 403]:
            return "low"  # Exists but protected
        elif status == 500:
            return "medium"  # Error = information
        return "none"