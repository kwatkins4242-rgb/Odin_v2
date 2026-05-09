"""
COMMS — Device Registry
The master database of every device ODIN knows about.
Persisted to device_registry.json so ODIN remembers devices across restarts.

Each device entry:
  id:           friendly_id (e.g. "living_room_ac", "front_door_lock")
  name:         Human-readable name
  protocol:     bluetooth | ble | wifi | mqtt | zigbee | zwave | ir | rf
  room:         Room location
  type:         light | thermostat | lock | plug | sensor | speaker | tv | ac | fan
  address:      IP / MAC / IEEE / topic depending on protocol
  topic:        MQTT command topic (if MQTT device)
  state_topic:  MQTT state topic (device reports its state here)
  last_state:   Most recent known state
  last_seen:    Unix timestamp
"""

import json
import time
from pathlib import Path
from typing import Optional, List

REGISTRY_FILE = Path(__file__).parent / "device_registry.json"


class DeviceRegistry:

    def __init__(self):
        self._devices = self._load()

    def _load(self) -> list:
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE) as f:
                    return json.load(f)
            except:
                pass
        # Default seed devices — common home setup
        # Charles can edit this or ODIN will auto-populate via discovery
        return [
            {
                "id":          "living_room_lights",
                "name":        "Living Room Lights",
                "protocol":    "mqtt",
                "type":        "light",
                "room":        "living_room",
                "topic":       "cmnd/living_room_lights/POWER",
                "state_topic": "stat/living_room_lights/POWER",
                "last_state":  None,
                "last_seen":   None
            },
            {
                "id":          "bedroom_ac",
                "name":        "Bedroom AC",
                "protocol":    "ir",
                "type":        "ac",
                "room":        "bedroom",
                "device_type": "ac",
                "last_state":  None,
                "last_seen":   None
            },
            {
                "id":          "tv",
                "name":        "TV",
                "protocol":    "ir",
                "type":        "tv",
                "room":        "living_room",
                "device_type": "tv",
                "last_state":  None,
                "last_seen":   None
            },
        ]

    def _save(self):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(self._devices, f, indent=2)

    def get(self, device_id: str) -> Optional[dict]:
        for d in self._devices:
            if d["id"] == device_id:
                return d
        return None

    def get_by_name(self, name: str) -> Optional[dict]:
        """Find device by name (case-insensitive, partial match)."""
        name_lower = name.lower()
        for d in self._devices:
            if name_lower in d["name"].lower() or name_lower in d["id"].lower():
                return d
        return None

    def get_all(self) -> List[dict]:
        return self._devices.copy()

    def get_by_room(self, room: str) -> List[dict]:
        return [d for d in self._devices if d.get("room", "").lower() == room.lower()]

    def get_by_type(self, device_type: str) -> List[dict]:
        return [d for d in self._devices if d.get("type", "").lower() == device_type.lower()]

    def get_by_protocol(self, protocol: str) -> List[dict]:
        return [d for d in self._devices if d.get("protocol", "").lower() == protocol.lower()]

    def add(self, device: dict) -> bool:
        """Add a new device. device must have 'id' and 'name' at minimum."""
        if not device.get("id") or not device.get("name"):
            return False
        # Don't duplicate
        if self.get(device["id"]):
            return self.update(device)
        device.setdefault("last_seen", None)
        device.setdefault("last_state", None)
        self._devices.append(device)
        self._save()
        return True

    def update(self, device: dict) -> bool:
        """Update an existing device."""
        for i, d in enumerate(self._devices):
            if d["id"] == device["id"]:
                self._devices[i].update(device)
                self._devices[i]["last_seen"] = time.time()
                self._save()
                return True
        return False

    def remove(self, device_id: str) -> bool:
        before = len(self._devices)
        self._devices = [d for d in self._devices if d["id"] != device_id]
        if len(self._devices) < before:
            self._save()
            return True
        return False

    def mark_seen(self, device_id: str, state: dict = None):
        """Update last_seen timestamp (and optionally last_state)."""
        for d in self._devices:
            if d["id"] == device_id:
                d["last_seen"] = time.time()
                if state is not None:
                    d["last_state"] = state
                self._save()
                break

    def search(self, query: str) -> List[dict]:
        """Free-text search across device names, rooms, types."""
        q = query.lower()
        return [
            d for d in self._devices
            if q in d.get("name", "").lower()
            or q in d.get("room", "").lower()
            or q in d.get("type", "").lower()
            or q in d.get("id", "").lower()
        ]