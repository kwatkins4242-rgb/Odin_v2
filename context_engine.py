# orchestrator/context_engine.py
"""
Keeps the last N turns and injects them into prompts.
"""

from collections import deque
from typing import List, Dict, Any

class ContextEngine:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self.sessions: Dict[str, deque] = {}  # session_id -> deque

    def add(self, session_id: str, role: str, text: str):
        """role: 'user' | 'assistant'"""
        if session_id not in self.sessions:
            self.sessions[session_id] = deque(maxlen=self.max_turns)
        self.sessions[session_id].append({"role": role, "text": text})

    def get(self, session_id: str) -> List[Dict[str, str]]:
        return list(self.sessions.get(session_id, []))

    def clear(self, session_id: str):
        self.sessions.pop(session_id, None)
