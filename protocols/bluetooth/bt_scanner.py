"""
COMMS — Bluetooth Scanner
Unified scan that hits both Bluetooth Classic and BLE simultaneously.
Also detects proximity — is a known device within range?
"""

import asyncio
from typing import List


class BTScanner:

    def scan_all(self) -> List[dict]:
        """Scan both BT Classic and BLE, return combined results."""
        results = []

        # BLE scan (async)
        try:
            from protocols.bluetooth.ble_manager import BLEManager
            ble     = BLEManager()
            ble_devices = asyncio.run(ble.scan(duration_sec=5))
            results.extend(ble_devices)
        except Exception as e:
            print(f"[BTScanner] BLE scan error: {e}")

        # BT Classic scan
        try:
            from protocols.bluetooth.bt_manager import BTManager
            bt      = BTManager()
            bt_devices = bt.scan(duration_sec=8)
            results.extend(bt_devices)
        except Exception as e:
            print(f"[BTScanner] BT Classic scan error: {e}")

        # Deduplicate by address (in case a device shows on both)
        seen    = set()
        unique  = []
        for d in results:
            if d["address"] not in seen:
                seen.add(d["address"])
                unique.append(d)

        return unique

    def is_device_nearby(self, address: str, rssi_threshold: int = -80) -> bool:
        """
        Check if a specific BLE device is in range.
        rssi_threshold: -60 = very close, -80 = reasonable range, -100 = edge of range
        Used for: "is Charles's phone nearby?" / "is the lock in range?"
        """
        try:
            from protocols.bluetooth.ble_manager import BLEManager
            ble     = BLEManager()
            devices = asyncio.run(ble.scan(duration_sec=3))
            for d in devices:
                if d["address"].upper() == address.upper():
                    return d.get("rssi", -100) >= rssi_threshold
        except Exception:
            pass
        return False

    def get_rssi(self, address: str) -> int:
        """Get signal strength of a specific BLE device (-100 to 0 dBm)."""
        try:
            from protocols.bluetooth.ble_manager import BLEManager
            ble     = BLEManager()
            devices = asyncio.run(ble.scan(duration_sec=3))
            for d in devices:
                if d["address"].upper() == address.upper():
                    return d.get("rssi", -100)
        except Exception:
            pass
        return -100
