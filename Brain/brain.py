import logging
import json
from typing import Dict, Any

# Local Brain Imports
from .memory_agent import MemoryAgent
from .compassion_engine import CompassionEngine, FamilyContext
from .reasoning_engine import ReasoningEngine, ReasoningMode
from .cognitive_memory_bridge import CognitiveMemoryBridge
from .context_engine import ContextEngine

logger = logging.getLogger("odin.brain")

class OdinBrain:
    """
    The central cortex. Receives input from the FastAPI router,
    thinks with compassion, reasons with Kimi K2, and remembers with purpose.
    """
    
    def __init__(self):
        self.memory = MemoryAgent()
        self.compassion = CompassionEngine(self.memory)
        self.reasoning = ReasoningEngine(self.compassion)
        self.memory_bridge = CognitiveMemoryBridge(self.memory)
        self.context = ContextEngine(max_turns=10)
        
    async def process(self, session_id: str, message: str, raw_context: dict = None) -> dict:
        """
        Main cognitive loop:
        Contextualize -> Feel -> Think -> Remember -> Respond
        """
        if raw_context is None:
            raw_context = {}
            
        logger.info(f"[Brain] Processing turn for session={session_id}")

        # ── Command Interception ──────────────────────────
        if message.strip().lower() == "save_odin_now":
            logger.info("[Brain] External command triggered: save_odin_now")
            try:
                import requests
                from settings import get_settings
                s = get_settings()
                resp = requests.post(f"http://localhost:{s.port_agent_tom}/tom/save?mode=manual", timeout=15)
                if resp.ok:
                    return {"response": "ODIN project saved and overridden successfully. iCloud mode status: OK."}
                else:
                    return {"response": f"Save command failed: {resp.text}"}
            except Exception as e:
                return {"response": f"Error triggering save: {str(e)}"}

        # 1. Contextualize (Identify role, emotional state, etc.)
        family_context = await self._build_family_context(session_id, message, raw_context)
        
        # 2. Feel (Compassion check - check presence weight)
        presence_weight = self.compassion.calculate_presence_weight(family_context)
        
        # 0.1 is 'maximal availability, minimal presence' (e.g. grieving)
        if presence_weight < 0.2:
            # We still reason, but maybe the response is adjusted
            logger.info("[Brain] Low presence weight detected (Sacred Space)")

        # 3. Think (Gather memory, reason deeply with Kimi K2)
        thinking_context = await self.memory_bridge.build_thinking_context(
            message, family_context.speaker_id
        )
        # Update thinking context with session history from context engine
        thinking_context["session_history"] = self.context.get(session_id)
        
        thought = await self.reasoning.think_deeply(
            query=message,
            context=thinking_context,
            mode=ReasoningMode.GENERATIONAL if "family" in message.lower() else ReasoningMode.PRACTICAL
        )
        
        # 4. Remember & Respond
        response_text = thought['conclusion']
        
        # Log to memory agent
        self.memory.log(session_id, "user", message)
        self.memory.log(session_id, "assistant", response_text)
        
        # Update session context engine
        self.context.add(session_id, "user", message)
        self.context.add(session_id, "assistant", response_text)

        # Record wisdom if confidence is high
        if thought.get('confidence', 0) > 0.8:
            await self.memory_bridge.store_wisdom(
                interaction={"speaker_id": family_context.speaker_id, "summary": message},
                reflection=response_text
            )
        
        return {
            "response": response_text,
            "thought_process": thought.get('reasoning_path', []),
            "confidence": thought.get('confidence', 0)
        }

    async def _build_family_context(self, session_id: str, message: str, raw_context: dict) -> FamilyContext:
        """Determines the family role and emotional state of the speaker."""
        # This would eventually call a speaker identification module
        # For now, we use defaults or data passed from the UI
        return FamilyContext(
            speaker_id=session_id,
            generational_role=raw_context.get("role", "guest"),
            emotional_state=raw_context.get("mood", "neutral"),
            conversation_history_depth=len(self.context.get(session_id)),
            sacred_topics=[]
        )

# Global singleton
_brain = None

def get_brain():
    global _brain
    if _brain is None:
        _brain = OdinBrain()
    return _brain