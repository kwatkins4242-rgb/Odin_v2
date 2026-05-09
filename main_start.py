import sys
import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

# Import Tom's logic
import brain
import tools
import vision
import voice

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ODIN — Agent Tom Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Mission(BaseModel):
    goal: str

class AgentState:
    def __init__(self):
        self.active = False
        self.current_goal = ""
        self.last_action = "Idle"
        self.status = "standby"
        self.awaiting_confirmation = False
        self.pending_action = None
        self.trusted_mode = False

state = AgentState()

async def ooda_loop(goal: str):
    state.active = True
    state.current_goal = goal
    state.status = "running"
    state.trusted_mode = settings.tom_auto_trust  # Initialize from global config
    voice.speak(f"Agent Tom initialized. Mission: {goal}")
    
    try:
        while state.active:
            # 1. OBSERVE
            state.status = "observing"
            screenshot_path = vision.capture_screen(resize_to=settings.tom_max_screen_width)
            
            # 2. DECIDE
            state.status = "deciding"
            action = brain.ask_llm(goal, screenshot_path)
            state.last_action = str(action)
            
            # 3. INTERLOCK (Safety Confirmation)
            act_type = action.get("type", "").upper()
            if act_type in ["CLICK", "TYPE", "HOTKEY", "SCROLL"] and not state.trusted_mode:
                pending_desc = action.get("description", f"perform {act_type}")
                state.status = f"waiting: {pending_desc}"
                state.awaiting_confirmation = True
                state.pending_action = action
                voice.speak(f"I am requesting permission to {act_type}. Please confirm on the dashboard.")
                
                # Wait indefinitely for user signal
                while state.awaiting_confirmation and state.active and not state.trusted_mode:
                    await asyncio.sleep(0.5)
                
                if not state.active:
                    break
            
            # 4. ACT
            if action.get("type") == "DONE":
                voice.speak("Mission accomplished.")
                state.status = "complete"
                break
            
            state.status = "acting"
            tools.execute_action(action)
            state.pending_action = None
            
            # 4. WAIT
            state.status = "waiting"
            await asyncio.sleep(settings.tom_loop_delay)
            
    except Exception as e:
        print(f"[TOM] Error: {e}")
        state.status = f"error: {str(e)}"
    finally:
        state.active = False

@app.get("/", response_class=HTMLResponse)
async def root():
    return f"""
    <html>
        <head><title>ODIN — Agent Tom Service</title></head>
        <body style="background:#0a0b0f; color:#e8e9f0; font-family:monospace; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0;">
            <h1 style="color:#7f77dd;">AGENT TOM — API SERVICE</h1>
            <p>Port 8060 is for headless API operations.</p>
            <p>To work with Tom, please use the <b>Master Hub Dashboard</b>:</p>
            <a href="http://localhost:8080/legacy.html" style="color:#5dcaa5; text-decoration:none; border:1px solid #5dcaa5; padding:10px 20px; border-radius:4px; margin-top:20px;">OPEN WORKSTATION</a>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    return {
        "status": "online",
        "agent": "Tom",
        "state": state.__dict__
    }

@app.post("/run")
async def run_mission(mission: Mission, background_tasks: BackgroundTasks):
    if state.active:
        return {"error": "Agent is already busy with a mission."}
    
    background_tasks.add_task(ooda_loop, mission.goal)
    return {"message": "Mission accepted.", "goal": mission.goal}

@app.post("/confirm")
async def confirm_action():
    if not state.awaiting_confirmation:
        return {"error": "No action is currently pending confirmation."}
    state.awaiting_confirmation = False
    return {"message": "Action confirmed. Resuming loop."}

@app.post("/trust")
async def trust_agent():
    state.trusted_mode = True
    state.awaiting_confirmation = False
    return {"message": "Trust mode enabled. Tom is now autonomous for this mission."}

@app.post("/deny")
async def deny_action():
    state.active = False
    state.awaiting_confirmation = False
    state.status = "denied"
    return {"message": "Action denied. Mission aborted."}

@app.post("/stop")
async def stop_mission():
    state.active = False
    state.awaiting_confirmation = False
    state.status = "stopping"
    return {"message": "Stop signal sent to Agent Tom."}

@app.post("/tom/save")
async def save_odin_now(mode: str = "manual"):
    """Trigger an immediate iCloud-style save."""
    import heartbeat_save
    success = heartbeat_save.save_now(mode=mode)
    if success:
        return {"message": f"ODIN Save completed ({mode} mode)."}
    else:
        return {"error": "Save failed. Check logs."}

if __name__ == "__main__":
    print(f"[TOM] Starting Agent Tom Service on port {settings.port_agent_tom}...")
    
    import subprocess
    
    # Launch Workers
    workers = [
        ("Vacuum", Path(__file__).parent / "workers_vacume" / "workers_fs.py"),
        ("Heartbeat Save", Path(__file__).parent / "heartbeat_save.py"),
        ("n8n Agent Service", Path(__file__).parent.parent / "agent_n8n.py")
    ]
    
    for name, script_path in workers:
        if script_path.exists():
            print(f"[TOM] Launching {name}: {script_path}")
            # Use dedicated venv for n8n if it exists
            python_exe = sys.executable
            if name == "n8n Agent Service":
                venv_python = Path(__file__).parent.parent / ".venv_n8n" / "Scripts" / "python.exe"
                if venv_python.exists():
                    python_exe = str(venv_python)
            
            subprocess.Popen([python_exe, str(script_path)], shell=False)
        else:
            print(f"[TOM] Worker {name} NOT found at {script_path}")

    uvicorn.run(app, host="0.0.0.0", port=settings.port_agent_tom, log_level="warning")
