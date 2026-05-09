"""
COMMS — Z-Wave Manager
Controls Z-Wave devices: door locks, thermostats, light switches, garage doors.
Z-Wave is better than Zigbee for locks and critical devices — more reliable, longer range.
Requires USB Z-Wave controller stick (Aeotec Z-Stick ~$45).
"""

import os
from typing import Optional, List

ZWAVE_PORT = os.getenv("ZWAVE_USB_PORT", "/dev/ttyUSB1")


class ZWaveManager:

    def __init__(self):
        self._network   = None
        self._available = self._detect_stick()

    def _detect_stick(self) -> bool:
        return os.path.exists(ZWAVE_PORT)

    def is_available(self) -> bool:
        return self._available

    def start(self) -> bool:
        """Initialize Z-Wave network."""
        if not self._available:
            print(f"[ZWave] No controller at {ZWAVE_PORT}")
            return False
        try:
            from openzwave.network import ZWaveNetwork
            from openzwave.option import ZWaveOption

            options = ZWaveOption(ZWAVE_PORT, config_path="/usr/share/openzwave/config")
            options.set_console_output(False)
            options.lock()

            self._network = ZWaveNetwork(options)
            print("[ZWave] Network starting...")
            return True
        except ImportError:
            print("[ZWave] python-openzwave not installed")
            return False
        except Exception as e:
            print(f"[ZWave] Start error: {e}")
            return False

    def get_nodes(self) -> List[dict]:
        """Get all Z-Wave nodes."""
        if not self._network:
            return []
        nodes = []
        for node_id, node in self._network.nodes.items():
            nodes.append({
                "id":           node_id,
                "name":         node.name or f"Node {node_id}",
                "product_name": node.product_name,
                "is_ready":     node.is_ready,
                "protocol":     "zwave"
            })
        return nodes

    def set_value(self, node_id: int, value_id: int, val) -> bool:
        """Set a Z-Wave value (generic command)."""
        if not self._network:
            return False
        try:
            node  = self._network.nodes[node_id]
            value = node.values[value_id]
            return node.set_field(value, val)
        except Exception as e:
            print(f"[ZWave] set_value error: {e}")
            return False

    def lock_door(self, node_id: int) -> bool:
        """Lock a Z-Wave door lock."""
        return self.set_value(node_id, 0, True)

    def unlock_door(self, node_id: int) -> bool:
        """Unlock a Z-Wave door lock."""
        return self.set_value(node_id, 0, False)

    def set_thermostat(self, node_id: int, temp_f: float) -> bool:
        """Set Z-Wave thermostat temperature."""
        return self.set_value(node_id, 1, temp_f)


class ZWaveNetwork:
    """Helper for Z-Wave network state tracking."""

    def __init__(self):
        self._state = "stopped"

    def get_status(self) -> dict:
        return {"state": self._state}
