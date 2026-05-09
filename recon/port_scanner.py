"""
ODIN-Hunter | Port Scanner
Identifies open ports and services
"""

import asyncio
import socket

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 465, 587, 993, 995,
    1433, 1521, 2181, 2375, 2376, 3000, 3306, 3389, 4443, 4848, 5000,
    5432, 5900, 6379, 7001, 8000, 8008, 8080, 8081, 8088, 8090, 8443,
    8444, 8888, 9000, 9090, 9200, 9300, 10000, 11211, 27017, 27018, 28017
]

SERVICE_MAP = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    465: "SMTPS", 587: "SMTP", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle", 2375: "Docker", 2376: "Docker-TLS",
    3000: "NodeJS/Grafana", 3306: "MySQL", 3389: "RDP", 4443: "HTTPS-Alt",
    5000: "Flask/Dev", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    7001: "WebLogic", 8000: "HTTP-Alt", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
    8888: "Jupyter/Dev", 9000: "PHP-FPM/SonarQube", 9090: "Prometheus",
    9200: "Elasticsearch", 9300: "Elasticsearch", 10000: "Webmin",
    11211: "Memcached", 27017: "MongoDB", 27018: "MongoDB", 28017: "MongoDB-Web"
}

class PortScanner:
    def __init__(self):
        self.timeout = 2.0

    async def scan(self, host: str, ports: list = None) -> dict:
        """Scan a host for open ports"""
        if ports is None:
            ports = COMMON_PORTS

        open_ports = []
        loop = asyncio.get_event_loop()

        async def check_port(port):
            try:
                conn = asyncio.open_connection(host, port)
                reader, writer = await asyncio.wait_for(conn, timeout=self.timeout)
                writer.close()
                await writer.wait_closed()
                service = SERVICE_MAP.get(port, "unknown")
                return {"port": port, "service": service, "state": "open"}
            except Exception:
                return None

        tasks = [check_port(p) for p in ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        open_ports = [r for r in results if isinstance(r, dict)]

        print(f"[PortScanner] {host}: {len(open_ports)} open ports")
        return {"host": host, "open_ports": open_ports, "total_scanned": len(ports)}

    def get_interesting_ports(self, scan_result: dict) -> list:
        """Flag ports that are interesting from a security perspective"""
        interesting = []
        HIGH_VALUE = [21, 22, 23, 2375, 3389, 5900, 6379, 9200, 11211, 27017]

        for port_info in scan_result.get("open_ports", []):
            port = port_info.get("port")
            if port in HIGH_VALUE:
                port_info["risk"] = "high"
                interesting.append(port_info)
            elif port not in [80, 443]:
                port_info["risk"] = "medium"
                interesting.append(port_info)

        return interesting
