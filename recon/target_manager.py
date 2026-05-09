"""
ODIN-Hunter | Target Manager
Orchestrates full recon pipeline on a target
"""

from recon.subdomain_enum import SubdomainEnum
from recon.port_scanner import PortScanner
from recon.tech_fingerprint import TechFingerprint
from recon.endpoint_crawler import EndpointCrawler
from recon.js_analyzer import JSAnalyzer
from recon.asset_discoverer import AssetDiscoverer

class TargetManager:
    def __init__(self):
        self.subdomain_enum  = SubdomainEnum()
        self.port_scanner    = PortScanner()
        self.tech_fp         = TechFingerprint()
        self.crawler         = EndpointCrawler()
        self.js_analyzer     = JSAnalyzer()
        self.asset_discoverer = AssetDiscoverer()

    async def run_full_recon(self, target: str) -> dict:
        """Run complete recon pipeline, return structured data"""
        print(f"[TargetManager] Starting full recon on {target}")
        recon = {"target": target}

        # Subdomains
        print(f"[TargetManager] Enumerating subdomains...")
        recon["subdomains"] = await self.subdomain_enum.enumerate(target)

        # Ports on main target + top subdomains
        print(f"[TargetManager] Scanning ports...")
        top_targets = [target] + recon["subdomains"][:10]
        recon["ports"] = {}
        for t in top_targets:
            recon["ports"][t] = await self.port_scanner.scan(t)

        # Tech fingerprint
        print(f"[TargetManager] Fingerprinting tech stack...")
        recon["tech_stack"] = await self.tech_fp.fingerprint(target)

        # Endpoint crawl
        print(f"[TargetManager] Crawling endpoints...")
        recon["endpoints"] = await self.crawler.crawl(target)

        # JS analysis
        print(f"[TargetManager] Analyzing JS files...")
        recon["js_findings"] = await self.js_analyzer.analyze(target)

        # Hidden assets
        print(f"[TargetManager] Discovering assets...")
        recon["assets"] = await self.asset_discoverer.discover(target)

        print(f"[TargetManager] Recon complete: {len(recon['subdomains'])} subdomains, {len(recon['endpoints'])} endpoints")
        return recon

    async def get_attack_surface(self, recon_data: dict) -> list:
        """Extract all attack surface targets from recon data"""
        targets = []
        base = recon_data.get("target", "")

        # Main target
        targets.append({"host": base, "type": "main"})

        # Subdomains
        for sub in recon_data.get("subdomains", []):
            targets.append({"host": sub, "type": "subdomain"})

        # Endpoints
        for ep in recon_data.get("endpoints", []):
            targets.append({"host": base, "path": ep, "type": "endpoint"})

        # APIs found in JS
        for js_find in recon_data.get("js_findings", {}).get("api_endpoints", []):
            targets.append({"host": base, "path": js_find, "type": "api_endpoint"})

        return targets
