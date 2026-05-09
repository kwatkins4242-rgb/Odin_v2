
"""
brain.py – The Reasoner
Calls an LLM with the current goal + screenshot and returns the next action.
"""

import base64
import json
import sys
from pathlib import Path
from openai import OpenAI

# Root Path Injection
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

# Initialize client
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url
)

def encode_image(image_path: str) -> str:
    """Convert PNG to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def ask_llm(goal: str, image_path: str) -> dict:
    """
    Send goal + screenshot to GPT-4o-mini and ask for the next action.
    """
    system_prompt = (
        "You are an AI desktop assistant. Given a user goal and a screenshot, "
        "respond with a single JSON object describing the next physical action. "
        "Allowed types: CLICK, TYPE, HOTKEY, SCROLL, DONE."
    )

    base64_image = encode_image(image_path)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"User goal: {goal}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            max_tokens=300,
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        # Parse JSON reply
        reply = response.choices[0].message.content
        return json.loads(reply)
    except Exception as e:
        print(f"[BRAIN] Error: {e}")
        # Safe fallback
        return {"type": "DONE", "description": f"Error: {str(e)}"}


