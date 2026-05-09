
"""
ODIN — Vision Utilities
========================
Shared logic for screen capture and image processing.
"""

import os
import time
from datetime import datetime
from pathlib import Path
import pyautogui
from PIL import Image

def capture_screen(output_dir: Path, resize_to: int = None) -> str:
    """
    Take a full-screen screenshot and save it to the specified directory.
    
    Returns
    -------
    str
        Absolute path to the saved PNG file.
    """
    output_dir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = output_dir / f"screen_{timestamp}.png"

    # Capture
    screenshot = pyautogui.screenshot()

    # Optional resize
    if resize_to:
        w, h = screenshot.size
        if w > resize_to:
            new_h = int(h * (resize_to / w))
            screenshot = screenshot.resize((resize_to, new_h), Image.LANCZOS)

    screenshot.save(filename, optimize=True, quality=50)
    return str(filename)
