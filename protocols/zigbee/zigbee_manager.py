"""
COMMS — Zigbee Manager
Controls Zigbee smart home devices: Philips Hue, IKEA Tradfri, smart plugs, sensors.
Requires a USB Zigbee coordinator dongle (~$15 SONOFF or HUSBZB-1).

Zigbee is the best protocol for lights and simple sensors — low power, reliable mesh.
"""

import os
from typing import Optional, List

ZIGBEE_PORT = os.getenv("ZIGBEE_USB_PORT", "/dev/ttyUSB0")
ZIGBEE_BAUD = int(os.getenv("ZIGBEE_BAUD", "115200"))


class ZigbeeManager:

    def __init__(self):
        self._app      = None
        self._devices  = {}
        self._available = self._detect_dongle()

    def _detect_dongle(self) -> bool:
        """Check if Zigbee USB dongle is connected."""
        return os.path.exists(ZIGBEE_PORT)

    def is_available(self) -> bool:
        return self._available

    async def start(self):
        """Initialize Zigbee coordinator and start network."""
        if not self._available:
            print("[Zigbee] No USB dongle detected at", ZIGBEE_PORT)
            return False
        try:
            import zigpy_znp.zigbee.application as znp_app
            from zigpy.config import CONF_DEVICE

            config = {
                CONF_DEVICE: {
                    "path": ZIGBEE_PORT,
                    "baudrate": ZIGBEE_BAUD
                }
            }
            self._app = await znp_app.ControllerApplication.new(config, auto_form=True)
            print(f"[Zigbee] Network started on {ZIGBEE_PORT}")
            return True
        except ImportError:
            print("[Zigbee] zigpy-znp not installed")
            return False
        except Exception as e:
            print(f"[Zigbee] Start error: {e}")
            return False

    async def get_devices(self) -> List[dict]:
        """Get all paired Zigbee devices."""
        if not self._app:
            return []
        devices = []
        for ieee, device in self._app.devices.items():
            devices.append({
                "ieee":      str(ieee),
                "nwk":       device.nwk,
                "model":     getattr(device, "model", "unknown"),
                "manufacturer": getattr(device, "manufacturer", "unknown"),
                "protocol":  "zigbee"
            })
        return devices

    async def set_light(self, ieee: str, on: bool = True,
                        brightness: Optional[int] = None,
                        color_temp: Optional[int] = None) -> bool:
        """
        Control a Zigbee light.
        brightness: 0-254
        color_temp: 153 (cool) - 500 (warm)
        """
        if not self._app:
            return False
        try:
            device  = self._app.get_device(ieee=ieee)
            cluster = device.endpoints[1].in_clusters.get(0x0006)  # On/Off cluster
            if cluster:
                await cluster.on() if on else await cluster.off()

            if brightness is not None:
                level_cluster = device.endpoints[1].in_clusters.get(0x0008)  # Level control
                if level_cluster:
                    await level_cluster.move_to_level_with_on_off(brightness, 5)

            return True
        except Exception as e:
            print(f"[Zigbee] set_light error: {e}")
            return False

    async def pair_device(self, timeout_sec: int = 60) -> Optional[dict]:
        """Open Zigbee network for pairing. Put device in pairing mode."""
        if not self._app:
            return None
        print(f"[Zigbee] Pairing window open for {timeout_sec}s — put device in pairing mode")
        await self._app.permit(timeout_sec)
        return {"status": "pairing_open", "timeout": timeout_sec}
