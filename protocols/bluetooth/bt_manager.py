"""
COMMS — Bluetooth Classic Manager
Handles Bluetooth Classic connections.
Used for: audio devices, older peripherals, phones, serial devices.

BLE (modern) is handled separately in ble_manager.py.
This handles the old-school Bluetooth that your headphones and speakers use.
"""

import os
import time
from typing import Optional, List

BT_TIMEOUT = int(os.getenv("BT_TIMEOUT", "10"))


class BTManager:

    def __init__(self):
        self._available = False
        self._socket    = None
        self._check_availability()

    def _check_availability(self):
        try:
            import bluetooth
            # Quick test — will raise if bluetooth not available
            bluetooth.lookup_name("00:00:00:00:00:00", timeout=1)
            self._available = True
        except ImportError:
            pass
        except Exception:
            # lookup_name throwing means BT hardware IS present but address invalid — that's fine
            self._available = True

    def is_available(self) -> bool:
        return self._available

    def scan(self, duration_sec: int = 8) -> List[dict]:
        """
        Scan for nearby Bluetooth Classic devices.
        Returns list of {address, name}.
        """
        if not self._available:
            return []
        try:
            import bluetooth
            print(f"[BT] Scanning ({duration_sec}s)...")
            nearby = bluetooth.discover_devices(
                duration=duration_sec,
                lookup_names=True,
                lookup_class=False,
                flush_cache=True
            )
            devices = [{"address": addr, "name": name or "Unknown", "protocol": "bluetooth"}
                       for addr, name in nearby]
            print(f"[BT] Found {len(devices)} devices")
            return devices
        except Exception as e:
            print(f"[BT] Scan error: {e}")
            return []

    def connect(self, address: str, port: int = 1) -> bool:
        """Connect to a Bluetooth device via RFCOMM."""
        if not self._available:
            return False
        try:
            import bluetooth
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((address, port))
            self._socket = sock
            print(f"[BT] Connected to {address}")
            return True
        except Exception as e:
            print(f"[BT] Connect error ({address}): {e}")
            return False

    def send_command(self, address: str, command: str, value: Optional[str] = None) -> dict:
        """Send a command string to a connected BT device."""
        payload = f"{command}:{value}" if value else command
        try:
            if not self._socket:
                self.connect(address)
            if self._socket:
                self._socket.send(payload.encode())
                return {"sent": payload}
        except Exception as e:
            print(f"[BT] Send error: {e}")
        return {"error": "send failed"}

    def disconnect(self):
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None

    def get_paired_devices(self) -> List[dict]:
        """Get list of already paired (trusted) devices."""
        try:
            import subprocess
            result = subprocess.run(
                ["bluetoothctl", "paired-devices"],
                capture_output=True, text=True
            )
            devices = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    devices.append({"address": parts[1], "name": parts[2], "protocol": "bluetooth", "paired": True})
            return devices
        except:
            return []
