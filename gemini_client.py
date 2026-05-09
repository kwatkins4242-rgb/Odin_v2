import logging
import requests
import settings
from google import genai
from google.genai import types

log = logging.getLogger("odin.sense.llm.gemini")

class GeminiClient:
    def __init__(self):
        if not getattr(settings, "GEMINI_API_KEY", None):
            raise ValueError("GEMINI_API_KEY not set in .env")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        
        try:
            self.chat_session = self.client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=settings.ODIN_PERSONA,
                    temperature=0.7,
                    max_output_tokens=300,
                )
            )
            log.info("GeminiClient initialized successfully.")
        except Exception as e:
            log.error(f"Failed to init Gemini chat session: {e}")
            self.chat_session = None

    def chat(self, user_text: str) -> str:
        if not self.chat_session:
            return self._fallback(user_text)

        try:
            response = self.chat_session.send_message(user_text)
            reply = response.text.strip()
            return reply
        except Exception as e:
            log.warning(f"Gemini failed: {e} — trying Ollama fallback")
            return self._fallback(user_text)

    def _fallback(self, text: str) -> str:
        try:
            r = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": text, "stream": False},
                timeout=30,
            )
            return r.json().get("response", "").strip()
        except Exception as e:
            log.error(f"Ollama fallback failed: {e}")
            return "I'm completely disconnected right now."
