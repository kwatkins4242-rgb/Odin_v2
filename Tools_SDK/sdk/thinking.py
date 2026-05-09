#!/usr/bin/env python3
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "MOONSHOT")
API_KEY = os.getenv(f"{AI_PROVIDER}_API_KEY")
BASE_URL = os.getenv(f"{AI_PROVIDER}_BASE_URL")
MODEL = os.getenv(f"{AI_PROVIDER}_MODEL")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def get_thinking(prompt: str):
    """Generate reasoning/thought using the current agent model"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are ODIN's internal reasoning module. Think deeply and logically."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Thinking Error: {e}"

if __name__ == "__main__":
    print(get_thinking("Explain the ODIN modular architecture briefly."))
