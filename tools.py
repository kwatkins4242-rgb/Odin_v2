

"""
tools.py – The Hands
Translates high-level decisions into low-level keyboard/mouse events.
"""

import pyautogui

# Emergency brake: slam mouse to top-left corner to abort
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05         # Small global pause between pyautogui calls

def execute_action(action: dict) -> None:
    """
    Execute an action dictionary produced by the LLM.

    Expected schema:
    {
        "type": "CLICK" | "TYPE" | "HOTKEY" | "SCROLL",
        "x": int, "y": int,            # for CLICK
        "text": str,                   # for TYPE
        "keys": ["ctrl", "c"],         # for HOTKEY
        "amount": int                  # for SCROLL
    }
    """
    act_type = action.get("type", "").upper()

    if act_type == "CLICK":
        pyautogui.click(action["x"], action["y"])

    elif act_type == "TYPE":
        pyautogui.write(action.get("text", ""), interval=0.08)

    elif act_type == "HOTKEY":
        keys = action.get("keys", [])
        if keys:
            pyautogui.hotkey(*keys)

    elif act_type == "SCROLL":
        pyautogui.scroll(action.get("amount", 0))

    else:
        raise ValueError(f"Unknown action type: {act_type}")

    print(f"[TOOLS] Executed: {action}")


