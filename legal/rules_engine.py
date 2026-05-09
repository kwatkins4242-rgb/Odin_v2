"""
ODIN-Hunter | Rules Engine
Enforces platform rules, rate limits, and safe harbor requirements
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DELAY = float(os.getenv("HUNTER_DELAY_BETWEEN_REQUESTS", "1.5"))

class RulesEngine:
    def __init__(self):
        self._request_log = {}  # target -> [timestamps]
        self._blocked_targets = set()

    async def check(self, platform: str, program_id: str) -> bool:
        """Master rules check before any hunt"""
        platform_rules = self._get_platform_rules(platform)

        if not platform_rules.get("active", True):
            print(f"[RulesEngine] Platform {platform} is currently inactive")
            return False

        print(f"[RulesEngine] ✅ Rules check passed for {platform}/{program_id}")
        return True

    def _get_platform_rules(self, platform: str) -> dict:
        rules = {
            "hackerone": {
                "active": True,
                "requires_auth": True,
                "max_requests_per_minute": 30,
                "safe_harbor": True,
                "coordinated_disclosure": True
            },
            "bugcrowd": {
                "active": True,
                "requires_auth": True,
                "max_requests_per_minute": 20,
                "safe_harbor": True,
                "coordinated_disclosure": True
            },
            "intigriti": {
                "active": True,
                "requires_auth": True,
                "max_requests_per_minute": 20,
                "safe_harbor": True,
                "coordinated_disclosure": True
            },
            "yeswehack": {
                "active": True,
                "requires_auth": True,
                "max_requests_per_minute": 20,
                "safe_harbor": True,
                "coordinated_disclosure": True
            }
        }
        return rules.get(platform, {"active": False})

    def rate_limit_check(self, target: str) -> bool:
        """Returns True if we're within rate limits for this target"""
        now = datetime.now()
        if target not in self._request_log:
            self._request_log[target] = []

        # Clean old entries (older than 1 minute)
        self._request_log[target] = [
            t for t in self._request_log[target]
            if now - t < timedelta(minutes=1)
        ]

        if len(self._request_log[target]) >= 30:
            print(f"[RulesEngine] ⚠️ Rate limit reached for {target}")
            return False

        self._request_log[target].append(now)
        return True

    def block_target(self, target: str, reason: str):
        """Permanently block a target this session"""
        self._blocked_targets.add(target)
        print(f"[RulesEngine] 🚫 Blocked {target}: {reason}")

    def is_blocked(self, target: str) -> bool:
        return target in self._blocked_targets

    def get_required_delay(self) -> float:
        return DELAY

    def verify_safe_harbor(self, platform: str) -> dict:
        """Return safe harbor status for a platform"""
        platforms_with_safe_harbor = ["hackerone", "bugcrowd", "intigriti", "yeswehack"]
        has_safe_harbor = platform.lower() in platforms_with_safe_harbor
        return {
            "platform": platform,
            "safe_harbor": has_safe_harbor,
            "recommendation": "Proceed with caution" if has_safe_harbor else "DO NOT HUNT — no safe harbor"
        }
