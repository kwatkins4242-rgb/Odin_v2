import io, logging, tempfile, wave
from groq import Groq
import settings

log = logging.getLogger("odin.sense.transcriber")

class Transcriber:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def transcribe(self, audio_data: bytes) -> str:
        try:
            # Write raw PCM to a temp WAV file for Groq
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                with wave.open(f, "wb") as wf:
                    wf.setnchannels(settings.CHANNELS)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(settings.SAMPLE_RATE)
                    wf.writeframes(audio_data)
                tmp_path = f.name

            with open(tmp_path, "rb") as audio_file:
                result = self.client.audio.transcriptions.create(
                    model=settings.GROQ_WHISPER_MODEL,
                    file=audio_file,
                    language="en",
                )
            return result.text.strip()

        except Exception as e:
            log.error(f"Transcription error: {e}")
            return ""