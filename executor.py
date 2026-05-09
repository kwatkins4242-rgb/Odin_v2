import pyautogui
import logging
import time

log = logging.getLogger("odin.vision.executor")

pyautogui.FAILSAFE = True  # Move mouse to corner to abort

def execute_action(action_dict):
    """
    Executes a single pyautogui action based on a dictionary description.
    """
    action_type = action_dict.get("action")
    if not action_type:
        log.warning("No action type provided.")
        return

    try:
        if action_type == "click":
            x = action_dict.get("x")
            y = action_dict.get("y")
            button = action_dict.get("button", "left")
            log.info(f"Clicking at ({x}, {y}) with {button} button.")
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, button=button)
            else:
                pyautogui.click(button=button)

        elif action_type == "double_click":
            x = action_dict.get("x")
            y = action_dict.get("y")
            log.info(f"Double clicking at ({x}, {y}).")
            if x is not None and y is not None:
                pyautogui.doubleClick(x=x, y=y)
            else:
                pyautogui.doubleClick()

        elif action_type == "type":
            text = action_dict.get("text", "")
            log.info(f"Typing text: '{text}'")
            pyautogui.write(text, interval=0.05)

        elif action_type == "press":
            key = action_dict.get("key")
            log.info(f"Pressing key: '{key}'")
            if key:
                pyautogui.press(key)

        elif action_type == "scroll":
            amount = action_dict.get("amount", 0)
            log.info(f"Scrolling by: {amount}")
            pyautogui.scroll(amount)
            
        elif action_type == "wait":
            seconds = action_dict.get("seconds", 1)
            log.info(f"Waiting for {seconds} seconds.")
            time.sleep(seconds)

        else:
            log.warning(f"Unknown action type: {action_type}")
    except pyautogui.FailSafeException:
        log.error("PyAutoGUI FailSafe triggered. Execution aborted.")
    except Exception as e:
        log.error(f"Error executing action {action_dict}: {e}")

def execute_actions(actions_list):
    for act in actions_list:
        execute_action(act)
        time.sleep(0.5)  # small buffer between actions
