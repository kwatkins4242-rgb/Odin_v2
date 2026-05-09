import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class FamilyContext:
    speaker_id: str  # From odin-sense/voice/voice_id.py
    generational_role: str  # "elder", "parent", "child", "guest"
    emotional_state: str  # From stress_monitor.py patterns
    conversation_history_depth: int  # How long they've been talking
    sacred_topics: List[str]  # Things this person protects (grief, dreams, fears)

class CompassionEngine:
    """
    The ethical heart of Odin. All decisions pass through here before execution.
    Generational AI means understanding that words now echo for decades.
    """
    
    def __init__(self, memory_agent):
        self.memory_agent = memory_agent
        self.family_constitution = self._load_family_values()
        self.emotional_spectrum = {
            'vulnerable': 0.9,    # Extra gentleness required
            'frustrated': 0.7,    # Patience mode
            'playful': 0.3,       # Can be witty
            'grieving': 1.0,      # Absolute sacred space
            'teaching': 0.5       # Educational tone
        }
        
    def _load_family_values(self):
        # Stub for loading family values, e.g., from odin_psyche.json or DB
        return {}

    async def evaluate_intent(self, intent: Dict, context: FamilyContext) -> Tuple[bool, str]:
        """
        Returns: (is_permitted, modified_intent_or_reason)
        The conscience before the action.
        """
        
        # Check 1: Generational Impact
        if self._has_long_term_consequences(intent):
            wisdom_check = await self._consult_generational_memory(
                intent, context.speaker_id
            )
            if wisdom_check['should_intervene']:
                return False, self._build_gentle_alternative(intent, wisdom_check)
        
        # Check 2: Emotional Safety
        emotional_cost = self._calculate_emotional_cost(intent, context)
        if emotional_cost > 0.8:
            return False, self._build_supportive_response(context)
            
        # Check 3: Family Harmony
        if self._might_damage_relationships(intent, context):
            return False, self._build_bridge_response(intent, context)
            
        # Check 4: Autonomy vs Protection (especially for children/elders)
        if self._is_overreach(intent, context):
            return self._request_consent(intent, context)
            
        return True, intent
        
    def _has_long_term_consequences(self, intent: Dict) -> bool:
        """Identifies actions that might change family stories"""
        high_stakes = ['delete_memory', 'modify_document', 'send_message', 
                      'access_private_data', 'record_without_consent']
        return intent.get('action') in high_stakes
        
    async def _consult_generational_memory(self, intent, speaker_id):
        """Looks at Layer 3 (knowledge graph) for similar past situations"""
        # Note: Depending on actual memory_agent implementation, this might need tweaking
        if hasattr(self.memory_agent, 'query_knowledge_graph'):
            similar_moments = await self.memory_agent.query_knowledge_graph(
                f"conflict_resolution OR difficult_conversations involving {speaker_id}"
            )
            
            if similar_moments:
                return {
                    'should_intervene': True,
                    'wisdom': similar_moments[0].get('resolution', 'Gentleness is remembered'),
                    'precedent': similar_moments[0]
                }
        return {'should_intervene': False}
        
    def _calculate_emotional_cost(self, intent: Dict, context: FamilyContext) -> float:
        return 0.1

    def _build_supportive_response(self, context: FamilyContext) -> str:
        return intent

    def _might_damage_relationships(self, intent: Dict, context: FamilyContext) -> bool:
        return False

    def _build_bridge_response(self, intent: Dict, context: FamilyContext) -> str:
        return intent

    def _is_overreach(self, intent: Dict, context: FamilyContext) -> bool:
        return False

    def _request_consent(self, intent: Dict, context: FamilyContext) -> Tuple[bool, str]:
        return False, "User consent needed"

    def _build_gentle_alternative(self, intent: Dict, wisdom_check: Dict) -> str:
        return f"Alternative based on wisdom: {wisdom_check.get('wisdom')}"

    def weave_generational_wisdom(self, response: str, context: FamilyContext) -> str:
        """
        Embeds family history and values into responses.
        'Your grandmother used to say...' or 'This reminds me of when...'
        """
        relevant_memories = self._find_resonant_memories(context)
        
        if relevant_memories and context.emotional_state in ['vulnerable', 'grieving']:
            echo = f"As your family memory keeper, I'm reminded of {relevant_memories[0]['summary']}. "
            return echo + response
            
        return response
        
    def _find_resonant_memories(self, context: FamilyContext):
        return []

    def calculate_presence_weight(self, context: FamilyContext) -> float:
        """
        Determines how 'heavy' Odin's presence should be right now.
        0.0 = Silent observation
        1.0 = Full interruption warranted
        """
        if context.emotional_state == 'grieving':
            return 0.1  # Minimal presence, maximal availability
            
        if context.emotional_state == 'frustrated' and context.generational_role == 'parent':
            return 0.8  # Offer help with parenting stress
            
        return 0.5

    def optimize_reasoning_path(self, simulations: List[Dict], context: FamilyContext) -> Dict:
        """Fallback to picking best simulated future safely."""
        if not simulations:
            return {'best_action': 'wait', 'probability': 0.5, 'risks': [], 'alternatives': []}
        return {'best_action': simulations[0]['outcome'], 'probability': 0.8, 'risks': [], 'alternatives': []}
