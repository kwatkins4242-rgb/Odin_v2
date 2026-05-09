

import pyttsx3
import threading
import queue
import logging

log = logging.getLogger("tom.voice")

# Speech queue and background thread
_speech_queue = queue.Queue()
_worker_thread = None

def _voice_worker():
    """Background worker that owns the TTS engine."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        while True:
            text = _speech_queue.get()
            if text is None: break # Shutdown signal
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[VOICE ERROR] {e}")
            _speech_queue.task_done()
    except Exception as e:
        print(f"[VOICE FATAL] Engine init failed: {e}")

def speak(text: str) -> None:
    """Non-blocking call to say something."""
    global _worker_thread
    print(f"[VOICE] {text}")
    
    # Lazy-start the worker thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_thread = threading.Thread(target=_voice_worker, daemon=True)
        _worker_thread.start()
        
    _speech_queue.put(text)











