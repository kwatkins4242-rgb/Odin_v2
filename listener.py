import struct, array, logging, time
import pyaudio
import settings
from audio_manager import AudioManager

log = logging.getLogger("odin.sense.listener")

class VoiceListener:
    def __init__(self, audio_manager: AudioManager):
        self.audio = audio_manager

    def capture(self, timeout: int = 8, silence_threshold: float = 0.03) -> bytes | None:
        """Capture audio until silence or timeout. Returns raw PCM bytes."""
        log.info("Listening for speech...")
        stream = self.audio.open_stream()
        frames = []
        silent_chunks = 0
        max_silent = int(settings.SAMPLE_RATE / settings.CHUNK * 1.5)  # 1.5s silence
        start = time.time()

        try:
            while True:
                if time.time() - start > timeout:
                    log.info("Listener timed out")
                    break

                chunk = stream.read(settings.CHUNK, exception_on_overflow=False)
                frames.append(chunk)

                # RMS energy check for silence detection
                data = array.array("h", chunk)
                rms = (sum(x * x for x in data) / len(data)) ** 0.5 / 32768
                if rms < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0

                if silent_chunks >= max_silent and len(frames) > 10:
                    log.info("Silence detected — done capturing")
                    break

        finally:
            self.audio.close_stream()

        if len(frames) < 5:
            return None

        return b"".join(frames)