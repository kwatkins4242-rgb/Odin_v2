"""
ODIN-Hunter | Swagger / OpenAPI Scanner
Fetches and parses OpenAPI specs (JSON or YAML) from common paths,
maps every endpoint into ODIN's attack surface, and flags instant findings:
  - Unauthenticated sensitive routes
  - File upload endpoints (multipart/form-data)
  - Debug/admin/swagger-ui exposure
  - Auth scheme weaknesses (HTTP basic, no auth)

Returns both:
  - A structured `api_surface` dict (injected into recon_data)
  - A list of instant ODIN `findings`
"""

import asyncio
import os
import json
import aiohttp
from urllib.parse import urlparse

try:
    import yaml  # type: ignore
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Common paths where specs live
SPEC_PATHS = [
    "/openapi.json",
    "/openapi.yaml",
    "/swagger.json",
    "/swagger.yaml",
    "/api/swagger.json",
    "/api/openapi.json",
    "/api-docs",
    "/api-docs/swagger.json",
    "/v1/api-docs",
    "/v2/api-docs",
    "/v3/api-docs",
    "/docs/openapi.json",
    "/api/v1/swagger.json",
    "/api/v2/swagger.json",
    "/api/v3/swagger.json",
    "/api/schema/",
    "/swagger/v1/swagger.json",
    "/swagger/v2/swagger.json",
]

SENSITIVE_KEYWORDS = [
    "admin", "user", "account", "password", "token", "auth", "login",
    "secret", "key", "payment", "billing", "credit", "card", "ssn",
    "transfer", "withdraw", "delete", "destroy", "internal", "private",
    "config", "setting", "export", "dump", "backup"
]


class SwaggerScanner:
    """
    Discovers and parses OpenAPI/Swagger specs from a target.
    Returns (api_surface: dict, findings: list[dict])
    """

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    # ── Spec Fetching ───────────────────────────────────────────────

    async def _fetch_spec(self, session: aiohttp.ClientSession, url: str) -> dict | None:
        """Try to fetch and parse a spec at the given URL."""
        try:
            async with session.get(url, ssl=False, allow_redirects=True) as resp:
                if resp.status != 200:
                    return None
                ct = resp.headers.get("Content-Type", "")
                text = await resp.text(errors="ignore")

                # Must look like JSON or YAML
                if not text.strip().startswith(("{", "[", "openapi", "swagger")):
                    return None

                if "yaml" in ct or "yml" in url or text.strip().startswith(("openapi", "swagger")):
                    if YAML_AVAILABLE:
                        try:
                            return yaml.safe_load(text)
                        except Exception:
                            pass
                    return None
                else:
                    try:
                        return json.loads(text)
                    except Exception:
                        return None
        except Exception:
            return None

    async def find_spec(self, target: str) -> tuple[str | None, dict | None]:
        """Probe common paths to find the first valid OpenAPI spec."""
        base = f"https://{target}" if not target.startswith("http") else target
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for path in SPEC_PATHS:
                url = f"{base}{path}"
                spec = await self._fetch_spec(session, url)
                if spec and ("paths" in spec or "swagger" in spec or "openapi" in spec):
                    print(f"[SwaggerScanner] Found spec at {url}")
                    return url, spec
        return None, None

    # ── Spec Parsing ────────────────────────────────────────────────

    def _parse_endpoints(self, spec: dict, base_url: str) -> list[dict]:
        """Extract all endpoints from an OpenAPI/Swagger spec."""
        endpoints = []
        paths = spec.get("paths", {})
        security_schemes = spec.get("components", {}).get("securitySchemes",
                           spec.get("securityDefinitions", {}))

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, op in methods.items():
                if method.lower() not in ("get", "post", "put", "patch", "delete", "head", "options"):
                    continue
                if not isinstance(op, dict):
                    continue

                # Collect parameters
                params = op.get("parameters", [])
                body_schema = (op.get("requestBody", {})
                               .get("content", {})
                               .get("application/json", {})
                               .get("schema", {}))

                # Detect file upload
                is_upload = any(
                    "multipart/form-data" in str(op.get("requestBody", {})) or
                    "binary" in str(op.get("requestBody", {}))
                    for _ in [1]
                )

                # Auth required?
                op_security = op.get("security", spec.get("security", []))
                has_auth = bool(op_security) and op_security != [{}]

                # Sensitive path?
                is_sensitive = any(kw in path.lower() for kw in SENSITIVE_KEYWORDS)

                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "url": f"{base_url}{path}",
                    "summary": op.get("summary", ""),
                    "params": params,
                    "body_schema": body_schema,
                    "has_auth": has_auth,
                    "is_upload": is_upload,
                    "is_sensitive": is_sensitive,
                    "interesting": is_sensitive or is_upload or not has_auth,
                    "tags": op.get("tags", []),
                    "source": "swagger_spec"
                })

        return endpoints

    def _detect_findings(self, spec: dict, endpoints: list[dict],
                         spec_url: str, target: str) -> list[dict]:
        """Generate instant findings from the spec itself."""
        findings = []

        # 1. Spec publicly exposed
        findings.append({
            "target": target,
            "type": "swagger_exposed",
            "title": "API Spec Publicly Accessible",
            "severity": "info",
            "description": f"OpenAPI/Swagger spec found at {spec_url} — full API surface exposed.",
            "proof": {"url": spec_url},
            "confidence": 0.99,
            "source": "swagger_scanner",
            "remediation": "Restrict spec access to authenticated users or internal network only."
        })

        # 2. Sensitive endpoints without auth
        for ep in endpoints:
            if ep["is_sensitive"] and not ep["has_auth"]:
                findings.append({
                    "target": target,
                    "type": "unauth_sensitive_endpoint",
                    "title": f"Sensitive Endpoint Without Auth: {ep['method']} {ep['path']}",
                    "severity": "high",
                    "description": (
                        f"Endpoint {ep['method']} {ep['path']} appears sensitive "
                        f"but has no authentication requirement in the spec."
                    ),
                    "proof": {"method": ep["method"], "path": ep["path"], "spec_url": spec_url},
                    "confidence": 0.75,
                    "source": "swagger_scanner",
                    "remediation": "Add authentication/authorization to this endpoint."
                })

        # 3. File upload endpoints (easy SSRF/path traversal surface)
        for ep in endpoints:
            if ep["is_upload"]:
                findings.append({
                    "target": target,
                    "type": "file_upload_endpoint",
                    "title": f"File Upload Endpoint: {ep['method']} {ep['path']}",
                    "severity": "medium",
                    "description": f"File upload detected at {ep['path']} — test for unrestricted upload, path traversal, SSRF.",
                    "proof": {"method": ep["method"], "path": ep["path"]},
                    "confidence": 0.85,
                    "source": "swagger_scanner",
                    "remediation": "Validate file types, size limits, and sanitize filenames."
                })

        # 4. HTTP Basic auth scheme (weak)
        security_schemes = spec.get("components", {}).get("securitySchemes",
                           spec.get("securityDefinitions", {}))
        for name, scheme in security_schemes.items():
            if scheme.get("type") == "http" and scheme.get("scheme") == "basic":
                findings.append({
                    "target": target,
                    "type": "weak_auth_scheme",
                    "title": "HTTP Basic Authentication Used",
                    "severity": "medium",
                    "description": f"Security scheme '{name}' uses HTTP Basic auth — susceptible to credential theft over plain HTTP.",
                    "proof": {"scheme_name": name, "type": "http_basic"},
                    "confidence": 0.90,
                    "source": "swagger_scanner",
                    "remediation": "Replace with OAuth2, JWT, or API keys over HTTPS."
                })

        # 5. No global auth
        global_security = spec.get("security", [])
        if not global_security:
            findings.append({
                "target": target,
                "type": "no_global_auth",
                "title": "No Global Authentication Defined in API Spec",
                "severity": "medium",
                "description": "The OpenAPI spec defines no global security requirement — individual endpoints may lack auth.",
                "proof": {"spec_url": spec_url},
                "confidence": 0.70,
                "source": "swagger_scanner",
                "remediation": "Define a global security requirement and override per-endpoint where needed."
            })

        return findings

    # ── Main Entry Point ────────────────────────────────────────────

    async def scan(self, target: str, recon_data: dict) -> tuple[list[dict], dict]:
        """
        Scan a target for OpenAPI specs.
        Returns (findings, api_surface).
        api_surface is injected into recon_data by VulnScanner.
        """
        base = f"https://{target}" if not target.startswith("http") else target
        spec_url, spec = await self.find_spec(target)

        if not spec:
            return [], {}

        endpoints = self._parse_endpoints(spec, base)
        findings  = self._detect_findings(spec, endpoints, spec_url, target)

        api_surface = {
            "spec_url":       spec_url,
            "spec_version":   spec.get("openapi") or spec.get("swagger"),
            "api_title":      spec.get("info", {}).get("title", ""),
            "endpoints":      endpoints,
            "endpoint_count": len(endpoints),
            "auth_schemes":   list(spec.get("components", {})
                              .get("securitySchemes",
                                   spec.get("securityDefinitions", {})).keys()),
        }

        print(f"[SwaggerScanner] {target}: {len(endpoints)} endpoints, {len(findings)} instant findings")
        return findings, api_surface
