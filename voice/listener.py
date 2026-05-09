"""
ODIN-SENSE — Voice Listener
Captures audio after wake word detection.
Uses Voice Activity Detection (VAD) to know when the user stops speaking
instead of relying on a fixed timeout.

Flow:
  wake word triggered → start recording → VAD detects silence → stop → return audio
"""

import os
import time
import struct
import numpy as np
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SAMPLE_RATE    = 16000   # Whisper expects 16kHz
CHANNELS       = 1       # Mono
MAX_RECORD_SEC = int(os.getenv("MAX_RECORD_SECONDS", "15"))
SILENCE_THRESH = float(os.getenv("SILENCE_THRESHOLD_SEC", "1.5"))  # Stop after this much silence
VAD_AGGRESSIVENESS = int(os.getenv("VAD_AGGRESSIVENESS", "2"))      # 0-3: higher = stricter


class VoiceListener:

    def __init__(self):
        self._sample_rate = SAMPLE_RATE

    def capture(self) -> Optional[np.ndarray]:
        """
        Record audio until user stops speaking.
        Returns numpy float32 array at 16kHz, or None on failure.
        """
        try:
            return self._capture_with_vad()
        except ImportError:
            return self._capture_simple_fallback()
        except Exception as e:
            print(f"[VoiceListener] Capture error: {e}")
            return None

    def _capture_with_vad(self) -> Optional[np.ndarray]:
        """
        Primary method: uses WebRTC VAD for smart silence detection.
        Stops recording when user pauses for SILENCE_THRESH seconds.
        """
        import webrtcvad
        import pyaudio

        vad    = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        pa     = pyaudio.PyAudio()

        # VAD requires 10, 20, or 30ms frames at 8/16/32kHz
        frame_duration_ms = 30
        frame_samples     = int(SAMPLE_RATE * frame_duration_ms / 1000)  # 480 samples
        frame_bytes       = frame_samples * 2  # 16-bit = 2 bytes per sample

        stream = pa.open(
            rate=SAMPLE_RATE,
            channels=CHANNELS,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=frame_samples
        )

        print("[VoiceListener] Recording... (speak now)")
        frames         = []
        silent_frames  = 0
        max_silent     = int(SILENCE_THRESH * 1000 / frame_duration_ms)
        max_frames     = int(MAX_RECORD_SEC * 1000 / frame_duration_ms)
        started        = False

        try:
            for _ in range(max_frames):
                raw = stream.read(frame_samples, exception_on_overflow=False)
                frames.append(raw)

                is_speech = vad.is_speech(raw, SAMPLE_RATE)

                if is_speech:
                    started       = True
                    silent_frames = 0
                elif started:
                    silent_frames += 1
                    if silent_frames >= max_silent:
                        break

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        if not frames:
            return None

        # Convert to numpy float32
        raw_bytes = b"".join(frames)
        int16     = np.frombuffer(raw_bytes, dtype=np.int16)
        float32   = int16.astype(np.float32) / 32768.0
        print(f"[VoiceListener] Captured {len(float32)/SAMPLE_RATE:.1f}s of audio")
        return float32

    def _capture_simple_fallback(self) -> Optional[np.ndarray]:
        """
        Fallback: records for a fixed duration when VAD not available.
        Uses sounddevice which is simpler to install.
        """
        import sounddevice as sd

        duration = 6  # seconds
        print(f"[VoiceListener] Recording {duration}s (fallback mode)...")
        audio = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32'
        )
        sd.wait()
        return audio.flatten()

    def save_wav(self, audio: np.ndarray, path: str):
        """Save captured audio to a WAV file (for debugging or Whisper file mode)."""
        import soundfile as sf
        sf.write(path, audio, SAMPLE_RATE)
