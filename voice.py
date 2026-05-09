
"""
voice.py – The Mouth
Very small TTS helper.
"""

import pyttsx3

# Initialize once and reuse
_engine = pyttsx3.init()
_engine.setProperty("rate", 180)  # Words per minute

def speak(text: str) -> None:
    """Non-blocking call to say something."""
    print(f"[VOICE] {text}")
    _engine.say(text)
    _engine.runAndWait()

