"""
COMMS — Auto Connect
On startup and periodically, connects to all known devices automatically.
ODIN never loses connection to the devices it knows about.
"""

import time
import threading
from typing import List

RECONNECT_INTERVAL_MIN = 5  # Check every 5 minutes


class AutoConnect:

    def __init__(self, registry: "DeviceRegistry", scanner: "DeviceScanner"):
        self._registry = registry
        self._scanner  = scanner
        self._running  = False

    def connect_known(self, nearby_devices: List[dict]) -> List[dict]:
        """
        Cross-reference nearby devices against known registry.
        Connect to known devices that are in range.
        Returns list of successfully connected devices.
        """
        connected = []
        nearby_addresses = {
            (d.get("address") or d.get("ip") or "").upper()
            for d in nearby_devices
        }

        for known in self._registry.get_all():
            address = (known.get("address") or known.get("ip") or "").upper()
            if not address:
                continue

            # Is this known device nearby?
            if address in nearby_addresses or known.get("protocol") in ("mqtt", "wifi"):
                result = self._try_connect(known)
                if result:
                    connected.append(known)
                    self._registry.mark_seen(known["id"])

        return connected

    def _try_connect(self, device: dict) -> bool:
        """Attempt to connect to a single device based on its protocol."""
        protocol = device.get("protocol", "")
        try:
            if protocol == "mqtt":
                # MQTT devices are always "connected" through the broker
                return True
            elif protocol == "bluetooth":
                from protocols.bluetooth.bt_manager import BTManager
                bt = BTManager()
                return bt.connect(device["address"])
            elif protocol == "ble":
                # BLE connects on demand — mark as available
                return True
            elif protocol in ("ir", "rf", "zigbee", "zwave"):
                # These are fire-and-forget — always available if hardware is present
                return True
        except Exception as e:
            print(f"[AutoConnect] Failed {device.get('id')}: {e}")
        return False

    def start_background_reconnect(self):
        """Start background thread that periodically reconnects dropped devices."""
        self._running = True
        t = threading.Thread(target=self._reconnect_loop, daemon=True)
        t.start()

    def _reconnect_loop(self):
        while self._running:
            time.sleep(RECONNECT_INTERVAL_MIN * 60)
            try:
                nearby = self._scanner.scan_all()
                self.connect_known(nearby)
            except Exception as e:
                print(f"[AutoConnect] Reconnect error: {e}")

    def stop(self):
        self._running = False