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
    """Get the weather in a location"""
    import random
    temp = 72 + random.randint(-10, 10)
    return {
        "location": location,
        "temperature": temp,
        "unit": "Fahrenheit"
    }

def run_tool_call():
    print(f"--- ODIN Tool Call (Provider: {AI_PROVIDER}) ---")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    messages = [{"role": "user", "content": "What is the weather in San Francisco?"}]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            print("Tool call detected!")
            available_functions = {
                "get_weather": get_weather,
            }
            
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"Calling function: {function_name} with args: {function_args}")
                function_response = function_to_call(**function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response),
                })
            
            second_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
            )
            print("\nFinal Response:")
            print(second_response.choices[0].message.content)
        else:
            print("\nFinal Response:")
            print(response_message.content)

    except Exception as e:
        print(f"Error during tool call execution: {e}")

if __name__ == "__main__":
    run_tool_call()
