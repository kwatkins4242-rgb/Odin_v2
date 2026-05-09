import os
import json
import time
import openai

# Locate providers.json and load key
providers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'providers.json'))

try:
    with open(providers_path, 'r') as f:
        providers = json.load(f)
        moonshot_config = providers.get('moonshot', {})
        api_key = moonshot_config.get('api_key')
except FileNotFoundError:
    print(f"Error: Could not find providers.json at {providers_path}")
    exit(1)

if not api_key:
    print("Error: No moonshot API key found in providers.json. Please add it first.")
    exit(1)

# Initialize Kimi / Moonshot Client
client = openai.Client(
    base_url="https://api.moonshot.ai/v1",
    api_key=api_key,
)

# You can adjust this to "moonshot-v1-8k" if you want the absolute cheapest, 
# or use the "kimi-k2-turbo-preview" you specified.
# Kimi K2 series model names include "kimi-k2-thinking", "kimi-k2-turbo-preview", etc.
MODEL_NAME = "kimi-k2-turbo-preview"

print(f"Starting endless worker with Kimi ({MODEL_NAME})...")
print("Press Ctrl+C to stop the agent before you go broke!\n")

iteration = 0
while True:
    iteration += 1
    print(f"=======================================")
    print(f"       TASK EXECUTION #{iteration}")
    print(f"=======================================")
    
    try:
        # The prompt loop for the continuous agent
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an autonomous AI worker for ODIN. Your goal is to generate unique, actionable insights and log your reasoning process."},
                {"role": "user", "content": f"Generate a detailed technical or creative insight for iteration {iteration}. Make it completely different from previous iterations."}
            ],
            max_tokens=4000,
            stream=True,
            temperature=0.9,
        )

        thinking = False
        print("💡 Output:")
        for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                
                # Check for reasoning_content (K2 Thinking feature)
                if choice.delta and hasattr(choice.delta, 'reasoning_content') and choice.delta.reasoning_content:
                    if not thinking:
                        thinking = True
                        print("\n[Thinking Process Started...]")
                    print(getattr(choice.delta, 'reasoning_content'), end="", flush=True)
                
                # Standard content
                if choice.delta and choice.delta.content:
                    if thinking:
                        thinking = False
                        print("\n\n[Final Answer Started...]")
                    print(choice.delta.content, end="", flush=True)
                    
        print("\n\n[Task Complete. Resting before the next iteration...]\n")
        time.sleep(15) # Wait 15 seconds before hitting the API again

    except Exception as e:
        print(f"\n[!] Error encountered: {e}")
        print("Retrying in 30 seconds...")
        time.sleep(30)
