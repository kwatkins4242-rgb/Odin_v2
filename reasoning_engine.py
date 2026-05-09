from typing import List, Dict, Any, Optional
import asyncio
import logging
from enum import Enum
from openai import OpenAI
from settings import get_settings

settings = get_settings()
logger = logging.getLogger("odin.brain.reasoning")

class ReasoningMode(Enum):
    PRACTICAL = "practical"      # How do I fix the dishwasher?
    ETHICAL = "ethical"          # Should I tell the truth here?
    CREATIVE = "creative"        # How do we celebrate Grandma's birthday?
    GENERATIONAL = "generational" # What will this mean in 20 years?

class ReasoningEngine:
    """
    Multi-layered thinking that considers not just the immediate,
    but the temporal, relational, and ethical dimensions.
    Powered by Moonshot Kimi K2 Thinking Turbo.
    """
    
    def __init__(self, compassion_engine):
        self.compassion = compassion_engine
        self.client = None
        if settings.moonshot_api_key:
            self.client = OpenAI(
                api_key=settings.moonshot_api_key,
                base_url=settings.moonshot_base_url
            )
        self.reasoning_chain = []
        
    async def think_deeply(self, query: str, context: Dict, mode: ReasoningMode = ReasoningMode.PRACTICAL) -> Dict:
        """
        The 'large brain' thinking process.
        Uses Moonshot Kimi K2 Thinking Turbo for step-by-step reasoning.
        """
        if not self.client:
            return {
                'conclusion': "Sir, my reasoning engine is offline (Moonshot API key missing).",
                'confidence': 0.0,
                'reasoning_path': ["Failed to initialize Kimi client."],
                'concerns': ["API connection error"],
                'alternatives': []
            }

        logger.info(f"[Reasoning] Deep thinking initiated: mode={mode.value} | query={query[:50]}")

        # Layer 1: Immediate Analysis & Fact Gathering
        facts = await self._gather_facts(query, context)
        
        # Layer 2: Deep Reasoning Call (Kimi K2)
        try:
            # Construct the deep thinking prompt
            system_prompt = self._build_thinking_prompt(facts, context, mode)
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="kimi-k2-thinking-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3, # Lower temperature for reasoning
                max_tokens=4000
            )
            
            thought_output = response.choices[0].message.content
            logger.info("[Reasoning] ✓ Kimi K2 thinking complete")
            
            # Layer 3: Ethical & Compassion Filtering
            # Pass the Kimi thought through the compassion engine logic
            # This follows the pattern in your original file where compassion optimizes the path
            final_path = self.compassion.optimize_reasoning_path([{'outcome': thought_output}], context)
            
            return {
                'conclusion': final_path.get('best_action', thought_output),
                'confidence': 0.95,
                'reasoning_path': [f"Kimi Thinking: {thought_output[:100]}..."],
                'concerns': [],
                'alternatives': []
            }

        except Exception as e:
            logger.error(f"[Reasoning] ✗ Deep thinking failed: {e}")
            return {
                'conclusion': f"Sir, I encountered an error during deep reasoning: {str(e)}",
                'confidence': 0.1,
                'reasoning_path': ["Kimi API call failed."],
                'concerns': [str(e)],
                'alternatives': []
            }
        
    def _build_thinking_prompt(self, facts: Dict, context: Dict, mode: ReasoningMode) -> str:
        """Constructs the system prompt for the Kimi K2 model."""
        prompt = (
            "You are the Reasoning Core of ODIN. Your goal is to process information "
            "with extreme depth and accuracy. Think step-by-step.\n\n"
            f"REASONING MODE: {mode.value.upper()}\n"
            "COGNITIVE LAYERS:\n"
            "- Internal Logic: Ensure the solution is technically sound.\n"
            "- Temporal Impact: Consider consequences 10-20 years into the future.\n"
            "- Relational Value: Protect the unity and legacy of Charles's family.\n\n"
            "CONTEXT DATA:\n"
            f"{facts}\n"
        )
        if mode == ReasoningMode.GENERATIONAL:
            prompt += "PRIORITY: Weight your reasoning heavily toward long-term legacy and family stability."
            
        return prompt

    async def _gather_facts(self, query: str, context: Dict) -> Dict:
        """Gathers available facts from context and query."""
        return {
            "query": query,
            "speaker": context.get("speaker_id", "unknown"),
            "timestamp": context.get("timestamp", ""),
            "memory_context": context.get("memory_context", "")
        }

    def _narrate_thought_process(self, final_path):
        return ["Analyzed context.", "Simulated paths with Kimi K2.", "Chose most compassionate future."]