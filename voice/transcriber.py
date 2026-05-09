"""
ODIN-SENSE — Whisper Transcriber
Converts audio to text using OpenAI Whisper running locally.
No API calls — runs on your hardware, stays private.

Model sizes (speed vs accuracy):
  tiny   → fastest, lowest accuracy (~39MB)
  base   → good balance for conversation (~74MB)  ← DEFAULT
  small  → better accuracy, still fast (~244MB)
  medium → excellent (~769MB)
  large  → best quality, slow (~1.5GB) — good for a dedicated server

Set WHISPER_MODEL in .env to choose.
"""

import os
import numpy as np
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

WHISPER_MODEL    = os.getenv("WHISPER_MODEL", "base")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")  # Forced English for speed
SAMPLE_RATE      = 16000


class Transcriber:

    def __init__(self):
        self._model  = None
        self._loaded = False
        self._load_model()

    def _load_model(self):
        """Load Whisper model on startup. Cached after first load."""
        try:
            import whisper
            print(f"[Transcriber] Loading Whisper '{WHISPER_MODEL}' model...")
            self._model  = whisper.load_model(WHISPER_MODEL)
            self._loaded = True
            print(f"[Transcriber] Whisper ready")
        except ImportError:
            print("[Transcriber] whisper not installed — will use fallback")
        except Exception as e:
            print(f"[Transcriber] Failed to load Whisper: {e}")

    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        """
        Transcribe a numpy float32 audio array to text.
        Returns cleaned transcript string or None.
        """
        if audio is None or len(audio) == 0:
            return None

        # Trim leading/trailing silence
        audio = self._trim_silence(audio)
        if len(audio) < SAMPLE_RATE * 0.3:  # Less than 0.3s — too short
            return None

        if self._loaded and self._model:
            return self._transcribe_whisper(audio)
        else:
            return self._transcribe_fallback(audio)

    def _transcribe_whisper(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe using local Whisper model."""
        try:
            import whisper
            start = time.time()

            result = self._model.transcribe(
                audio,
                language=WHISPER_LANGUAGE,
                fp16=False,  # CPU-safe
                condition_on_previous_text=False,  # Faster
                verbose=False
            )

            text     = result.get("text", "").strip()
            duration = time.time() - start
            print(f"[Transcriber] Transcribed in {duration:.2f}s: \"{text[:60]}\"")

            # Filter noise/hallucinations Whisper sometimes produces
            if self._is_noise(text):
                return None

            return text if text else None

        except Exception as e:
            print(f"[Transcriber] Whisper error: {e}")
            return None

    def _transcribe_fallback(self, audio: np.ndarray) -> Optional[str]:
        """
        Fallback using SpeechRecognition (uses Google STT API — needs internet).
        Only used when Whisper is unavailable.
        """
        try:
            import speech_recognition as sr
            import soundfile as sf
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, audio, SAMPLE_RATE)
                tmp_path = f.name

            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data)
            os.unlink(tmp_path)
            return text.strip() if text else None

        except Exception as e:
            print(f"[Transcriber] Fallback STT failed: {e}")
            return None

    def _trim_silence(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Trim leading and trailing silence from audio."""
        mask   = np.abs(audio) > threshold
        if not np.any(mask):
            return audio
        start  = np.argmax(mask)
        end    = len(mask) - np.argmax(mask[::-1])
        return audio[start:end]

    def _is_noise(self, text: str) -> bool:
        """
        Filter Whisper hallucinations — common artifacts it produces on silence.
        """
        HALLUCINATIONS = {
            "thank you", "thanks for watching", "you", "bye", "okay",
            ".", ",", "...", "um", "uh", "hmm", "[music]", "[applause]",
            "subtitles by", "transcribed by", "www."
        }
        stripped = text.lower().strip(" .,!?")
        return stripped in HALLUCINATIONS or len(stripped) < 2

    def is_ready(self) -> bool:
        return self._loaded
