"""COMMS — WiFi Manager
Manages WiFi connectivity and gets network info.
ODIN uses this to know what network it's on, get the local IP,
check if internet is up, and support network-based device discovery.
"""

import os
import socket
import subprocess
from typing import Optional, List


class WiFiManager:

    def get_local_ip(self) -> str:
        """Get the machine's local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def get_ssid(self) -> Optional[str]:
        """Get the current WiFi network name (SSID)."""
        try:
            import sys
            if sys.platform == "win32":
                result = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True, text=True
                )
                for line in result.stdout.split("\n"):
                    if "SSID" in line and "BSSID" not in line:
                        return line.split(":")[1].strip()
            else:
                result = subprocess.run(
                    ["iwgetid", "-r"],
                    capture_output=True, text=True
                )
                ssid = result.stdout.strip()
                return ssid if ssid else None
        except:
            return None

    def is_connected(self) -> bool:
        """Check if internet is reachable."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    def get_network_info(self) -> dict:
        """Get full network info."""
        local_ip = self.get_local_ip()
        # Derive subnet from IP (assumes /24)
        parts  = local_ip.rsplit(".", 1)
        subnet = parts[0] + ".0/24" if len(parts) == 2 else "unknown"

        return {
            "local_ip":  local_ip,
            "ssid":      self.get_ssid(),
            "connected": self.is_connected(),
            "subnet":    subnet
        }

    def get_gateway(self) -> Optional[str]:
        """Get default gateway IP."""
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True
            )
            parts = result.stdout.split()
            idx   = parts.index("via") + 1
            return parts[idx]
        except:
            try:
                local_ip = self.get_local_ip()
                parts    = local_ip.rsplit(".", 1)
                return parts[0] + ".1"
            except:
                return None
