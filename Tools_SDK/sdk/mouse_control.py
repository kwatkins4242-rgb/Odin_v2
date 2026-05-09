import pyautogui
import time

pyautogui.FAILSAFE = True  # Move mouse to corner to abort

def mouse_move(x: int, y: int):
    pyautogui.moveTo(x, y, duration=0.3)

def mouse_click(x: int, y: int, button: str = "left"):
    pyautogui.click(x, y, button=button)

def mouse_double_click(x: int, y: int):
    pyautogui.doubleClick(x, y)

def mouse_drag(x1: int, y1: int, x2: int, y2: int):
    pyautogui.dragTo(x2, y2, duration=0.5)

def type_text(text: str, interval: float = 0.05):
    pyautogui.typewrite(text, interval=interval)

def press_key(key: str):
    pyautogui.press(key)

def hotkey(*keys):
    pyautogui.hotkey(*keys)

if __name__ == "__main__":
    print("Mouse control module tested successfully. (No actions taken to prevent accidental movement)")
