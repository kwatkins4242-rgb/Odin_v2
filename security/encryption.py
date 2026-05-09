"""
 Encryption Manager
Encrypts all device communication payloads.
ODIN's comms stay private even on a local network.
Uses Fernet (AES-128 CBC + HMAC) — symmetric, fast, secure enough for home use.
"""

import os
import base64
from pathlib import Path
from typing import Optional

KEY_FILE = Path(__file__).parent / ".comms_key"


class EncryptionManager:

    def __init__(self):
        self._key    = self._load_or_create_key()
        self._fernet = None
        self._init_cipher()

    def _load_or_create_key(self) -> bytes:
        if KEY_FILE.exists():
            with open(KEY_FILE, "rb") as f:
                return f.read()
        # Generate new key
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        print("[Encryption] Generated new encryption key")
        return key

    def _init_cipher(self):
        try:
            from cryptography.fernet import Fernet
            self._fernet = Fernet(self._key)
        except ImportError:
            print("[Encryption] cryptography not installed — comms unencrypted")

    def encrypt(self, data: str) -> str:
        """Encrypt a string. Returns base64-encoded ciphertext."""
        if not self._fernet:
            return data
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """Decrypt a ciphertext string. Returns original string or None."""
        if not self._fernet:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return None

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dict as JSON."""
        import json
        return self.encrypt(json.dumps(data))

    def decrypt_dict(self, ciphertext: str) -> Optional[dict]:
        """Decrypt to dict."""
        import json
        plain = self.decrypt(ciphertext)
        if plain:
            try:
                return json.loads(plain)
            except:
                pass
        return None

    def generate_device_token(self, device_id: str) -> str:
        """Generate a short auth token for a device."""
        import hashlib
        secret = os.getenv("COMMS_SECRET", "odin-secret")
        return hashlib.sha256(f"{device_id}:{secret}".encode()).hexdigest()[:16]
