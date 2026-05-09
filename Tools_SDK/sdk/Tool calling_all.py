#!/usr/bin/env python3
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from .env
AI_PROVIDER = os.getenv("AI_PROVIDER", "MOONSHOT")
API_KEY = os.getenv(f"{AI_PROVIDER}_API_KEY")
BASE_URL = os.getenv(f"{AI_PROVIDER}_BASE_URL")
MODEL = os.getenv(f"{AI_PROVIDER}_MODEL")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def get_weather(location: str):
    """Get the weather for a location"""
    return {"temperature": 72, "condition": "sunny", "location": location}

def run_all_tool_calls():
    print(f"--- ODIN Tool Calling All (Provider: {AI_PROVIDER}) ---")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and state"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    # Example 1: Weather in SF
    messages = [{"role": "user", "content": "What is the weather in San Francisco?"}]
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        
        msg = response.choices[0].message
        if msg.tool_calls:
            print(f"Tool Call: {msg.tool_calls[0].function.name}({msg.tool_calls[0].function.arguments})")
            res = get_weather(**json.loads(msg.tool_calls[0].function.arguments))
            print(f"Result: {res}")
        else:
            print(f"Response: {msg.content}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_all_tool_calls()
