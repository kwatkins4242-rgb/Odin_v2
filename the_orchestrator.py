
"""
main.py – The Orchestrator
Runs the OODA loop forever until the LLM reports DONE.
"""

import sys
import time

from brain import ask_llm
from config import LOOP_DELAY, MAX_SCREEN_WIDTH
from tools import execute_action
from vision import capture_screen
from voice import speak

def run_agent(user_goal: str) -> None:
    """
    Observe → Orient/Decide → Act loop.
    """
    speak(f"Starting task: {user_goal}")
    try:
        while True:
            # 1. OBSERVE
            screenshot_path = capture_screen(resize_to=MAX_SCREEN_WIDTH)
            # 2. ORIENT / DECIDE
            action = ask_llm(user_goal, screenshot_path)
            print(f"[MAIN] Decision: {action}")
            # 3. ACT
            if action.get("type") == "DONE":
                speak("Task complete!")
                break
            execute_action(action)
            # 4. PAUSE
            time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
        speak("Agent interrupted by user.")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py 'your goal here'")
        sys.exit(1)
    goal = " ".join(sys.argv[1:])
    run_agent(goal)




async def read_all_sensors(self, system_id: str) -> Dict[str, Any]:
        system_sensors = [
            sid for sid, sensor in self.sensors.items()
            if sensor["config"].get("system_id") == system_id
        ]

        if not system_sensors:  ### NEW: create demo sensors only once
            await self.register_sensor(
                "temp_01", "temperature",
                {"system_id": system_id, "base_value": 25.0, "thresholds": {"high": 35.0}}
            )
            await self.register_sensor(
                "press_01", "pressure",
                {"system_id": system_id, "base_value": 101.3}
            )
            system_sensors = ["temp_01", "press_01"]

        results = {}
        for sid in system_sensors:
            results[sid] = await self.read_sensor(sid)

        return {
            "system_id": system_id,
            "sensor_count": len(system_sensors),
            "readings": results,
            "timestamp": datetime.now().isoformat()
        }

