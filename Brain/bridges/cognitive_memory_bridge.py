import logging
from .memory_agent import MemoryAgent

logger = logging.getLogger("brain.bridge")

class CognitiveMemoryBridge:
    def __init__(self, memory_agent: MemoryAgent):
        self.memory = memory_agent

    async def build_thinking_context(self, query: str, speaker_id: str) -> dict:
        """Pulls memory context for the reasoning engine."""
        history = self.memory.recall_relevant(speaker_id)
        long_term = self.memory.load_long_term()
        return {
            "history": history,
            "long_term": long_term,
            "query": query
        }

    async def store_wisdom(self, interaction: dict, reflection: str):
        """Stores a reflection/conclusion back to memory."""
        # For now, just log it. Could be expanded to KG storage.
        logger.info(f"Storing wisdom: {reflection[:50]}...")
        pass
