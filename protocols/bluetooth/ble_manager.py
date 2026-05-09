"""
COMMS — BLE Manager (Bluetooth Low Energy)
Handles BLE devices: smart bulbs, sensors, locks, fitness trackers, beacons.
Uses bleak — the best cross-platform BLE library for Python.

BLE devices communicate via Services + Characteristics (UUID-based).
ODIN reads sensor data and writes control commands via these UUIDs.
"""

import asyncio
import os
from typing import Optional, List

BLE_SCAN_SEC = int(os.getenv("BLE_SCAN_SECONDS", "5"))


class BLEManager:

    async def scan(self, duration_sec: int = BLE_SCAN_SEC) -> List[dict]:
        """
        Scan for nearby BLE devices.
        Returns list of {address, name, rssi, protocol}.
        """
        try:
            from bleak import BleakScanner
            print(f"[BLE] Scanning ({duration_sec}s)...")
            devices = await BleakScanner.discover(timeout=duration_sec)
            result  = []
            for d in devices:
                result.append({
                    "address":  d.address,
                    "name":     d.name or "Unknown BLE Device",
                    "rssi":     d.rssi,
                    "protocol": "ble",
                    "metadata": d.metadata
                })
            print(f"[BLE] Found {len(result)} BLE devices")
            return result
        except ImportError:
            print("[BLE] bleak not installed")
            return []
        except Exception as e:
            print(f"[BLE] Scan error: {e}")
            return []

    def scan_sync(self, duration_sec: int = BLE_SCAN_SEC) -> List[dict]:
        """Synchronous wrapper for scan."""
        return asyncio.run(self.scan(duration_sec))

    async def read_characteristic(self, address: str, char_uuid: str) -> Optional[bytes]:
        """Read a BLE characteristic value (e.g. sensor reading, battery level)."""
        try:
            from bleak import BleakClient
            async with BleakClient(address) as client:
                value = await client.read_gatt_char(char_uuid)
                return value
        except Exception as e:
            print(f"[BLE] Read error ({address}, {char_uuid}): {e}")
            return None

    async def write_characteristic(self, address: str, char_uuid: str, data: bytes) -> bool:
        """Write to a BLE characteristic (send a command to the device)."""
        try:
            from bleak import BleakClient
            async with BleakClient(address) as client:
                await client.write_gatt_char(char_uuid, data)
                return True
        except Exception as e:
            print(f"[BLE] Write error ({address}, {char_uuid}): {e}")
            return False

    async def send_command(self, address: str, char_uuid: str,
                           command: str, value: Optional[str] = None) -> dict:
        """
        High-level command sender.
        Encodes command+value as bytes and writes to device characteristic.
        """
        payload = f"{command}:{value}" if value else command
        success = await self.write_characteristic(address, char_uuid, payload.encode())
        return {"sent": payload, "success": success}

    async def get_services(self, address: str) -> List[dict]:
        """
        List all services and characteristics of a BLE device.
        Useful for figuring out what an unknown device can do.
        """
        try:
            from bleak import BleakClient
            services = []
            async with BleakClient(address) as client:
                for service in client.services:
                    chars = []
                    for char in service.characteristics:
                        chars.append({
                            "uuid":       str(char.uuid),
                            "properties": char.properties,
                            "description": char.description
                        })
                    services.append({
                        "uuid":            str(service.uuid),
                        "description":     service.description,
                        "characteristics": chars
                    })
            return services
        except Exception as e:
            print(f"[BLE] get_services error: {e}")
            return []

    async def subscribe_notifications(self, address: str, char_uuid: str, callback):
        """
        Subscribe to continuous notifications from a BLE characteristic.
        Used for sensor data, heart rate monitors, proximity beacons, etc.
        callback(sender, data) is called whenever the device sends a notification.
        """
        try:
            from bleak import BleakClient
            print(f"[BLE] Subscribing to {address} / {char_uuid}")
            async with BleakClient(address) as client:
                await client.start_notify(char_uuid, callback)
                # Keep alive until cancelled
                await asyncio.sleep(float("inf"))
        except Exception as e:
            print(f"[BLE] Notification error: {e}")
