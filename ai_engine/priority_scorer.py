"""ODIN-Hunter | Priority Scorer"""
class PriorityScorer:
    def score(self, finding: dict) -> float:
        sev_scores = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2, "informational": 0.05}
        base = sev_scores.get(finding.get("severity", "medium"), 0.5)
        confidence = finding.get("confidence", 0.7)
        bounty_max = finding.get("estimated_bounty_max", 500)
        return round(base * confidence * (1 + bounty_max / 10000), 3)
