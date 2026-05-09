"""
COMMS — MQTT Broker Manager
Manages the local Mosquitto broker installation.
ODIN runs its own broker so all smart home traffic stays local — no cloud.
"""

import os
import subprocess
import time


class MQTTBroker:
    """
    Manages the local Mosquitto MQTT broker.
    Mosquitto install: apt install mosquitto mosquitto-clients
    """

    def is_running(self) -> bool:
        """Check if Mosquitto is running."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "mosquitto"],
                capture_output=True, text=True
            )
            return result.stdout.strip() == "active"
        except:
            # Try port check as fallback
            import socket
            try:
                s = socket.create_connection(("localhost", 1883), timeout=1)
                s.close()
                return True
            except:
                return False

    def start(self) -> bool:
        """Start the Mosquitto broker."""
        if self.is_running():
            return True
        try:
            subprocess.run(["systemctl", "start", "mosquitto"], check=True)
            time.sleep(1)
            return self.is_running()
        except Exception as e:
            print(f"[MQTTBroker] Start error: {e}")
            # Try direct launch
            try:
                subprocess.Popen(["mosquitto", "-d"])
                time.sleep(1)
                return self.is_running()
            except:
                return False

    def stop(self):
        try:
            subprocess.run(["systemctl", "stop", "mosquitto"])
        except:
            subprocess.run(["pkill", "mosquitto"])

    def enable_on_boot(self):
        """Enable Mosquitto to start on system boot."""
        try:
            subprocess.run(["systemctl", "enable", "mosquitto"])
        except Exception as e:
            print(f"[MQTTBroker] Enable error: {e}")

    def get_config_path(self) -> str:
        """Return path to Mosquitto config file."""
        candidates = [
            "/etc/mosquitto/mosquitto.conf",
            "/usr/local/etc/mosquitto/mosquitto.conf",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return "/etc/mosquitto/mosquitto.conf"

    def write_odin_config(self):
        """
        Write a minimal Mosquitto config for ODIN.
        Allows local connections without auth (internal only).
        """
        config = """# ODIN MQTT Broker Config
listener 1883 localhost
allow_anonymous true
log_type all
persistence true
persistence_location /var/lib/mosquitto/
"""
        config_path = self.get_config_path()
        try:
            with open(config_path, "w") as f:
                f.write(config)
            print(f"[MQTTBroker] Config written to {config_path}")
        except PermissionError:
            print(f"[MQTTBroker] Need sudo to write {config_path}")
