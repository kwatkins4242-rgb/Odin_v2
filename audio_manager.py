import pyaudio, logging
import settings

log = logging.getLogger("odin.sense.audio")

class AudioManager:
    def __init__(self):
        self.pa     = None
        self.stream = None

    def init(self) -> bool:
        try:
            self.pa = pyaudio.PyAudio()
            # Quick test — open and close
            test = self.pa.open(
                format=pyaudio.paInt16,
                channels=settings.CHANNELS,
                rate=settings.SAMPLE_RATE,
                input=True,
                frames_per_buffer=settings.CHUNK,
            )
            test.close()
            log.info("Audio initialized OK")
            return True
        except Exception as e:
            log.error(f"Audio init failed: {e}")
            return False

    def open_stream(self):
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=settings.CHANNELS,
            rate=settings.SAMPLE_RATE,
            input=True,
            frames_per_buffer=settings.CHUNK,
        )
        return self.stream

    def read_chunk(self) -> bytes:
        if not self.stream:
            return b""
        return self.stream.read(settings.CHUNK, exception_on_overflow=False)

    def close_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def cleanup(self):
        self.close_stream()
        if self.pa:
            self.pa.terminate()