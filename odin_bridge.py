"""
ODIN Agent Bridge
=================
Location: C:\\AI\\MyOdin\\odin_bridge.py
Port: 8099

Bridges ODIN to n8n, external tools, and autonomous tasks.
Auth: X-ODIN-KEY header required on all POST routes.
"""

import sys
import os
import shutil
import subprocess
import base64
from pathlib import Path
from datetime import datetime
import utils.vision_utils as vision_utils

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / ".env", override=True)

from settings import get_settings
settings = get_settings()

import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BRIDGE_KEY = settings.odin_bridge_key
CORE_URL   = settings.core_url
LOG_FILE   = ROOT / "bridge_log.txt"


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Initialize integrated services
try:
    from M3.comms.mail_service import MailService
    mail_svc = MailService()
except Exception as e:
    print(f"[BRIDGE] MailService failed to load: {e}")
    mail_svc = None


app = FastAPI(title="ODIN Agent Bridge", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────
async def require_key(request: Request):
    key = request.headers.get("X-ODIN-KEY", "")
    if key != BRIDGE_KEY:
        log(f"AUTH FAIL from {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid or missing X-ODIN-KEY")


# ── Models ────────────────────────────────────────────
class WriteFileRequest(BaseModel):
    path:     str
    content:  str
    encoding: str = "utf-8"

class DeleteFileRequest(BaseModel):
    path: str

class RunScriptRequest(BaseModel):
    script:  str
    timeout: int = 30

class RunCommandRequest(BaseModel):
    command: str
    cwd:     str = None
    timeout: int = 30

class ReadFileRequest(BaseModel):
    path: str

class ListDirRequest(BaseModel):
    path: str

class MakeDirRequest(BaseModel):
    path: str

class MoveFileRequest(BaseModel):
    src: str
    dst: str

class N8nTriggerRequest(BaseModel):
    task:         str
    payload:      dict
    callback_url: str = None
    job_id:       str = None

class CallbackRequest(BaseModel):
    url:  str
    data: dict

class ChatRequest(BaseModel):
    message:    str
    session_id: str = "n8n"
    history:    list = []

class SendMailRequest(BaseModel):
    to:      str
    subject: str
    body:    str

class CheckMailRequest(BaseModel):
    limit: int = 5


# ── Helpers ───────────────────────────────────────────
async def send_callback(url: str, data: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=data)
            log(f"CALLBACK → {url} [{r.status_code}]")
    except Exception as e:
        log(f"CALLBACK FAILED: {url} — {e}")


# ── Public routes ─────────────────────────────────────
@app.get("/")
def status():
    return {
        "status":  "ODIN Bridge ONLINE",
        "version": "2.0.0",
        "port":    8099,
        "time":    datetime.now().isoformat(),
        "core":    CORE_URL,
    }

@app.get("/health")
def health():
    return {"ok": True, "bridge": "online"}


# ── n8n Trigger ───────────────────────────────────────
@app.post("/n8n/trigger", dependencies=[Depends(require_key)])
async def n8n_trigger(req: N8nTriggerRequest):
    log(f"N8N TRIGGER: task={req.task} job_id={req.job_id}")
    result = {
        "job_id":  req.job_id,
        "task":    req.task,
        "success": False,
        "data":    None,
        "error":   None,
    }

    try:
        if req.task == "chat":
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{CORE_URL}/api/chat",
                    json={
                        "message":    req.payload.get("message", ""),
                        "history":    req.payload.get("history", []),
                        "session_id": req.payload.get("session_id", "n8n"),
                    }
                )
                data = r.json()
                result["data"]    = data.get("response", data)
                result["success"] = True

        elif req.task == "memory_search":
            q = req.payload.get("query", "")
            limit = req.payload.get("limit", 5)
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"http://localhost:{settings.port_memory}/api/memory/search",
                    params={"q": q, "limit": limit}
                )
                result["data"] = r.json()
                result["success"] = r.status_code == 200

        elif req.task == "run_command":
            cmd  = RunCommandRequest(**req.payload)
            proc = subprocess.run(
                cmd.command, shell=True, capture_output=True,
                text=True, timeout=cmd.timeout, cwd=cmd.cwd
            )
            result["success"] = proc.returncode == 0
            result["data"]    = {
                "stdout":     proc.stdout,
                "stderr":     proc.stderr,
                "returncode": proc.returncode,
            }

        elif req.task == "run_script":
            s    = RunScriptRequest(**req.payload)
            proc = subprocess.run(
                [sys.executable, "-c", s.script],
                capture_output=True, text=True, timeout=s.timeout
            )
            result["success"] = proc.returncode == 0
            result["data"]    = {
                "stdout":     proc.stdout,
                "stderr":     proc.stderr,
                "returncode": proc.returncode,
            }

        elif req.task == "write_file":
            wr = WriteFileRequest(**req.payload)
            p  = Path(wr.path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(wr.content, encoding=wr.encoding)
            result["success"] = True
            result["data"]    = {"path": str(p.resolve())}

        elif req.task == "read_file":
            rr = ReadFileRequest(**req.payload)
            p  = Path(rr.path)
            if not p.exists():
                raise FileNotFoundError(f"{rr.path} not found")
            result["success"] = True
            result["data"]    = {"content": p.read_text(encoding="utf-8", errors="replace")}

        elif req.task == "list_dir":
            lr = ListDirRequest(**req.payload)
            p  = Path(lr.path)
            entries = [
                {"name": i.name, "type": "dir" if i.is_dir() else "file"}
                for i in sorted(p.iterdir())
            ]
            result["success"] = True
            result["data"]    = {"entries": entries}

        elif req.task == "delete_file":
            dr = DeleteFileRequest(**req.payload)
            p  = Path(dr.path)
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink(missing_ok=True)
            result["success"] = True
            result["data"]    = {"path": dr.path, "action": "deleted"}

        elif req.task == "make_dir":
            mr = MakeDirRequest(**req.payload)
            p  = Path(mr.path)
            p.mkdir(parents=True, exist_ok=True)
            result["success"] = True
            result["data"]    = {"path": str(p.resolve())}

        elif req.task == "move_file":
            mv = MoveFileRequest(**req.payload)
            shutil.move(mv.src, mv.dst)
            result["success"] = True
            result["data"]    = {"src": mv.src, "dst": mv.dst}

        elif req.task == "send_mail":
            if not mail_svc:
                raise Exception("MailService not available")
            m = SendMailRequest(**req.payload)
            res = mail_svc.send_email(m.to, m.subject, m.body)
            result["success"] = res.get("success", False)
            result["data"] = res

        elif req.task == "check_mail":
            if not mail_svc:
                raise Exception("MailService not available")
            m = CheckMailRequest(**req.payload)
            res = mail_svc.check_inbox(limit=m.limit)
            result["success"] = res.get("success", False)
            result["data"] = res
            
        elif req.task == "take_screenshot":
            # Uses shared utility to capture then encodes to base64
            # LOG_DIR inside Bridge root
            log_dir = ROOT / "M4" / "agents" / "logs"
            path = vision_utils.capture_screen(log_dir, resize_to=1280)
            
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            result["success"] = True
            result["data"] = {
                "base64": encoded_string,
                "path": path,
                "format": "png"
            }

        else:
            result["error"] = f"Unknown task: {req.task}"

    except Exception as e:
        result["error"] = str(e)
        log(f"N8N TRIGGER ERROR: {e}")

    if req.callback_url:
        await send_callback(req.callback_url, result)

    return result


@app.post("/n8n/callback", dependencies=[Depends(require_key)])
async def manual_callback(req: CallbackRequest):
    await send_callback(req.url, req.data)
    return {"sent": True}


# ── Chat passthrough ──────────────────────────────────
@app.post("/api/chat", dependencies=[Depends(require_key)])
async def chat(req: ChatRequest):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{CORE_URL}/api/chat",
                json={
                    "message":    req.message,
                    "history":    req.history,
                    "session_id": req.session_id,
                }
            )
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── File operations ───────────────────────────────────
@app.post("/write_file", dependencies=[Depends(require_key)])
def write_file(req: WriteFileRequest):
    try:
        p = Path(req.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(req.content, encoding=req.encoding)
        log(f"WRITE_FILE: {req.path}")
        return {"success": True, "path": str(p.resolve())}
    except Exception as e:
        log(f"WRITE_FILE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/read_file", dependencies=[Depends(require_key)])
def read_file(req: ReadFileRequest):
    try:
        p = Path(req.path)
        if not p.exists():
            raise HTTPException(status_code=404, detail="File not found")
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"success": True, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete_file", dependencies=[Depends(require_key)])
def delete_file(req: DeleteFileRequest):
    try:
        p = Path(req.path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)
        return {"success": True, "path": req.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/list_dir", dependencies=[Depends(require_key)])
def list_dir(req: ListDirRequest):
    try:
        p = Path(req.path)
        entries = [{"name": i.name, "type": "dir" if i.is_dir() else "file"} for i in sorted(p.iterdir())]
        return {"success": True, "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/make_dir", dependencies=[Depends(require_key)])
def make_dir(req: MakeDirRequest):
    try:
        p = Path(req.path)
        p.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": str(p.resolve())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_command", dependencies=[Depends(require_key)])
def run_command(req: RunCommandRequest):
    try:
        proc = subprocess.run(req.command, shell=True, capture_output=True, text=True, timeout=req.timeout, cwd=req.cwd)
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run_script", dependencies=[Depends(require_key)])
def run_script(req: RunScriptRequest):
    try:
        proc = subprocess.run(
            [sys.executable, "-c", req.script],
            capture_output=True, text=True, timeout=req.timeout
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_mail", dependencies=[Depends(require_key)])
def bridge_send_mail(req: SendMailRequest):
    if not mail_svc:
        raise HTTPException(status_code=503, detail="MailService not available")
    res = mail_svc.send_email(req.to, req.subject, req.body)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res["error"])
    return res


@app.post("/check_mail", dependencies=[Depends(require_key)])
def bridge_check_mail(req: CheckMailRequest):
    if not mail_svc:
        raise HTTPException(status_code=503, detail="MailService not available")
    res = mail_svc.check_inbox(limit=req.limit)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res["error"])
    return res


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)