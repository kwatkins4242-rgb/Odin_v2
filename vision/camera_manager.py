"""
ODIN-SENSE — Camera Manager
Manages camera input — laptop webcam, USB cam, or Raspberry Pi camera.
Provides single frames or continuous streams to other vision modules.

Supports:
  - Auto-selects best available camera
  - Graceful fallback when no camera present
  - Resolution tuning for performance vs quality
  - Pause/resume for privacy
"""

import os
import time
import numpy as np
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

CAMERA_INDEX      = int(os.getenv("CAMERA_INDEX", "0"))
CAPTURE_WIDTH     = int(os.getenv("CAMERA_WIDTH", "640"))
CAPTURE_HEIGHT    = int(os.getenv("CAMERA_HEIGHT", "480"))
CAPTURE_FPS       = int(os.getenv("CAMERA_FPS", "30"))


class CameraManager:

    def __init__(self):
        self._cap     = None
        self._active  = False
        self._paused  = False
        self._open()

    def _open(self):
        """Open camera with auto-detection fallback."""
        try:
            import cv2
            # Try the configured index first
            for idx in [CAMERA_INDEX, 0, 1, 2]:
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAPTURE_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
                    cap.set(cv2.CAP_PROP_FPS,          CAPTURE_FPS)
                    # Test read
                    ok, _ = cap.read()
                    if ok:
                        self._cap    = cap
                        self._active = True
                        print(f"[Camera] Opened camera index {idx} ({CAPTURE_WIDTH}x{CAPTURE_HEIGHT})")
                        return
                    cap.release()

            print("[Camera] No camera found — vision features disabled")
        except ImportError:
            print("[Camera] OpenCV not installed — camera disabled")
        except Exception as e:
            print(f"[Camera] Failed to open camera: {e}")

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame.
        Returns numpy BGR array (OpenCV format) or None.
        """
        if not self._active or self._paused or self._cap is None:
            return None
        try:
            import cv2
            ok, frame = self._cap.read()
            if ok:
                return frame
            # Camera disconnected — try to reopen
            self._cap.release()
            self._active = False
            time.sleep(1)
            self._open()
        except Exception as e:
            print(f"[Camera] Capture error: {e}")
        return None

    def capture_rgb(self) -> Optional[np.ndarray]:
        """Capture frame in RGB format (for face_recognition library)."""
        frame = self.capture_frame()
        if frame is None:
            return None
        import cv2
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def pause(self):
        """Pause camera (privacy mode — no frames captured)."""
        self._paused = True
        print("[Camera] Paused (privacy mode)")

    def resume(self):
        self._paused = False
        print("[Camera] Resumed")

    def is_active(self) -> bool:
        return self._active and not self._paused

    def get_resolution(self) -> dict:
        if not self._cap:
            return {}
        import cv2
        return {
            "width":  int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps":    int(self._cap.get(cv2.CAP_PROP_FPS))
        }

    def release(self):
        if self._cap:
            self._cap.release()
            self._active = False

    def __del__(self):
        self.release()
