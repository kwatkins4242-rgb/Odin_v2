"""
COMMS — IR Learner
Standalone module for learning IR codes from physical remotes.
Import from ir_manager — this file provides the CLI interface.
"""

from protocols.infrared.ir_manager import IRLearner, IRManager


def learn_device(device_type: str):
    """
    Interactive IR learning session for a device type.
    Guides Charles through pressing each button on the remote.

    Usage:
        python -m protocols.infrared.ir_learner
    """
    learner  = IRLearner()
    ir       = IRManager()

    COMMON_COMMANDS = {
        "tv":         ["power", "volume_up", "volume_down", "mute", "input", "channel_up", "channel_down"],
        "ac":         ["power", "temp_up", "temp_down", "mode_cool", "mode_heat", "fan_low", "fan_high"],
        "fan":        ["power", "speed_1", "speed_2", "speed_3", "oscillate", "timer"],
        "projector":  ["power", "input_hdmi", "input_vga", "menu", "volume_up", "volume_down"],
    }

    commands = COMMON_COMMANDS.get(device_type, ["power"])
    print(f"\n=== Learning IR codes for: {device_type} ===")
    print(f"Commands to learn: {', '.join(commands)}")
    print("Have your remote ready.\n")

    for cmd in commands:
        input(f"Press ENTER then press [{cmd}] on the remote...")
        code = learner.learn(device_type, cmd)
        if code:
            print(f"  ✓ Learned: {cmd}")
        else:
            print(f"  ✗ Failed to learn: {cmd} — press ENTER to skip")
            input()

    print(f"\n✅ Learning complete for {device_type}")
    print(f"Commands available: {', '.join(ir.list_commands(device_type))}")


if __name__ == "__main__":
    import sys
    device = sys.argv[1] if len(sys.argv) > 1 else input("Device type (tv/ac/fan): ")
    learn_device(device)
