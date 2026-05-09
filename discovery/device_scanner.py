"""
COMMS — Device Scanner
Master scanner that hits all active protocols simultaneously.
odin-core calls: "scan for devices" → this runs everything in parallel.
"""

import concurrent.futures
import time
from typing import List, Optional


class DeviceScanner:

    def __init__(self, protocols_online: List[str]):
        self._protocols = protocols_online

    def scan_all(self, protocols: Optional[List[str]] = None) -> List[dict]:
        """
        Scan all active protocols in parallel.
        Returns deduplicated list of discovered devices.
        """
        targets = protocols or self._protocols
        if not targets:
            return []

        print(f"[Scanner] Scanning protocols: {', '.join(targets)}")
        all_devices = []

        # Run scans concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {}
            if "bluetooth" in targets or "ble" in targets:
                futures["bt"] = pool.submit(self._scan_bluetooth)
            if "wifi" in targets:
                futures["wifi"] = pool.submit(self._scan_wifi)
                futures["mdns"] = pool.submit(self._scan_mdns)

            for key, future in futures.items():
                try:
                    result = future.result(timeout=15)
                    all_devices.extend(result)
                except Exception as e:
                    print(f"[Scanner] {key} scan error: {e}")

        # Deduplicate
        seen     = set()
        unique   = []
        for d in all_devices:
            key = d.get("address") or d.get("ip") or d.get("name", "")
            if key and key not in seen:
                seen.add(key)
                d["discovered_at"] = time.time()
                unique.append(d)

        print(f"[Scanner] Found {len(unique)} unique devices")
        return unique

    def _scan_bluetooth(self) -> List[dict]:
        try:
            from protocols.bluetooth.bt_scanner import BTScanner
            return BTScanner().scan_all()
        except Exception as e:
            print(f"[Scanner] BT error: {e}")
            return []

    def _scan_wifi(self) -> List[dict]:
        try:
            from protocols.wifi.network_scanner import NetworkScanner
            return NetworkScanner().scan()
        except Exception as e:
            print(f"[Scanner] WiFi error: {e}")
            return []

    def _scan_mdns(self) -> List[dict]:
        try:
            from protocols.wifi.network_scanner import MDNSDiscovery
            return MDNSDiscovery().discover()
        except Exception as e:
            print(f"[Scanner] mDNS error: {e}")
            return []

    def identify_device(self, device: dict) -> dict:
        """
        Try to identify what type of device something is based on its properties.
        Name/hostname patterns → device type classification.
        """
        name      = (device.get("name") or device.get("hostname") or "").lower()
        TYPE_HINTS = {
            "bulb":      "light",  "light": "light", "hue": "light", "ikea": "light",
            "lock":      "lock",   "door":  "lock",
            "therm":     "thermostat", "nest": "thermostat", "ecobee": "thermostat",
            "plug":      "plug",   "outlet": "plug", "switch": "plug",
            "cam":       "camera", "camera": "camera",
            "sensor":    "sensor", "temp":   "sensor", "motion": "sensor",
            "speaker":   "speaker", "echo":  "speaker", "home":  "speaker",
            "tv":        "tv",     "roku":   "tv",    "fire":  "tv",
            "print":     "printer",
        }
        for hint, dtype in TYPE_HINTS.items():
            if hint in name:
                device["type"] = dtype
                break
        return device
