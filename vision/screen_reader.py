"""
ODIN-SENSE — Screen Reader
Reads what's on Charles's screen.
Useful for ODIN to understand context without being told explicitly:
  "What's that error in your terminal?"
  "I can see you're looking at that invoice..."

Uses PIL/mss for screen capture, EasyOCR for text extraction.
"""

import os
import numpy as np
from typing import Optional

SCREEN_INDEX = int(os.getenv("SCREEN_INDEX", "0"))  # Multi-monitor: 0=primary


class ScreenReader:

    def capture_screenshot(self) -> Optional[np.ndarray]:
        """Capture the current screen as a numpy RGB array."""
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                monitors = sct.monitors
                if SCREEN_INDEX + 1 >= len(monitors):
                    monitor = monitors[1]  # Primary monitor
                else:
                    monitor = monitors[SCREEN_INDEX + 1]
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                return img[:, :, :3]  # Drop alpha channel → BGR
        except ImportError:
            return self._capture_pil_fallback()
        except Exception as e:
            print(f"[ScreenReader] Capture error: {e}")
            return None

    def _capture_pil_fallback(self) -> Optional[np.ndarray]:
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            return np.array(img)
        except Exception as e:
            print(f"[ScreenReader] PIL fallback failed: {e}")
            return None

    def read_screen_text(self) -> str:
        """Full OCR of current screen. Returns extracted text."""
        img = self.capture_screenshot()
        if img is None:
            return ""
        from vision.ocr_engine import OCREngine
        ocr = OCREngine()
        return ocr.extract_text(img)

    def get_focused_region_text(self, x: int, y: int, w: int, h: int) -> str:
        """Read text from a specific screen region (for reading active window content)."""
        img = self.capture_screenshot()
        if img is None:
            return ""
        region = img[y:y+h, x:x+w]
        from vision.ocr_engine import OCREngine
        ocr = OCREngine()
        return ocr.extract_text(region)


class OCREngine:
    """
    Extracts text from images.
    Primary: EasyOCR (neural, no system install needed)
    Fallback: Pytesseract (requires: apt install tesseract-ocr)
    """

    def __init__(self):
        self._easyocr_reader = None
        self._init_easyocr()

    def _init_easyocr(self):
        try:
            import easyocr
            self._easyocr_reader = easyocr.Reader(
                ["en"],
                gpu=False,  # CPU mode for portability
                verbose=False
            )
            print("[OCR] EasyOCR initialized")
        except ImportError:
            print("[OCR] EasyOCR not installed — will use pytesseract")
        except Exception as e:
            print(f"[OCR] EasyOCR init error: {e}")

    def extract_text(self, image: np.ndarray) -> str:
        """Extract all text from an image array."""
        if image is None:
            return ""
        if self._easyocr_reader:
            return self._extract_easyocr(image)
        return self._extract_tesseract(image)

    def extract_from_file(self, image_path: str) -> str:
        """Extract text from an image file."""
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                from PIL import Image
                img = np.array(Image.open(image_path))
            return self.extract_text(img)
        except Exception as e:
            print(f"[OCR] extract_from_file error: {e}")
            return ""

    def _extract_easyocr(self, image: np.ndarray) -> str:
        try:
            results = self._easyocr_reader.readtext(image, detail=0, paragraph=True)
            return "\n".join(results)
        except Exception as e:
            print(f"[OCR] EasyOCR extraction error: {e}")
            return self._extract_tesseract(image)

    def _extract_tesseract(self, image: np.ndarray) -> str:
        try:
            import pytesseract
            from PIL import Image
            pil_image = Image.fromarray(image)
            text = pytesseract.image_to_string(pil_image, config="--psm 6")
            return text.strip()
        except Exception as e:
            print(f"[OCR] Tesseract extraction error: {e}")
            return ""
