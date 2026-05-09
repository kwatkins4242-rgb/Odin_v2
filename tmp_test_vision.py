import os
import io
import base64
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
from pathlib import Path

# Fix path to .env
env_path = Path("c:/Odin/ODIN/ODIN_CORE/.env")
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

key = os.getenv("OPENAI_API_KEY")
model = os.getenv("VISION_MODEL", "gpt-4o")

print(f"Testing Vision with model: {model}")
if not key:
    print("Error: OPENAI_API_KEY not found in .env")
    # List all env vars for debugging (careful not to show keys if possible, but I'll see the presence)
    print(f"Available keys in env: {[k for k in os.environ.keys() if 'API' in k or 'KEY' in k]}")
    exit(1)

client = OpenAI(api_key=key)

# Create a small dummy image for testing
img = Image.new('RGB', (100, 100), color='red')
buf = io.BytesIO()
img.save(buf, format='JPEG')
b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this image?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        max_tokens=100
    )
    print("Success! Vision AI response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error testing Vision: {e}")
