"""
 Auth Manager
Authenticates device connections so random devices can't talk to ODIN.
Uses JWT tokens for network devices and HMAC for hardware connections.
"""

import os
import time
import json
from typing import Optional


class AuthManager:

    def __init__(self, encryption: "EncryptionManager"):
        self._encryption = encryption
        self._secret     = os.getenv("COMMS_JWT_SECRET", self._default_secret())
        self._trusted    = self._load_trusted()

    def _default_secret(self) -> str:
        """Generate a stable secret from the encryption key."""
        import hashlib
        return hashlib.sha256(os.getenv("COMMS_SECRET", "odin").encode()).hexdigest()

    def _load_trusted(self) -> dict:
        """Load trusted device list."""
        from pathlib import Path
        trusted_file = Path(__file__).parent / "trusted_devices.json"
        if trusted_file.exists():
            try:
                with open(trusted_file) as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_trusted(self):
        from pathlib import Path
        trusted_file = Path(__file__).parent / "trusted_devices.json"
        with open(trusted_file, "w") as f:
            json.dump(self._trusted, f, indent=2)

    def generate_token(self, device_id: str, expires_hours: int = 8760) -> str:
        """
        Generate a JWT token for a device.
        expires_hours=8760 → 1 year (set to None for no expiry)
        """
        try:
            import jwt
            payload = {
                "device_id": device_id,
                "iat":       int(time.time()),
            }
            if expires_hours:
                payload["exp"] = int(time.time()) + (expires_hours * 3600)
            return jwt.encode(payload, self._secret, algorithm="HS256")
        except ImportError:
            # Fallback: simple HMAC token
            return self._encryption.generate_device_token(device_id)

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify a device token. Returns device_id on success, None on failure.
        """
        try:
            import jwt
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload.get("device_id")
        except Exception:
            return None

    def trust_device(self, device_id: str, name: str = None) -> str:
        """
        Add a device to the trusted list and return its token.
        """
        token = self.generate_token(device_id)
        self._trusted[device_id] = {
            "name":       name or device_id,
            "token":      token,
            "trusted_at": time.time()
        }
        self._save_trusted()
        return token

    def is_trusted(self, device_id: str) -> bool:
        return device_id in self._trusted

    def revoke(self, device_id: str):
        """Remove a device from trusted list."""
        if device_id in self._trusted:
            del self._trusted[device_id]
            self._save_trusted()

    def list_trusted(self) -> list:
        return [{"id": k, **v} for k, v in self._trusted.items()]
