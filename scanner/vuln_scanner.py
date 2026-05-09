"""
ODIN-Hunter | Master Vulnerability Scanner
Orchestrates all scanners against target attack surface
"""

import asyncio
from scanner.sqli_tester import SQLiTester
from scanner.xss_tester import XSSTester
from scanner.ssrf_tester import SSRFTester
from scanner.idor_tester import IDORTester
from scanner.auth_tester import AuthTester
from scanner.api_tester import APITester
from scanner.swagger_scanner import SwaggerScanner
from integrations.kali_bridge import KaliBridge
from integrations.burp_bridge import BurpBridge

class VulnScanner:
    def __init__(self):
        self.sqli   = SQLiTester()
        self.xss    = XSSTester()
        self.ssrf   = SSRFTester()
        self.idor   = IDORTester()
        self.auth   = AuthTester()
        self.api    = APITester()
        self.swagger = SwaggerScanner()
        self.kali    = KaliBridge()
        self.burp    = BurpBridge()
        self.active_scan_count = 0

    async def scan_all(self, target: str, recon_data: dict) -> list:
        """Run all scanners against target, return list of findings"""
        self.active_scan_count += 1
        findings = []
        endpoints = recon_data.get("endpoints", [])
        tech_stack = recon_data.get("tech_stack", {}).get("technologies", {})
        js_findings = recon_data.get("js_findings", {})

        try:
            # --- 1. Swagger / OpenAPI Parsing ---
            swagger_findings, api_surface = await self.swagger.scan(target, recon_data)
            if swagger_findings:
                findings.extend(swagger_findings)
            if api_surface:
                recon_data["api_surface"] = api_surface
                # Add discovered Swagger endpoints to our attack surface mapping
                for ep in api_surface.get("endpoints", []):
                    if not any(e.get("path") == ep.get("path") for e in endpoints):
                        endpoints.append({
                            "path": ep.get("path"),
                            "method": ep.get("method"),
                            "interesting": ep.get("interesting", False)
                        })

            # --- 2. Secrets in JS (instant wins) ---
            for secret in js_findings.get("secrets", []):
                findings.append({
                    "target": target,
                    "type": "secret_exposure",
                    "title": f"Secret Exposed in JS: {secret['type']}",
                    "severity": secret.get("severity", "high"),
                    "description": f"A {secret['type']} was found in a public JavaScript file.",
                    "proof": {"file": secret.get("file"), "type": secret["type"]},
                    "confidence": 0.95
                })

            # --- 3. Security headers ---
            security_headers = recon_data.get("tech_stack", {}).get("security_headers", {})
            missing = security_headers.get("missing", {})
            for header, risk in missing.items():
                if header in ["Strict-Transport-Security", "Content-Security-Policy"]:
                    findings.append({
                        "target": target,
                        "type": "missing_security_header",
                        "title": f"Missing Security Header: {header}",
                        "severity": "low" if header not in ["Strict-Transport-Security"] else "medium",
                        "description": risk,
                        "proof": {"missing_header": header},
                        "confidence": 0.99
                    })

            # --- 4. Source maps exposed ---
            for map_url in js_findings.get("source_maps", []):
                findings.append({
                    "target": target,
                    "type": "source_map_exposed",
                    "title": "JavaScript Source Map Exposed",
                    "severity": "medium",
                    "description": f"Source map found at {map_url} — reveals original source code.",
                    "proof": {"url": map_url},
                    "confidence": 0.95
                })

            # --- 5. Scanner tasks (run in parallel) ---
            interesting_endpoints = [ep for ep in endpoints if ep.get("interesting")][:20]

            scan_tasks = [
                self.sqli.test(target, interesting_endpoints),
                self.xss.test(target, interesting_endpoints),
                self.ssrf.test(target, interesting_endpoints),
                self.idor.test(target, interesting_endpoints),
                self.auth.test(target, recon_data),
                self.api.test(target, recon_data),
                self.kali.run_all(target, recon_data),    # KALI LINUX RUNS HERE
                self.burp.run_active_scan(target),        # BURP ACTIVE SCAN RUNS HERE
            ]

            results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    findings.extend(result)
                elif isinstance(result, Exception):
                    print(f"[VulnScanner] Tool raised exception: {result}")

        finally:
            self.active_scan_count -= 1

        print(f"[VulnScanner] {target}: {len(findings)} raw findings")
        return findings
