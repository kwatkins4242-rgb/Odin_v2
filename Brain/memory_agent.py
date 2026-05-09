import json
import logging
from pathlib import Path
from datetime import datetime
from settings import get_settings

settings = get_settings()
logger = logging.getLogger("brain.memory")

class MemoryAgent:
    """
    Manages the persistent memory of ODIN.
    Wraps the JSON-based storage for conversations and knowledge.
    """
    
    def __init__(self):
        self.data_dir = settings.memory_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.conv_log = self.data_dir / "conversation_log.json"
        self.long_term = self.data_dir / "long_term_memory.json"
        self.knowledge = self.data_dir / "knowledge_graph.json"
        
        self._ensure_files()

    def _ensure_files(self):
        for f, default in [(self.conv_log, "[]"), (self.long_term, "{}"), (self.knowledge, "{}")]:
            if not f.exists():
                f.write_text(default, encoding="utf-8")

    def log(self, session_id: str, role: str, text: str):
        """Logs a conversation turn."""
        try:
            raw = json.loads(self.conv_log.read_text(encoding="utf-8"))
            entry = {
                "role": role,
                "content": text,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id
            }
            # Backwards compatibility with M1/main.py roles
            if role == "user":
                entry["role_user"] = text
            elif role == "assistant":
                entry["role_assistant"] = text
                
            raw.append(entry)
            if len(raw) > 500:
                raw = raw[-500:]
            self.conv_log.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to log to memory: {e}")

    def recall_relevant(self, query: str, top_k: int = 10) -> list:
        """Recalls the last k turns."""
        try:
            raw = json.loads(self.conv_log.read_text(encoding="utf-8"))
            return raw[-top_k:]
        except:
            return []

    def load_long_term(self) -> str:
        """Loads long term memory as a string."""
        try:
            data = json.loads(self.long_term.read_text(encoding="utf-8"))
            return "\n".join(f"{k}: {v}" for k, v in data.items())
        except:
            return ""

    def query_knowledge_graph(self, query: str) -> list:
        """Placeholder for KG queries."""
        return []

    def is_online(self) -> bool:
        return self.data_dir.exists()
