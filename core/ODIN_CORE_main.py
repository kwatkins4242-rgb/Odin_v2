"""
ODIN_CORE — main.py
File: C:/AI\MyOdin\M1\core\main.py
"""

import os
import asyncio
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────
load_dotenv()

# Add root to sys.path so we can load settings
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ODIN_PORT      = settings.port_core
UPLOAD_DIR     = os.getenv("UPLOAD_DIR", r"C:\AI\MyOdin\uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Lifespan ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[CORE] Online OK")
    yield
    print("[CORE] Shutting down")


# ── App ────────────────────────────────────────────────
app = FastAPI(title="CORE", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════
#  AI PROVIDER — Moonshot Kimi K2.5 Thinking Turbo
# ═══════════════════════════════════════════════════════

async def call_ai(system: str, message: str, history: list = []) -> str:

    # 1. Tier 1: Kimi K2 Turbo (Moonshot) - The "Deep Thinker"
    if os.getenv("MOONSHOT_API_KEY"):
        try:
            import httpx
            # Use your specific MOONSHOT_BASE_URL and MOONSHOT_MODEL
            base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
            model = os.getenv("MOONSHOT_MODEL", "kimi-k2-turbo-preview")
            
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('MOONSHOT_API_KEY')}"},
                    json={
                        "model": model,
                        "messages": [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}],
                        "max_tokens": 4096, # Give it room to work
                        "temperature": 0.3
                    }
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[CORE] Kimi Turbo failed: {e} — sliding to Groq")

    # 2. Tier 2: Groq - The "Speed Demon"
    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            # Llama 3.3 70B is a great middle-ground for intelligence and speed
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system}] + history + [{"role": "user", "content": message}],
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[CORE] Groq failed: {e} — activating Gemini Pro")

    # 3. Tier 3: Gemini 1.5 Pro - The "Bad Ass" Fallback
    if os.getenv("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Use Pro (not Flash) for the heavy lifting fallback
            model = genai.GenerativeModel("gemini-1.5-pro", system_instruction=system)
            
            chat_history = []
            for h in history:
                role = "user" if h.get("role") == "user" else "model"
                chat_history.append({"role": role, "parts": [h.get("content", "")]})

            chat = model.start_chat(history=chat_history)
            return chat.send_message(message).text
        except Exception as e:
            print(f"[CORE] Gemini Pro failed: {e}")

    return "⚠ All AI systems are unresponsive. Check your API keys."
  
# ═══════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"status": "ODIN online", "version": "1.0.0", "port": ODIN_PORT}


@app.get("/health")
async def health():
    return {"ok": True}


# ── Chat (IDE + Mobile) ────────────────────────────────
@app.post("/api/chat")
async def chat(data: dict):
    message      = data.get("message", "").strip()
    history      = data.get("history", [])
    agent_mode   = data.get("agent_mode", False)
    system_extra = data.get("system_extra", "")
    file_name    = data.get("file_name", "")
    file_content = data.get("file_content", "")

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    system = "You are ODIN, a focused AI development assistant. Be direct, concise, and always produce working code."

    if agent_mode:
        system += (
            "\n\nAGENT MODE ACTIVE. When you need to create, edit, or delete files, "
            "or run a terminal command, include these XML tags AFTER your explanation:\n"
            "<odin-action type=\"create\" path=\"relative/path.ext\">file content here</odin-action>\n"
            "<odin-action type=\"edit\" path=\"relative/path.ext\">full new content</odin-action>\n"
            "<odin-action type=\"delete\" path=\"relative/path.ext\"/>\n"
            "<odin-action type=\"run\" cmd=\"command to run\"/>"
        )

    if system_extra:
        system += "\n\n" + system_extra

    if file_name and file_content:
        message += f"\n\n[Attached: {file_name}]\n{file_content[:6000]}"

    reply = await call_ai(system, message, history)
    return {"reply": reply}


# ── File Upload (Mobile) ───────────────────────────────
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    message: str = Form(""),
    filename: str = Form(""),
):
    safe_name = filename or file.filename or "upload"
    dest = os.path.join(UPLOAD_DIR, safe_name)

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = os.path.getsize(dest)
    print(f"[CORE] Received file: {safe_name} ({size} bytes)")

    # Ask AI about it if there's a message
    reply = f"Received {safe_name} ({size:,} bytes)."
    if message:
        reply = await call_ai(
            "You are ODIN. A file was just uploaded to you.",
            f"File '{safe_name}' ({size} bytes) was uploaded. User says: {message}\nRespond to what they want done with it.",
            [],
        )

    return {"reply": reply, "filename": safe_name, "size": size, "path": dest}


# ── Terminal execute — REST fallback ───────────────────
@app.post("/api/terminal/execute")
async def terminal_execute(data: dict):
    cmd = data.get("command", "").strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="command is required")

    import subprocess
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=r"C:/AI\MyOdin\M1\core",
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out (30s)", "code": 1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "code": 1}


# ── Files API (IDE file tree sync) ────────────────────
@app.get("/api/files")
async def list_files(path: str = Query(default=r"C:/AI\MyOdin\M1\core")):
    files = []
    for root, dirs, filenames in os.walk(path):
        # skip hidden / venv folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', '.venv', 'node_modules')]
        for fname in filenames:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, path).replace("\\", "/")
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                content = ""
            files.append({"path": rel, "content": content})
    return {"files": files}


@app.post("/api/files/save")
async def save_file(data: dict):
    path    = data.get("path", "")
    content = data.get("content", "")
    if not path:
        raise HTTPException(status_code=400, detail="path required")
    full = os.path.join(r"C:/AI\MyOdin\M1\core", path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return {"ok": True, "path": path}


@app.delete("/api/files/delete")
async def delete_file(data: dict):
    path = data.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path required")
    # Use local project root for deletions
    full = os.path.join(r"C:\AI\MyOdin", path)
    if os.path.isfile(full):
        os.remove(full)
        return {"ok": True, "deleted": path}
    raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn
    # Important: name is the main entry point for hot-reload or sub-process
    uvicorn.run(app, host="0.0.0.0", port=ODIN_PORT)


# ── WebSocket Terminal — real interactive shell ────────
@app.websocket("/ws/terminal")
async def ws_terminal(websocket: WebSocket):
    await websocket.accept()
    print("[ODIN_CORE] Terminal WebSocket connected")

    import asyncio, subprocess

    shell = "cmd.exe" if os.name == "nt" else "bash"
    proc = await asyncio.create_subprocess_shell(
        shell,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=r"C:\AI\MyOdin",
    )

    async def read_output():
        while True:
            try:
                data = await proc.stdout.read(1024)
                if not data:
                    break
                await websocket.send_text(data.decode("utf-8", errors="replace"))
            except Exception:
                break

    asyncio.create_task(read_output())

    asyncio.create_task(read_output())

    try:
        while True:
            data = await websocket.receive_text()
            # FIX: Ensure there is no trailing 'S' here
            if proc.stdin:
                proc.stdin.write(data.encode())
                await proc.stdin.drain()
    except WebSocketDisconnect:
        print("[ODIN_CORE] Terminal disconnected")
        proc.terminate()
    except Exception as e:
        print(f"[ODIN_CORE] Terminal error: {e}")
        proc.terminate()