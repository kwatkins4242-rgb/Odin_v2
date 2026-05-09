"""
COMMS — RF Scanner
Standalone RF signal scanner. Import RFScanner from rf_manager.
This file provides CLI access for learning RF codes.
"""

from protocols.rf.rf_manager import RFScanner, RFManager
import json
from pathlib import Path


def learn_rf_code(device_name: str, command: str):
    """
    Learn an RF code by pressing a button on a physical remote/switch.
    Saves the code to rf_codes/ for later use.
    """
    scanner  = RFScanner()
    codes_dir = Path(__file__).parent.parent.parent / "rf_codes"
    codes_dir.mkdir(exist_ok=True)

    print(f"Listening for RF signal... press [{command}] on your device.")
    received = scanner.listen(duration_sec=10)

    if not received:
        print("No signal received.")
        return

    code_data = received[0]
    print(f"Received: {code_data}")

    # Save to file
    codes_file = codes_dir / f"{device_name}.json"
    try:
        with open(codes_file) as f:
            codes = json.load(f)
    except:
        codes = {}

    codes[command] = {
        "code":         code_data["code"],
        "pulse_length": code_data["pulse_length"],
        "protocol":     code_data["protocol"]
    }

    with open(codes_file, "w") as f:
        json.dump(codes, f, indent=2)

    print(f"✓ Saved: {device_name}/{command}")


if __name__ == "__main__":
    import sys
    device  = sys.argv[1] if len(sys.argv) > 1 else input("Device name: ")
    command = sys.argv[2] if len(sys.argv) > 2 else input("Command: ")
    learn_rf_code(device, command)