"""ODIN-Hunter | False Positive Filter"""
class FalsePositiveFilter:
    def filter(self, findings: list) -> list:
        return [f for f in findings if f.get("confidence", 0) >= 0.6]
