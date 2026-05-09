"""
ODIN-SENSE — Speaker (TTS)
Converts ODIN's text responses to speech.

Providers (configured via TTS_PROVIDER in .env):
  pyttsx3    → offline, instant, robotic voice — works on USB with no internet
  elevenlabs → high quality, natural voice, needs API key + internet
  gtts       → Google TTS, needs internet, free, decent quality

Default: pyttsx3 (offline, always available)
Upgrade path: ElevenLabs once Charles has funding/API key
"""

import os
import threading
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

TTS_PROVIDER   = os.getenv("TTS_PROVIDER", "pyttsx3")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ODIN_VOICE_ID  = os.getenv("ELEVENLABS_VOICE_ID", "")  # ElevenLabs voice ID

# pyttsx3 settings
TTS_RATE       = int(os.getenv("TTS_RATE", "175"))    # words per minute
TTS_VOLUME     = float(os.getenv("TTS_VOLUME", "0.9"))
TTS_VOICE_IDX  = int(os.getenv("TTS_VOICE_INDEX", "0"))  # 0=default, try different for deeper voice


class Speaker:

    def __init__(self):
        self._engine  = None
        self._lock    = threading.Lock()
        self._provider = TTS_PROVIDER
        self._setup()

    def _setup(self):
        if self._provider == "pyttsx3":
            self._setup_pyttsx3()

    def _setup_pyttsx3(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate",   TTS_RATE)
            self._engine.setProperty("volume", TTS_VOLUME)

            # Try to set a deeper voice
            voices = self._engine.getProperty("voices")
            if voices and TTS_VOICE_IDX < len(voices):
                self._engine.setProperty("voice", voices[TTS_VOICE_IDX].id)

        except Exception as e:
            print(f"[Speaker] pyttsx3 setup failed: {e}")
            self._engine = None

    def speak(self, text: str, blocking: bool = False):
        """
        Convert text to speech.
        blocking=False plays in background thread (default — ODIN keeps processing).
        blocking=True waits until done speaking (use for critical messages).
        """
        if not text or not text.strip():
            return

        text = self._clean_text(text)

        if blocking:
            self._speak_sync(text)
        else:
            t = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
            t.start()

    def _speak_sync(self, text: str):
        """Synchronous speech — blocks until done."""
        with self._lock:  # Prevent overlapping speech
            try:
                if self._provider == "elevenlabs" and ELEVENLABS_KEY:
                    self._speak_elevenlabs(text)
                elif self._provider == "gtts":
                    self._speak_gtts(text)
                else:
                    self._speak_pyttsx3(text)
            except Exception as e:
                print(f"[Speaker] TTS error: {e}")
                self._speak_pyttsx3(text)  # Always fallback to pyttsx3

    def _speak_pyttsx3(self, text: str):
        try:
            if not self._engine:
                self._setup_pyttsx3()
            if self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            print(f"[Speaker] pyttsx3 error: {e}")

    def _speak_elevenlabs(self, text: str):
        """ElevenLabs — natural, near-human voice. Needs API key."""
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import play

            client = ElevenLabs(api_key=ELEVENLABS_KEY)
            audio  = client.generate(
                text=text,
                voice=ODIN_VOICE_ID or "Adam",  # Deep authoritative voice
                model="eleven_turbo_v2"          # Fastest model
            )
            play(audio)
        except Exception as e:
            print(f"[Speaker] ElevenLabs failed: {e}, falling back to pyttsx3")
            self._speak_pyttsx3(text)

    def _speak_gtts(self, text: str):
        """Google TTS via gtts library — needs internet, free, decent quality."""
        try:
            from gtts import gTTS
            import pygame
            import tempfile, os

            tts = gTTS(text=text, lang="en", slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tts.save(f.name)
                tmp_path = f.name

            pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.unlink(tmp_path)

        except Exception as e:
            print(f"[Speaker] gTTS failed: {e}")
            self._speak_pyttsx3(text)

    def _clean_text(self, text: str) -> str:
        """
        Strip markdown and formatting that doesn't translate to speech.
        "**Bold text**" → "Bold text"
        "- bullet" → "bullet"
        """
        import re
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)   # Bold/italic
        text = re.sub(r"`[^`]+`", "", text)                      # Inline code
        text = re.sub(r"#{1,6}\s*", "", text)                    # Headers
        text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)  # Bullets
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)   # Links
        text = text.strip()
        return text

    def set_provider(self, provider: str):
        """Switch TTS provider at runtime."""
        self._provider = provider
        if provider == "pyttsx3":
            self._setup_pyttsx3()

    def get_voices(self) -> list:
        """List available pyttsx3 voices."""
        if not self._engine:
            return []
        return [{"id": v.id, "name": v.name} for v in self._engine.getProperty("voices")]
