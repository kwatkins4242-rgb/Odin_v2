"""
COMMS — RF Manager (433MHz / 915MHz)
Controls RF devices: power outlets, ceiling fans, door sensors, garage doors.
Tons of cheap smart plugs and switches use 433MHz — this talks to all of them.

Hardware needed: ~$5 RF transmitter/receiver module (FS1000A or similar)
On Raspberry Pi: use GPIO via rpi-rf
On PC: use USB RTL-SDR dongle or RF serial module
"""

import os
import time
from typing import Optional

RF_FREQUENCY  = os.getenv("RF_FREQUENCY", "433")   # "433" or "915"
RF_SERIAL_PORT = os.getenv("RF_SERIAL_PORT", "/dev/ttyUSB0")


class RFManager:

    def __init__(self):
        self._available = self._detect_hardware()

    def _detect_hardware(self) -> bool:
        """Check if RF hardware is available."""
        import os
        # Check for Raspberry Pi GPIO
        if os.path.exists("/dev/gpiomem"):
            return True
        # Check for serial RF module
        if os.path.exists(RF_SERIAL_PORT):
            return True
        return False

    def send(self, frequency_mhz: str, code: str, value: Optional[str] = None,
             repeat: int = 3) -> bool:
        """
        Transmit an RF code.
        Repeats transmission multiple times for reliability (RF can miss).
        """
        if os.path.exists("/dev/gpiomem"):
            return self._send_gpio(code, repeat)
        elif os.path.exists(RF_SERIAL_PORT):
            return self._send_serial(code, value, repeat)
        else:
            print("[RF] No RF hardware detected")
            return False

    def _send_gpio(self, code: str, repeat: int) -> bool:
        """Send RF via Raspberry Pi GPIO (rpi-rf)."""
        try:
            from rpi_rf import RFDevice
            rfdevice = RFDevice(int(os.getenv("RF_GPIO_PIN", "17")))
            rfdevice.enable_tx()
            for _ in range(repeat):
                rfdevice.tx_code(int(code), int(os.getenv("RF_PROTOCOL", "1")),
                                 int(os.getenv("RF_PULSE_LENGTH", "350")))
                time.sleep(0.1)
            rfdevice.cleanup()
            return True
        except Exception as e:
            print(f"[RF] GPIO send error: {e}")
            return False

    def _send_serial(self, code: str, value: Optional[str], repeat: int) -> bool:
        """Send RF via serial module."""
        try:
            import serial
            payload = f"{code}:{value}" if value else code
            with serial.Serial(RF_SERIAL_PORT, 9600, timeout=1) as ser:
                for _ in range(repeat):
                    ser.write(f"{payload}\n".encode())
                    time.sleep(0.1)
            return True
        except Exception as e:
            print(f"[RF] Serial send error: {e}")
            return False

    def is_available(self) -> bool:
        return self._available


class RFScanner:
    """Listens for incoming RF signals — useful for learning codes and detecting sensors."""

    def listen(self, duration_sec: int = 10, callback=None) -> list:
        """
        Listen for RF signals. Returns list of received codes.
        callback(code) called for each received signal if provided.
        """
        received = []
        if os.path.exists("/dev/gpiomem"):
            received = self._listen_gpio(duration_sec, callback)
        else:
            print("[RFScanner] No GPIO — passive RF scan not available without Pi")
        return received

    def _listen_gpio(self, duration_sec: int, callback) -> list:
        try:
            import time
            from rpi_rf import RFDevice

            rfdevice = RFDevice(int(os.getenv("RF_RX_GPIO_PIN", "27")))
            rfdevice.enable_rx()

            received  = []
            last_code = None
            end_time  = time.time() + duration_sec

            while time.time() < end_time:
                if rfdevice.rx_code_timestamp != last_code:
                    last_code = rfdevice.rx_code_timestamp
                    code_data = {
                        "code":         rfdevice.rx_code,
                        "pulse_length": rfdevice.rx_pulselength,
                        "protocol":     rfdevice.rx_proto,
                        "timestamp":    time.time()
                    }
                    received.append(code_data)
                    if callback:
                        callback(code_data)
                time.sleep(0.01)

            rfdevice.cleanup()
            return received
        except Exception as e:
            print(f"[RFScanner] Listen error: {e}")
            return []
