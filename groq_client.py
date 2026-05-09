import logging
import requests
from groq import Groq
import settings

log = logging.getLogger("odin.sense.llm")

class GroqClient:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model  = settings.GROQ_LLM_MODEL
        self.history = []

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        messages = [{"role": "system", "content": settings.ODIN_PERSONA}] + self.history[-10:]

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7,
            )
            reply = resp.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply

        except Exception as e:
            log.warning(f"Groq failed: {e} — trying Ollama fallback")
            return self._ollama_fallback(user_text)

    def _ollama_fallback(self, text: str) -> str:
        try:
            r = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": text, "stream": False},
                timeout=30,
            )
            return r.json().get("response", "").strip()
        except Exception as e:
            log.error(f"Ollama fallback also failed: {e}")
            return "I'm having trouble connecting right now."