"""
ODIN-COMMS — Communications Module
ODIN's radio tower. Manages all device communication protocols:
Bluetooth, BLE, WiFi, Zigbee, Z-Wave, IR, RF, and MQTT.

Every smart device in Charles's environment goes through here.
odin-core sends commands: "turn off the AC", "lock the door",
"what devices are nearby" — ODIN-COMMS handles the actual talking.

Startup sequence:
  1. Security layer initializes (encryption keys)
  2. Device registry loads known devices
  3. Protocol managers initialize available hardware
  4. Discovery scan runs (finds what's nearby)
  5. Auto-connect to known devices
  6. FastAPI comms API comes online (port 8003)
"""

import os
import asyncio
import uvicorn
import threading
import time
from pathlib import Path
load_dotenv(r"Z:\ODIN\ODIN_PRO\.env", override=True)

from security.encryption import EncryptionManager
from security.auth_manager import AuthManager
from discovery.device_registry import DeviceRegistry
from discovery.device_scanner import DeviceScanner
from discovery.auto_connect import AutoConnect
from api.comms_server import app, set_comms_state


# ── Global Comms State ────────────────────────────────────────────────────────

comms_state = {
    "protocols_online":  [],
    "known_devices":     [],
    "nearby_devices":    [],
    "connected_devices": [],
    "mqtt_connected":    False,
    "last_scan":         None,
    "pending_commands":  [],
}


async def boot_comms():
    print("📡  ODIN-COMMS booting up...")

    # ── Security ─────────────────────────────────────────────────────────────
    encryption = EncryptionManager()
    auth       = AuthManager(encryption)
    print("  ✓ Encryption and auth ready")

    # ── Device Registry ───────────────────────────────────────────────────────
    registry = DeviceRegistry()
    comms_state["known_devices"] = registry.get_all()
    print(f"  ✓ Device registry: {len(comms_state['known_devices'])} known devices")

    # ── Protocol Managers ────────────────────────────────────────────────────
    protocols_online = []

    # Bluetooth
    if os.getenv("BLUETOOTH_ENABLED", "true").lower() == "true":
        try:
            from protocols.bluetooth.bt_manager import BTManager
            bt = BTManager()
            if bt.is_available():
                protocols_online.append("bluetooth")
                print("  ✓ Bluetooth classic ready")
        except Exception as e:
            print(f"  ⚠ Bluetooth: {e}")

    # BLE
    if os.getenv("BLE_ENABLED", "true").lower() == "true":
        try:
            from protocols.bluetooth.ble_manager import BLEManager
            ble = BLEManager()
            protocols_online.append("ble")
            print("  ✓ BLE ready")
        except Exception as e:
            print(f"  ⚠ BLE: {e}")

    # WiFi/Network
    try:
        from protocols.wifi.wifi_manager import WiFiManager
        wifi = WiFiManager()
        protocols_online.append("wifi")
        print(f"  ✓ WiFi ready (IP: {wifi.get_local_ip()})")
    except Exception as e:
        print(f"  ⚠ WiFi: {e}")

    # MQTT
    if os.getenv("MQTT_ENABLED", "true").lower() == "true":
        try:
            from protocols.mqtt.mqtt_client import MQTTClient
            mqtt = MQTTClient()
            connected = mqtt.connect()
            if connected:
                comms_state["mqtt_connected"] = True
                protocols_online.append("mqtt")
                print(f"  ✓ MQTT connected ({os.getenv('MQTT_BROKER', 'localhost')})")
        except Exception as e:
            print(f"  ⚠ MQTT: {e}")

    # Zigbee (only if USB dongle detected)
    if os.getenv("ZIGBEE_ENABLED", "false").lower() == "true":
        try:
            from protocols.zigbee.zigbee_manager import ZigbeeManager
            zigbee = ZigbeeManager()
            if zigbee.is_available():
                protocols_online.append("zigbee")
                print("  ✓ Zigbee dongle detected")
        except Exception as e:
            print(f"  ⚠ Zigbee: {e}")

    # Z-Wave (only if USB stick detected)
    if os.getenv("ZWAVE_ENABLED", "false").lower() == "true":
        try:
            from protocols.zwave.zwave_manager import ZWaveManager
            zwave = ZWaveManager()
            if zwave.is_available():
                protocols_online.append("zwave")
                print("  ✓ Z-Wave stick detected")
        except Exception as e:
            print(f"  ⚠ Z-Wave: {e}")

    # IR
    if os.getenv("IR_ENABLED", "false").lower() == "true":
        try:
            from protocols.infrared.ir_manager import IRManager
            ir = IRManager()
            protocols_online.append("ir")
            print("  ✓ IR blaster ready")
        except Exception as e:
            print(f"  ⚠ IR: {e}")

    # RF
    if os.getenv("RF_ENABLED", "false").lower() == "true":
        try:
            from protocols.rf.rf_manager import RFManager
            rf = RFManager()
            protocols_online.append("rf")
            print("  ✓ RF transceiver ready")
        except Exception as e:
            print(f"  ⚠ RF: {e}")

    comms_state["protocols_online"] = protocols_online
    print(f"  📡 Protocols online: {', '.join(protocols_online) or 'none'}")

    # ── Discovery + Auto-Connect ──────────────────────────────────────────────
    scanner      = DeviceScanner(protocols_online)
    auto_connect = AutoConnect(registry, scanner)

    # Initial scan in background (don't block startup)
    threading.Thread(
        target=_run_initial_scan,
        args=(scanner, auto_connect, comms_state),
        daemon=True
    ).start()

    set_comms_state(comms_state)
    actual_port = int(os.getenv("COMMS_PORT", 8003))
    print(f"📡  ODIN-COMMS online → http://localhost:{actual_port}")


def _run_initial_scan(scanner, auto_connect, state):
    time.sleep(2)  # Let startup finish
    print("  🔍 Running initial device scan...")
    devices = scanner.scan_all()
    state["nearby_devices"] = devices
    state["last_scan"]      = time.time()
    print(f"  🔍 Found {len(devices)} nearby devices")

    # Auto-connect to known devices
    connected = auto_connect.connect_known(devices)
    state["connected_devices"] = connected
    print(f"  🔗 Connected to {len(connected)} known devices")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(boot_comms())

    uvicorn.run(
        "api.comms_server:app",
        host="0.0.0.0",
        port=int(os.getenv("COMMS_PORT", 8003)),
        reload=False,
        log_level="warning"
    )
