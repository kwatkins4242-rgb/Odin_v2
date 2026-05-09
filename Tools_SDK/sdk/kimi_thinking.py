import os
import openai

client = openai.Client(
    base_url="https://api.moonshot.ai/v1",
    api_key=os.getenv("MOONSHOT_API_KEY"),
)

stream = client.chat.completions.create(
    model="kimi-k2-thinking",
    messages=[
        {
            "role": "system",
            "content": "You are Kimi.",
        },
        {
            "role": "user",
            "content": "Please explain why 1+1=2."
        },
    ],
    max_tokens=1024*32,
    stream=True,
    temperature=1.0,
)

thinking = False
for chunk in stream:
    if chunk.choices:
        choice = chunk.choices[0]
        if choice.delta and hasattr(choice.delta, "reasoning_content"):
            if not thinking:
                thinking = True
                print("=============Start Reasoning=============")
            print(getattr(choice.delta, "reasoning_content"), end="")
        if choice.delta and choice.delta.content:
            if thinking:
                thinking = False
                print("\n=============End Reasoning=============")
            print(choice.delta.content, end="")