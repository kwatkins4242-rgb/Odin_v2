"""
Agent Bridge — hands: files, shell, screenshot.
Port 8099. Brain posts here; auth via X-ODIN-KEY or JSON api_key.
All file paths are resolved under the project ROOT unless absolute and allowed.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from settings import get_settings

settings = get_settings()
log = logging.getLogger("bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Brain Bridge", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _key_ok(header_key: str | None, body_key: str | None) -> bool:
    expected = settings.effective_bridge_key
    if not expected:
        log.warning("BRIDGE_KEY / ODIN_BRIDGE_KEY not set — refusing requests.")
        return False
    got = (header_key or body_key or "").strip()
    return got == expected


def _under_root(p: Path) -> bool:
    try:
        p.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def _safe_path(raw: str | None, default: str = ".") -> Path:
    if raw is None or str(raw).strip() == "":
        raw = default
    path = Path(str(raw).strip()).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    else:
        path = path.resolve()
    if not _under_root(path):
        raise HTTPException(400, f"Path must stay under project root: {ROOT}")
    return path


@app.get("/health")
def health():
    return {"status": "ok", "service": "bridge", "root": str(ROOT)}


class TriggerBody(BaseModel):
    task: str
    payload: dict = {}
    api_key: str | None = None


@app.post("/n8n/trigger")
async def n8n_trigger(
    body: TriggerBody,
    request: Request,
    x_odin_key: str | None = Header(default=None, alias="X-ODIN-KEY"),
):
    if not _key_ok(x_odin_key, body.api_key):
        raise HTTPException(401, "Invalid or missing bridge key")

    task = (body.task or "").strip().lower().replace("-", "_")
    payload = body.payload or {}

    try:
        data = await _dispatch(task, payload)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("bridge task failed")
        return {"success": False, "error": str(e)}


async def _dispatch(task: str, payload: dict) -> dict:
    if task in ("take_screenshot", "see", "screenshot"):
        return _task_screenshot(payload)
    if task == "list_dir":
        return _task_list_dir(payload)
    if task == "read_file":
        return _task_read_file(payload)
    if task == "write_file":
        return _task_write_file(payload)
    if task == "delete_file":
        return _task_delete_file(payload)
    if task in ("make_dir", "mkdir"):
        return _task_make_dir(payload)
    if task in ("move_file", "rename"):
        return _task_move_file(payload)
    if task == "run_command":
        return _task_run_command(payload)
    if task == "memory_search":
        return {"hits": [], "note": "Use Brain RAG; bridge memory_search is a stub."}
    raise HTTPException(400, f"Unknown task: {task}")


def _task_screenshot(_: dict) -> dict:
    try:
        import mss
        from PIL import Image
    except ImportError as e:
        raise HTTPException(500, f"mss/Pillow required for screenshots: {e}") from e

    with mss.mss() as sct:
        mon = sct.monitors[1]
        shot = sct.grab(mon)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"base64": b64, "format": "png"}


def _task_list_dir(payload: dict) -> dict:
    d = _safe_path(payload.get("path") or ".")
    if not d.exists():
        return {"error": "path does not exist", "path": str(d)}
    if d.is_file():
        return {"files": [d.name], "path": str(d)}
    names = sorted(os.listdir(d))
    return {"path": str(d), "entries": names, "count": len(names)}


def _task_read_file(payload: dict) -> dict:
    path = _safe_path(payload.get("path"))
    if not path.is_file():
        raise HTTPException(400, f"Not a file: {path}")
    max_bytes = int(payload.get("max_bytes", 500_000))
    data = path.read_bytes()[:max_bytes]
    text = data.decode("utf-8", errors="replace")
    return {"path": str(path), "content": text, "truncated": path.stat().st_size > len(data)}


def _task_write_file(payload: dict) -> dict:
    path = _safe_path(payload.get("path"))
    content = payload.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "bytes": len(content.encode("utf-8")), "written": True}


def _task_delete_file(payload: dict) -> dict:
    path = _safe_path(payload.get("path"))
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
    else:
        raise HTTPException(400, f"Nothing to delete: {path}")
    return {"deleted": str(path)}


def _task_make_dir(payload: dict) -> dict:
    path = _safe_path(payload.get("path"))
    path.mkdir(parents=True, exist_ok=True)
    return {"created": str(path)}


def _task_move_file(payload: dict) -> dict:
    src = _safe_path(payload.get("from") or payload.get("source"))
    dst = _safe_path(payload.get("to") or payload.get("dest"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return {"from": str(src), "to": str(dst)}


def _task_run_command(payload: dict) -> dict:
    cmd = payload.get("command") or payload.get("cmd")
    if not cmd or not isinstance(cmd, str):
        raise HTTPException(400, "payload.command required (string)")
    cwd = _safe_path(payload.get("cwd") or ".")
    timeout = int(payload.get("timeout", 120))
    # Strip dangerous nulls; keep single shell string for compatibility with tools/*.py
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.run(
        cmd,
        shell=True,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if len(out) > 100_000:
        out = out[:100_000] + "\n... [truncated]"
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "combined": out,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.port_bridge, log_level="info")
