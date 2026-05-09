"""
ODIN-SENSE — Wake Word Detector
Uses Picovoice Porcupine to listen for trigger phrases 24/7.
Extremely low CPU (~1%) — designed to run always-on.

Porcupine AccessKey: free tier available at https://picovoice.ai
Set PORCUPINE_ACCESS_KEY in .env
"""

import os
import struct
import time
from typing import Callable, Optional
from dotenv import load_dotenv

load_dotenv()

PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")
SENSITIVITY_DEFAULT  = float(os.getenv("WAKE_SENSITIVITY", "0.6"))


class WakeWordDetector:
    """
    Always-on wake word listener.
    Calls on_wake(keyword_str) when a trigger phrase is detected.
    Rotates through all .ppn files managed by WakeManager.
    """

    def __init__(self, wake_manager: "WakeManager", on_wake: Callable[[str], None]):
        self.wake_manager = wake_manager
        self.on_wake      = on_wake
        self._running     = False
        self._paused      = False

    def run(self):
        """
        Main detection loop. Runs in a background thread.
        Blocks forever until stop() is called.
        """
        if not PORCUPINE_ACCESS_KEY:
            print("[WakeWord] ⚠ PORCUPINE_ACCESS_KEY not set — running in simulation mode")
            self._simulation_mode()
            return

        try:
            import pvporcupine
            import pvrecorder
        except ImportError:
            print("[WakeWord] pvporcupine/pvrecorder not installed — running in simulation mode")
            self._simulation_mode()
            return

        self._running = True

        while self._running:
            # Get current batch of wake word files
            keyword_paths, keywords, sensitivities = self.wake_manager.get_active_batch()

            if not keyword_paths:
                print("[WakeWord] No .ppn files found — check wake_word/custom_words/")
                time.sleep(5)
                continue

            porcupine = None
            recorder  = None

            try:
                porcupine = pvporcupine.create(
                    access_key=PORCUPINE_ACCESS_KEY,
                    keyword_paths=keyword_paths,
                    sensitivities=sensitivities
                )

                recorder = pvrecorder.PvRecorder(
                    frame_length=porcupine.frame_length,
                    device_index=-1  # Default device; can set via env
                )
                recorder.start()
                print(f"[WakeWord] Listening for: {', '.join(keywords)}")

                while self._running and not self._paused:
                    pcm = recorder.read()
                    result = porcupine.process(pcm)
                    if result >= 0:
                        detected_keyword = keywords[result] if result < len(keywords) else "odin"
                        self.on_wake(detected_keyword)
                        # Brief pause after wake to avoid double-triggering
                        time.sleep(0.5)

            except Exception as e:
                print(f"[WakeWord] Error: {e}")
                time.sleep(2)
            finally:
                if recorder:
                    try:
                        recorder.stop()
                        recorder.delete()
                    except:
                        pass
                if porcupine:
                    try:
                        porcupine.delete()
                    except:
                        pass

    def pause(self):
        """Pause detection (e.g. while ODIN is speaking to avoid self-triggering)."""
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False

    def _simulation_mode(self):
        """
        Runs when Porcupine not available.
        Simulates wake word detection every 30 seconds for testing.
        """
        print("[WakeWord] Simulation mode — simulating wake every 30s")
        self._running = True
        while self._running:
            time.sleep(30)
            if not self._paused:
                self.on_wake("hey-odin (simulated)")
