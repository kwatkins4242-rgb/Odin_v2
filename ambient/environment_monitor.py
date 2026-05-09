"""
ODIN-SENSE — Environment Monitor
Monitors the broader environment Charles is in:
  - System health (CPU, RAM, disk)
  - Network status
  - Time of day context
  - Battery/power status
  - Audio environment (loud/quiet)

Keeps sense_state current so ODIN always has environmental context.
"""

import os
import time
import psutil
from datetime import datetime

POLL_INTERVAL_SEC = float(os.getenv("ENV_POLL_INTERVAL", "30.0"))


class EnvironmentMonitor:

    def __init__(self, state: dict):
        self._state   = state
        self._running = False

    def run(self):
        """Background polling loop. Updates state every POLL_INTERVAL_SEC."""
        self._running = True
        while self._running:
            try:
                self._update()
            except Exception as e:
                print(f"[EnvMonitor] Error: {e}")
            time.sleep(POLL_INTERVAL_SEC)

    def _update(self):
        now = datetime.now()

        env = {
            "timestamp":      now.isoformat(),
            "time_of_day":    self._get_time_context(now.hour),
            "cpu_percent":    psutil.cpu_percent(interval=1),
            "ram_percent":    psutil.virtual_memory().percent,
            "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_free_gb":   self._get_disk_free(),
            "battery":        self._get_battery(),
            "network_up":     self._check_network(),
            "running_procs":  self._get_notable_processes(),
        }

        self._state["environment"] = env

        # Surface critical alerts
        if env["cpu_percent"] > 90:
            self._state["pending_alert"] = {
                "type": "high_cpu",
                "message": f"CPU is pegged at {env['cpu_percent']}%. Something's hammering it."
            }
        if env["ram_percent"] > 90:
            self._state["pending_alert"] = {
                "type": "low_ram",
                "message": f"RAM at {env['ram_percent']}%. You're running low on memory."
            }
        battery = env.get("battery", {})
        if battery and not battery.get("charging") and battery.get("percent", 100) < 15:
            self._state["pending_alert"] = {
                "type": "low_battery",
                "message": f"Battery at {battery['percent']}%. Plug in soon."
            }

    def _get_time_context(self, hour: int) -> str:
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _get_disk_free(self) -> float:
        try:
            usage = psutil.disk_usage("/")
            return round(usage.free / (1024**3), 2)
        except:
            return -1.0

    def _get_battery(self) -> dict:
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent":  round(battery.percent, 1),
                    "charging": battery.power_plugged,
                    "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                }
        except:
            pass
        return {}

    def _check_network(self) -> bool:
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    def _get_notable_processes(self) -> list[str]:
        """Return names of resource-heavy processes."""
        try:
            procs = []
            for proc in psutil.process_iter(["name", "cpu_percent"]):
                if proc.info["cpu_percent"] and proc.info["cpu_percent"] > 20:
                    procs.append(proc.info["name"])
            return procs[:5]
        except:
            return []

    def get_snapshot(self) -> dict:
        return self._state.get("environment", {})

    def stop(self):
        self._running = False
