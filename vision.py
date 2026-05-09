


"""
vision.py – The Eyes
Captures the screen, resizes it for faster upload, and returns the file path.
Consolidated to use shared vision utilities.
"""

import sys
from pathlib import Path

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import utils.vision_utils as vision_utils

# Create logs directory if it does not exist
LOG_DIR = Path(__file__).parent / "logs"

def capture_screen(resize_to: int = None) -> str:
    """
    Take a full-screen screenshot and optionally resize it for faster LLM upload.
    Uses shared utility function.
    """
    return vision_utils.capture_screen(LOG_DIR, resize_to=resize_to)



