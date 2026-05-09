"""ODIN-Hunter | PoC Generator"""
class PoCGenerator:
    def generate(self, finding): return finding.get("poc_steps", [])
