"""ODIN-Hunter | Safe Harbor Checker"""

class SafeHarborChecker:
    PLATFORMS_WITH_SAFE_HARBOR = ["hackerone", "bugcrowd", "intigriti", "yeswehack"]

    def check(self, platform: str) -> dict:
        has_harbor = platform.lower() in self.PLATFORMS_WITH_SAFE_HARBOR
        return {
            "platform": platform,
            "safe_harbor": has_harbor,
            "recommendation": "Safe to hunt" if has_harbor else "⚠️ No safe harbor — research legal status first"
        }
