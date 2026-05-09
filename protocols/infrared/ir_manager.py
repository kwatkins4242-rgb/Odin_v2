"""
COMMS — IR Manager
Sends infrared signals to control TVs, AC units, fans, projectors — anything with a remote.
Uses LIRC on Linux. Hardware: ~$5 IR blaster/receiver (GPIO or USB).

Code files live in ir_codes/ folder as JSON.
ODIN can learn new codes from existing remotes via ir_learner.py.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, List

IR_CODES_DIR = Path(__file__).parent / "ir_codes"
IR_CODES_DIR.mkdir(exist_ok=True)


class IRManager:

    def __init__(self):
        self._codes = self._load_all_codes()

    def _load_all_codes(self) -> dict:
        """Load all IR code JSON files from ir_codes/."""
        codes = {}
        for f in IR_CODES_DIR.glob("*.json"):
            try:
                with open(f) as fh:
                    codes[f.stem] = json.load(fh)
            except:
                pass
        return codes

    def send(self, device_type: str, command: str) -> bool:
        """
        Send an IR command to a device type.
        device_type: "tv", "ac", "fan", "projector", etc.
        command: "power", "volume_up", "mute", "cool_mode", etc.
        """
        if device_type not in self._codes:
            print(f"[IR] Unknown device type: {device_type}")
            return False

        device_codes = self._codes[device_type]
        if command not in device_codes:
            print(f"[IR] Unknown command '{command}' for '{device_type}'")
            return False

        code = device_codes[command]
        return self._transmit(code)

    def _transmit(self, code: str) -> bool:
        """Transmit an IR code via LIRC."""
        try:
            result = subprocess.run(
                ["irsend", "SEND_ONCE", code.split(":")[0], code.split(":")[1]],
                capture_output=True, text=True, timeout=3
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("[IR] LIRC (irsend) not found — IR transmission disabled")
            return False
        except Exception as e:
            print(f"[IR] Transmit error: {e}")
            return False

    def list_devices(self) -> List[str]:
        return list(self._codes.keys())

    def list_commands(self, device_type: str) -> List[str]:
        return list(self._codes.get(device_type, {}).keys())

    def add_code(self, device_type: str, command: str, code: str):
        """Add a new IR code for a device command."""
        if device_type not in self._codes:
            self._codes[device_type] = {}
        self._codes[device_type][command] = code
        self._save_device_codes(device_type)

    def _save_device_codes(self, device_type: str):
        path = IR_CODES_DIR / f"{device_type}.json"
        with open(path, "w") as f:
            json.dump(self._codes[device_type], f, indent=2)


class IRLearner:
    """
    Learns IR codes from existing remotes.
    Point a remote at the IR receiver and press a button — ODIN captures the code.
    """

    def learn(self, device_type: str, command: str, timeout_sec: int = 10) -> Optional[str]:
        """
        Listen for an IR signal and save it.
        Tell Charles: "Point your remote at the receiver and press [command]"
        """
        print(f"[IRLearner] Waiting for '{command}' from '{device_type}' ({timeout_sec}s)...")
        try:
            result = subprocess.run(
                ["irrecord", "-d", "/dev/lirc0", "--list-namespace"],
                capture_output=True, text=True, timeout=timeout_sec
            )
            if result.returncode == 0:
                code = result.stdout.strip()
                ir   = IRManager()
                ir.add_code(device_type, command, code)
                print(f"[IRLearner] Learned: {device_type}/{command} = {code}")
                return code
        except Exception as e:
            print(f"[IRLearner] Error: {e}")
        return None
