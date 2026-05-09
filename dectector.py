import struct, logging
import settings
from audio_manager import AudioManager

log = logging.getLogger("odin.sense.wake")

class WakeWordDetector:
    """
    Tries Porcupine first. Falls back to SpeechRecognition keyword matching.
    """
    def __init__(self, audio_manager: AudioManager):
        self.audio = audio_manager
        self.active_keywords = settings.WAKE_WORDS
        self._porcupine = None
        self._sr_fallback = False
        self._init_engine()

    def _init_engine(self):
        pv_key = getattr(settings, "PORCUPINE_KEY", "")
        if pv_key:
            try:
                import pvporcupine
                self._porcupine = pvporcupine.create(
                    access_key=pv_key,
                    keywords=["hey siri"],  # swap with custom .ppn when ready
                )
                log.info("Porcupine wake word engine loaded")
                return
            except Exception as e:
                log.warning(f"Porcupine unavailable: {e}")

        # SpeechRecognition fallback
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._mic = sr.Microphone(sample_rate=settings.SAMPLE_RATE)
            self._sr_fallback = True
            log.info("Wake word: using SpeechRecognition keyword fallback")
        except Exception as e:
            log.error(f"SpeechRecognition fallback also failed: {e}")

    def listen_for_wake(self) -> str | None:
        if self._porcupine:
            return self._porcupine_listen()
        elif self._sr_fallback:
            return self._sr_listen()
        return None

    def _porcupine_listen(self) -> str | None:
        stream = self.audio.open_stream()
        try:
            while True:
                pcm = stream.read(self._porcupine.frame_length, exception_on_overflow=False)
                pcm_unpacked = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
                idx = self._porcupine.process(pcm_unpacked)
                if idx >= 0:
                    return "hey odin"
        finally:
            self.audio.close_stream()

    def _sr_listen(self) -> str | None:
        import speech_recognition as sr
        with self._mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = self._recognizer.listen(source, timeout=None, phrase_time_limit=4)
                text = self._recognizer.recognize_google(audio).lower()
                log.debug(f"SR heard: {text}")
                for kw in self.active_keywords:
                    if kw in text:
                        return kw
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                log.warning(f"SR service error: {e}")
        return None

    def cleanup(self):
        if self._porcupine:
            self._porcupine.delete()