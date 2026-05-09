"""
ODIN-SENSE — OCR Engine (ocr_engine.py)
Standalone text extraction from images and screen captures.
Sits in odin-sense/vision/ folder.

Two engines:
  EasyOCR   → better accuracy, no system install, first choice
  Tesseract → fallback, needs: apt install tesseract-ocr

Usage:
  ocr = OCREngine()
  text = ocr.extract_text(image_array)
  text = ocr.extract_from_file("screenshot.png")
  text = ocr.extract_from_screen()   # live screen grab
"""

import os
import numpy as np
from typing import Optional, List


class OCREngine:

    def __init__(self):
        self._easyocr  = None
        self._tesseract_available = False
        self._init()

    def _init(self):
        """Initialize best available OCR engine."""
        # Try EasyOCR first
        try:
            import easyocr
            self._easyocr = easyocr.Reader(["en"], gpu=False, verbose=False)
            print("[OCR] EasyOCR ready")
        except ImportError:
            print("[OCR] EasyOCR not installed — trying tesseract")
        except Exception as e:
            print(f"[OCR] EasyOCR init error: {e}")

        # Check Tesseract as fallback
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            if not self._easyocr:
                print("[OCR] Tesseract ready (fallback)")
        except:
            if not self._easyocr:
                print("[OCR] ⚠ No OCR engine available. Install EasyOCR or Tesseract.")

    def extract_text(self, image: np.ndarray) -> str:
        """
        Extract all text from a numpy image array (BGR or RGB).
        Returns plain text string.
        """
        if image is None or image.size == 0:
            return ""

        if self._easyocr:
            return self._extract_easyocr(image)
        elif self._tesseract_available:
            return self._extract_tesseract(image)
        return ""

    def extract_from_file(self, path: str) -> str:
        """Extract text from an image file."""
        try:
            import cv2
            img = cv2.imread(path)
            if img is None:
                from PIL import Image
                img = np.array(Image.open(path))
            return self.extract_text(img)
        except Exception as e:
            print(f"[OCR] File read error: {e}")
            return ""

    def extract_from_screen(self, region: dict = None) -> str:
        """
        Capture screen and extract text.
        region: optional {"left": x, "top": y, "width": w, "height": h}
        """
        try:
            import mss, mss.tools
            with mss.mss() as sct:
                monitor = region or sct.monitors[1]
                img     = np.array(sct.grab(monitor))
                return self.extract_text(img[:, :, :3])
        except ImportError:
            try:
                from PIL import ImageGrab
                img = np.array(ImageGrab.grab())
                return self.extract_text(img)
            except Exception as e:
                print(f"[OCR] Screen capture failed: {e}")
                return ""

    def extract_with_boxes(self, image: np.ndarray) -> List[dict]:
        """
        Extract text WITH bounding boxes.
        Returns list of {text, box, confidence}
        box: [top_left, top_right, bottom_right, bottom_left]
        """
        if image is None or not self._easyocr:
            return []
        try:
            results = self._easyocr.readtext(image)
            return [
                {"text": text, "box": box, "confidence": round(conf, 3)}
                for box, text, conf in results
                if conf > 0.3
            ]
        except Exception as e:
            print(f"[OCR] extract_with_boxes error: {e}")
            return []

    def _extract_easyocr(self, image: np.ndarray) -> str:
        try:
            results = self._easyocr.readtext(image, detail=0, paragraph=True)
            return "\n".join(r for r in results if r.strip())
        except Exception as e:
            print(f"[OCR] EasyOCR extraction error: {e}")
            if self._tesseract_available:
                return self._extract_tesseract(image)
            return ""

    def _extract_tesseract(self, image: np.ndarray) -> str:
        try:
            import pytesseract
            from PIL import Image
            pil = Image.fromarray(image)
            return pytesseract.image_to_string(pil, config="--psm 6").strip()
        except Exception as e:
            print(f"[OCR] Tesseract error: {e}")
            return ""

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image for better OCR accuracy:
        grayscale → denoise → threshold → upscale if small
        """
        try:
            import cv2
            gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            # Upscale small images — OCR works better on larger text
            h, w  = denoised.shape
            if w < 640:
                scale    = 640 / w
                denoised = cv2.resize(denoised, None, fx=scale, fy=scale,
                                      interpolation=cv2.INTER_CUBIC)
            # Adaptive threshold for better contrast
            thresh = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            return thresh
        except Exception:
            return image

    def is_ready(self) -> bool:
        return self._easyocr is not None or self._tesseract_available
