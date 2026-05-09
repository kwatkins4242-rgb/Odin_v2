"""
ODIN-Hunter | Severity Classifier
CVSS v3.1 scoring and severity normalization
"""

SEVERITY_TO_CVSS = {
    "critical": 9.5,
    "high": 7.5,
    "medium": 5.5,
    "low": 2.5,
    "informational": 0.0
}

CVSS_RANGES = {
    (9.0, 10.0): "critical",
    (7.0, 8.9):  "high",
    (4.0, 6.9):  "medium",
    (0.1, 3.9):  "low",
    (0.0, 0.0):  "informational"
}

BOUNTY_ESTIMATES = {
    "critical": (5000, 50000),
    "high":     (1000, 10000),
    "medium":   (200,  2000),
    "low":      (50,   500),
    "informational": (0, 150)
}

class SeverityClassifier:
    def calculate_cvss(self, finding: dict) -> dict:
        severity = finding.get("severity", "medium").lower()
        vuln_type = finding.get("type", "")

        # Base scores by type
        type_scores = {
            "sql_injection": 9.8,
            "auth_bypass": 9.1,
            "jwt_none_algorithm": 9.1,
            "ssrf": 8.8,
            "xss": 8.2,
            "idor": 8.0,
            "secret_exposure": 9.0,
            "mass_assignment": 7.5,
            "graphql_introspection": 5.3,
            "http_method_override": 5.0,
            "deprecated_api": 5.0,
            "missing_security_header": 3.7,
            "source_map_exposed": 5.3,
            "dom_xss": 7.5,
            "auth_missing": 8.5,
        }

        score = type_scores.get(vuln_type, SEVERITY_TO_CVSS.get(severity, 5.5))

        # Adjust by confidence
        confidence = finding.get("confidence", 0.8)
        adjusted = score * confidence

        return {
            "score": round(score, 1),
            "adjusted_score": round(adjusted, 1),
            "severity": severity,
            "vector": self._get_vector(vuln_type)
        }

    def _get_vector(self, vuln_type: str) -> str:
        vectors = {
            "sql_injection": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            "xss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
            "ssrf": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:L/A:N",
            "idor": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N",
            "auth_bypass": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        }
        return vectors.get(vuln_type, "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N")

    def normalize_severity(self, severity: str) -> str:
        mapping = {
            "p1": "critical", "p2": "high", "p3": "medium", "p4": "low",
            "critical": "critical", "high": "high", "medium": "medium",
            "low": "low", "info": "informational", "informational": "informational"
        }
        return mapping.get(severity.lower(), "medium")

    def get_bounty_estimate(self, severity: str) -> dict:
        sev = self.normalize_severity(severity)
        min_b, max_b = BOUNTY_ESTIMATES.get(sev, (0, 0))
        return {"severity": sev, "min": min_b, "max": max_b, "avg": (min_b + max_b) // 2}
