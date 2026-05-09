"""
ODIN-SENSE | Main Entry Point
Groq Whisper (STT) → Groq Llama (LLM) → Ollama fallback
"""
import sys, time, signal, logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("odin_sense.log", encoding="utf-8")],
)
log = logging.getLogger("odin.sense")

_running = True
def _shutdown(sig, frame):
    global _running
    log.info("Shutdown — stopping ODIN-SENSE...")
    _running = False

signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

def boot():
    log.info("=" * 50)
    log.info("  ODIN-SENSE  |  Booting...")
    log.info("=" * 50)

    from audio.audio_manager import AudioManager
    from wake_word.detector import WakeWordDetector
    from voice.listener import VoiceListener
    from voice.transcriber import Transcriber
    from voice.speaker import Speaker
    from config import settings

    audio = AudioManager()
    if not audio.init():
        log.error("Audio init failed — check mic permissions")
        sys.exit(1)

    wake = WakeWordDetector(audio_manager=audio)
    listener = VoiceListener(audio_manager=audio)
    transcriber = Transcriber()
    speaker = Speaker()

    log.info(f"LIVE | Wake words: {wake.active_keywords}")
    speaker.say("ODIN sense online.")

    global _running
    while _running:
        try:
            triggered = wake.listen_for_wake()
            if not triggered:
                continue

            log.info(f"Wake word: '{triggered}'")
            speaker.say("Yeah?")

            audio_data = listener.capture(timeout=settings.LISTEN_TIMEOUT)
            if audio_data is None:
                continue

            text = transcriber.transcribe(audio_data)
            if not text or not text.strip():
                continue

            log.info(f'Heard: "{text}"')
            _route(text, speaker, settings)

        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"Loop error: {e}", exc_info=True)
            time.sleep(1)

    audio.cleanup()
    wake.cleanup()
    log.info("ODIN-SENSE offline.")

def _route(text, speaker, settings):
    import requests
    core_url = getattr(settings, "ODIN_CORE_URL", None)
    if core_url:
        try:
            r = requests.post(f"{core_url}/chat", json={"message": text, "source": "sense"}, timeout=10)
            if r.status_code == 200:
                reply = r.json().get("response", "")
                if reply:
                    speaker.say(reply)
                return
        except requests.RequestException as e:
            log.warning(f"Core unreachable: {e} — using LLM fallback")

    from llm.groq_client import GroqClient
    reply = GroqClient().chat(text)
    if reply:
        speaker.say(reply)

if __name__ == "__main__":
    boot()