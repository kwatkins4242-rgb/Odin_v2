from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import Dict, Any, List
import google.genai as genai  

# Configure Gemini API if the key exists
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = "gemini-1.5-pro"  # or gemini-1.5-flash
else:
    gemini_model = None


app = FastAPI(title="ODIN Comms API", description="Communication Bridge for ODIN System")

# Global state hold for ODIN-COMMS
odin_comms_state: Dict[str, Any] = {}

def set_comms_state(state: dict):
    """Called by main.py to inject the global comms state into the API server."""
    global odin_comms_state
    odin_comms_state = state

# --- Models ---
class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

class DeviceCommand(BaseModel):
    device_id: str
    command: str
    args: dict = {}

# --- Base Endpoints ---

@app.get("/")
async def root():
    return {"status": "online", "module": "ODIN-COMMS"}

@app.get("/status")
async def get_status():
    """Return the current global state of ODIN COMMS."""
    return odin_comms_state

# --- Device Control ---

@app.get("/devices")
async def get_devices():
    """Return lists of known, nearby, and connected devices."""
    return {
        "known": odin_comms_state.get("known_devices", []),
        "nearby": odin_comms_state.get("nearby_devices", []),
        "connected": odin_comms_state.get("connected_devices", []),
    }

@app.post("/devices/command")
async def send_device_command(cmd: DeviceCommand):
    """
    Placeholder for sending a command to a specific device.
    In the future, this will route the command to the appropriate protocol manager.
    """
    odin_comms_state.setdefault("pending_commands", []).append({
        "device_id": cmd.device_id,
        "command": cmd.command,
        "args": cmd.args,
        "status": "pending"
    })
    return {"status": "queued", "device": cmd.device_id, "command": cmd.command}

# --- Gemini Integration ---

@app.post("/ai/chat", response_model=ChatResponse)
async def chat_with_gemini(req: ChatRequest):
    """
    A basic integration with Google Gemini API for general AI assistance via COMMS.
    Requires GEMINI_API_KEY in the .env file.
    """
    if not gemini_model:
        raise HTTPException(status_code=503, detail="Gemini API is not configured. Missing GEMINI_API_KEY.")
    
    try:
        model = genai.GenerativeModel(gemini_model)
        # Using generate_content for a simple conversational or query turn
        response = model.generate_content(req.prompt)
        return ChatResponse(response=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
