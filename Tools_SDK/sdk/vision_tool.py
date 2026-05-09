#!/usr/bin/env python3
import os
import base64
import time
import pyautogui
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "MOONSHOT")
API_KEY = os.getenv(f"{AI_PROVIDER}_API_KEY")
BASE_URL = os.getenv(f"{AI_PROVIDER}_BASE_URL")
VISION_MODEL = os.getenv("MOONSHOT_VISION_MODEL", "moonshot-v1-8k-vision-preview")
SCREENSHOTS_DIR = os.getenv("ODIN_SCREENSHOTS_DIR", "C:\\AI\\MyOdin\\screenshots")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def capture_screen():
    """Take a screenshot and save it to the screenshots directory"""
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    
    print(f"Capturing screen to {filepath}...")
    screenshot = pyautogui.screenshot()
    screenshot.convert('RGB').save(filepath, "PNG")
    
    return filepath

def analyze_screen(filepath, prompt="Describe what is on the screen and what you see."):
    """Send a screenshot to the vision model for analysis"""
    print(f"Analyzing screen with model: {VISION_MODEL}...")
    
    base64_image = encode_image(filepath)
    
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during vision analysis: {e}"

def run_vision_loop(output_path=None):
    """Main function to demonstrate vision capability"""
    print("--- ODIN Vision Tool ---")
    
    if output_path:
        # Just capture to specific path, skip analysis for high-freq cron jobs
        if not os.path.exists(os.path.dirname(output_path)) and os.path.dirname(output_path):
            os.makedirs(os.path.dirname(output_path))
        
        screenshot = pyautogui.screenshot()
        screenshot.convert('RGB').save(output_path, "PNG")
        print(f"Captured screen to {output_path}")
        return

    filepath = capture_screen()
    analysis = analyze_screen(filepath)
    print("\nVision Analysis Results:")
    print(analysis)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ODIN Vision Tool")
    parser.add_validator = False # Suppress some defaults if needed
    parser.add_argument("--output", help="Save screenshot to specific path and exit")
    
    args = parser.parse_args()
    
    run_vision_loop(output_path=args.output)
