"""
ODIN-SENSE — Audio Manager
Central audio I/O hub. All other modules go through this.
Manages device selection, input/output routing, and volume.
"""

import os
import time
import numpy as np
from typing import Optional, List

SAMPLE_RATE   = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
CHUNK_SIZE    = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))


class AudioManager:

    def __init__(self):
        self._input_device  = None
        self._output_device = None
        self._pa            = None
        self._initialized   = False
        self._init()

    def _init(self):
        try:
            import pyaudio
            self._pa          = pyaudio.PyAudio()
            self._initialized = True
        except ImportError:
            print("[AudioManager] PyAudio not installed")
        except Exception as e:
            print(f"[AudioManager] Init error: {e}")

    def list_devices(self) -> List[dict]:
        """List all available audio devices."""
        if not self._pa:
            return []
        devices = []
        for i in range(self._pa.get_device_count()):
            info = self._pa.get_device_info_by_index(i)
            devices.append({
                "index":       i,
                "name":        info["name"],
                "max_inputs":  info["maxInputChannels"],
                "max_outputs": info["maxOutputChannels"],
                "sample_rate": info["defaultSampleRate"]
            })
        return devices

    def select_best_device(self) -> Optional[dict]:
        """Auto-select the best input device. Prefers USB mics over built-ins."""
        devices = self.list_devices()
        if not devices:
            return None

        # Prefer USB microphones
        for d in devices:
            if d["max_inputs"] > 0 and "usb" in d["name"].lower():
                self._input_device = d
                return d

        # Fall back to default input
        for d in devices:
            if d["max_inputs"] > 0:
                self._input_device = d
                return d

        return None

    def get_rms_level(self, duration_sec: float = 0.5) -> float:
        """
        Get current ambient noise RMS level (0.0-1.0).
        Called by sensitivity tuner and noise filter.
        """
        if not self._pa:
            return 0.0
        try:
            import pyaudio
            stream = self._pa.open(
                rate=SAMPLE_RATE,
                channels=1,
                format=pyaudio.paFloat32,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            frames    = []
            n_chunks  = int(SAMPLE_RATE * duration_sec / CHUNK_SIZE)
            for _ in range(n_chunks):
                raw  = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                data = np.frombuffer(raw, dtype=np.float32)
                frames.append(data)
            stream.stop_stream()
            stream.close()

            all_audio = np.concatenate(frames)
            return float(np.sqrt(np.mean(all_audio ** 2)))
        except:
            return 0.0

    def cleanup(self):
        if self._pa:
            try:
                self._pa.terminate()
            except:
                pass
