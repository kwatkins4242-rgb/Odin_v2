import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL       = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ODIN_CORE_URL      = os.getenv("ODIN_CORE_URL", "")        # leave blank for standalone

GROQ_LLM_MODEL     = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_WHISPER_MODEL = "whisper-large-v3"
OLLAMA_MODEL       = os.getenv("OLLAMA_MODEL", "llama3")

LISTEN_TIMEOUT      = int(os.getenv("LISTEN_TIMEOUT", 8))
SILENCE_THRESHOLD   = float(os.getenv("SILENCE_THRESHOLD", 0.03))
SAMPLE_RATE         = 16000
CHANNELS            = 1
CHUNK               = 1024

WAKE_WORDS = [
    "hey odin", "yo odin", "odin", "ok odin",
    "hey o-d-i-n", "odin you there", "wake up odin"
]

ODIN_PERSONA = """You are ODIN, a sharp and direct AI assistant. 
Keep voice responses concise — 1-3 sentences max unless asked for detail.
You are running on the user's local machine as their personal AI companion."""