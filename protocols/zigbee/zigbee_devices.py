"""
COMMS — Zigbee Device Registry
Tracks known Zigbee devices with friendly names and capabilities.
"""

import json
from pathlib import Path

ZIGBEE_DEVICES_FILE = Path(__file__).parent / "zigbee_devices.json"


class ZigbeeDevices:

    def __init__(self):
        self._devices = self._load()

    def _load(self) -> list:
        if ZIGBEE_DEVICES_FILE.exists():
            with open(ZIGBEE_DEVICES_FILE) as f:
                return json.load(f)
        return []

    def _save(self):
        with open(ZIGBEE_DEVICES_FILE, "w") as f:
            json.dump(self._devices, f, indent=2)

    def register(self, ieee: str, name: str, type_: str, room: str = None):
        """Register a Zigbee device with a friendly name."""
        entry = {
            "ieee": ieee, "name": name, "type": type_,
            "room": room, "protocol": "zigbee"
        }
        self._devices = [d for d in self._devices if d["ieee"] != ieee]
        self._devices.append(entry)
        self._save()

    def get_by_name(self, name: str) -> dict:
        for d in self._devices:
            if d["name"].lower() == name.lower():
                return d
        return {}

    def get_all(self) -> list:
        return self._devices
