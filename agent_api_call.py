import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from root (three levels up)
env_path = Path(__file__).parent / ".." / ".." / ".." / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
MAX_SCREEN_WIDTH = 1024          # Resize screenshots to this width (keeps aspect ratio)
LOOP_DELAY       = 2             # Seconds between iterations
