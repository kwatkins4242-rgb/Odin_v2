"""
COMMS — Network Scanner
Scans the local network for devices using nmap and ARP.
Finds IPs, hostnames, open ports, and device types.
"""

import subprocess
import socket
from typing import List


class NetworkScanner:

    def scan(self, subnet: str = None) -> List[dict]:
        """
        Scan the local subnet for active devices.
        Returns list of {ip, hostname, mac, open_ports, device_type}
        """
        if not subnet:
            from protocols.wifi.wifi_manager import WiFiManager
            info   = WiFiManager().get_network_info()
            subnet = info.get("subnet", "192.168.1.0/24")

        devices = []

        # Try nmap first (most thorough)
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(hosts=subnet, arguments="-sn -T4")  # Ping scan only (fast)
            for host in nm.all_hosts():
                info = nm[host]
                devices.append({
                    "ip":       host,
                    "hostname": info.hostname() or self._resolve_hostname(host),
                    "mac":      info["addresses"].get("mac", "unknown"),
                    "protocol": "wifi",
                    "state":    info.state()
                })
        except ImportError:
            # Fallback: basic ARP scan
            devices = self._arp_scan(subnet)
        except Exception as e:
            print(f"[NetworkScanner] nmap error: {e}")
            devices = self._arp_scan(subnet)

        return devices

    def scan_ports(self, ip: str, ports: str = "80,443,8080,8883,1883,5683") -> dict:
        """
        Scan specific ports on a device to identify its capabilities.
        Common ports: 80=HTTP, 1883=MQTT, 8883=MQTT+TLS, 5683=CoAP (IoT)
        """
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(ip, ports, "-sV -T4")
            open_ports = []
            if ip in nm.all_hosts():
                for proto in nm[ip].all_protocols():
                    for port in nm[ip][proto].keys():
                        if nm[ip][proto][port]["state"] == "open":
                            open_ports.append({
                                "port":    port,
                                "service": nm[ip][proto][port].get("name", "unknown"),
                                "version": nm[ip][proto][port].get("version", "")
                            })
            return {"ip": ip, "open_ports": open_ports}
        except Exception as e:
            return {"ip": ip, "error": str(e)}

    def _arp_scan(self, subnet: str) -> List[dict]:
        """Simple ARP-based scan as fallback when nmap unavailable."""
        devices = []
        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True, text=True
            )
            for line in result.stdout.split("\n"):
                if "(" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        hostname = parts[0]
                        ip       = parts[1].strip("()")
                        devices.append({
                            "ip":       ip,
                            "hostname": hostname,
                            "protocol": "wifi",
                            "source":   "arp"
                        })
        except Exception as e:
            print(f"[NetworkScanner] ARP fallback error: {e}")
        return devices

    def _resolve_hostname(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return ip


class MDNSDiscovery:
    """
    Discovers devices on the local network by service type using mDNS/Bonjour.
    Finds: Chromecasts, smart TVs, printers, Home Assistant, etc. without knowing their IP.
    """

    # Common IoT/smart home mDNS service types
    SERVICE_TYPES = [
        "_http._tcp.local.",        # Web servers
        "_googlecast._tcp.local.",  # Chromecast / Google devices
        "_hap._tcp.local.",         # HomeKit accessories
        "_mqtt._tcp.local.",        # MQTT brokers
        "_home-assistant._tcp.local.",
        "_esphome._tcp.local.",     # ESPHome devices
        "_workstation._tcp.local.", # Linux workstations
        "_airplay._tcp.local.",     # Apple AirPlay
        "_printer._tcp.local.",
    ]

    def discover(self, timeout_sec: int = 5) -> List[dict]:
        """Discover all mDNS services on the local network."""
        devices = []
        try:
            from zeroconf import Zeroconf, ServiceBrowser
            import time

            zc      = Zeroconf()
            found   = []

            class Listener:
                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info:
                        found.append({
                            "name":     name,
                            "type":     type_,
                            "ip":       socket.inet_ntoa(info.addresses[0]) if info.addresses else None,
                            "port":     info.port,
                            "protocol": "mdns",
                            "properties": {k.decode(): v.decode() for k, v in info.properties.items()
                                          if isinstance(k, bytes)}
                        })
                def remove_service(self, *args): pass
                def update_service(self, *args): pass

            listener = Listener()
            browsers = [ServiceBrowser(zc, stype, listener) for stype in self.SERVICE_TYPES]
            time.sleep(timeout_sec)
            zc.close()
            devices = found

        except ImportError:
            print("[mDNS] zeroconf not installed")
        except Exception as e:
            print(f"[mDNS] Discovery error: {e}")

        return devices
