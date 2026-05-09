"""
ODIN-Hunter | Scope Checker
CRITICAL: This runs before ANY scan. Out of scope = full stop.
"""

import tldextract
import re
from platforms.platform_manager import PlatformManager

class ScopeChecker:
    def __init__(self):
        self.platform_mgr = PlatformManager()

    async def check(self, target: str, program_id: str, platform: str) -> bool:
        """
        Returns True if target is in scope for this program.
        Returns False and logs warning if out of scope.
        """
        if not target or not program_id:
            print(f"[ScopeChecker] BLOCKED: Missing target or program_id")
            return False

        try:
            scope_list = await self.platform_mgr.get_scope(platform, program_id)
            if not scope_list:
                print(f"[ScopeChecker] WARNING: Could not fetch scope for {program_id} — defaulting to BLOCKED")
                return False

            return self._target_in_scope(target, scope_list)

        except Exception as e:
            print(f"[ScopeChecker] ERROR: {e} — defaulting to BLOCKED")
            return False

    def _target_in_scope(self, target: str, scope_list: list) -> bool:
        """Check if target matches any in-scope entry"""
        target_ext = tldextract.extract(target)
        target_domain = f"{target_ext.domain}.{target_ext.suffix}"

        for scope_entry in scope_list:
            entry = scope_entry.get("value", "").strip()
            scope_type = scope_entry.get("type", "url")

            if scope_type in ["url", "domain", "wildcard"]:
                # Wildcard: *.example.com
                if entry.startswith("*."):
                    base = entry[2:]
                    if target.endswith(base) or target == base:
                        print(f"[ScopeChecker] ✅ IN SCOPE (wildcard): {target} matches {entry}")
                        return True
                # Exact domain match
                elif entry == target or entry == target_domain:
                    print(f"[ScopeChecker] ✅ IN SCOPE: {target}")
                    return True
                # Subdomain match
                elif target.endswith(f".{entry}"):
                    print(f"[ScopeChecker] ✅ IN SCOPE (subdomain): {target} under {entry}")
                    return True

            elif scope_type == "cidr":
                # IP range check would go here
                pass

        print(f"[ScopeChecker] ❌ OUT OF SCOPE: {target} — HUNT BLOCKED")
        return False

    def check_out_of_scope(self, target: str, out_of_scope_list: list) -> bool:
        """Returns True if target is explicitly OUT of scope"""
        for entry in out_of_scope_list:
            value = entry.get("value", "").strip()
            if value in target or target == value:
                print(f"[ScopeChecker] ❌ EXPLICITLY OUT OF SCOPE: {target}")
                return True
        return False

    def is_safe_target(self, target: str) -> bool:
        """Basic sanity checks on the target itself"""
        # Never scan localhost or internal IPs
        blocked_patterns = [
            r"^localhost$",
            r"^127\.",
            r"^192\.168\.",
            r"^10\.",
            r"^172\.(1[6-9]|2[0-9]|3[01])\.",
            r"^0\.0\.0\.0$",
            r"^::1$"
        ]
        for pattern in blocked_patterns:
            if re.match(pattern, target):
                print(f"[ScopeChecker] ❌ BLOCKED internal target: {target}")
                return False
        return True
