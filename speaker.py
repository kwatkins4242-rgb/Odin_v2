import logging, threading
import pyttsx3

log = logging.getLogger("odin.sense.speaker")

class Speaker:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty("voices")
            # Pick a deeper/male voice if available
            for v in voices:
                if "david" in v.name.lower() or "male" in v.name.lower():
                    self.engine.setProperty("voice", v.id)
                    break
            self.engine.setProperty("rate", 185)
            self.engine.setProperty("volume", 0.9)
            log.info("Speaker (pyttsx3) initialized")
        except Exception as e:
            log.error(f"Speaker init failed: {e}")
            self.engine = None

    def say(self, text: str):
        if not self.engine:
            log.warning(f"[TTS offline] Would say: {text}")
            return
        log.info(f"Speaking: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            log.error(f"TTS error: {e}")