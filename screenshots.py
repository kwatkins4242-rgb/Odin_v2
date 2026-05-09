import os
import base64
from google.genai import types


SCREENSHOTS_DIR = os.environ.get("ODIN_SCREENSHOTS_DIR", r"C:\AI\MyOdin\screenshots")


def load_image_part(image_path):
    """Load an image file and return a Gemini-compatible Part."""
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")
    with open(image_path, "rb") as f:
        data = f.read()
    return types.Part(inline_data=types.Blob(mime_type=mime_type, data=data))


def get_latest_screenshot():
    """Return the path to the most recently modified image in SCREENSHOTS_DIR."""
    if not os.path.isdir(SCREENSHOTS_DIR):
        return None
    images = [
        os.path.join(SCREENSHOTS_DIR, f)
        for f in os.listdir(SCREENSHOTS_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
    if not images:
        return None
    return max(images, key=os.path.getmtime)


def get_n_latest_screenshots(n=3):
    """Return paths to the N most recent screenshots."""
    if not os.path.isdir(SCREENSHOTS_DIR):
        return []
    images = [
        os.path.join(SCREENSHOTS_DIR, f)
        for f in os.listdir(SCREENSHOTS_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
    images.sort(key=os.path.getmtime, reverse=True)
    return images[:n]
