"""
ODIN M1 — Brain
===============
Location: project/M1/main.py (paths via pathlib)
Port: 7000 (see settings.port_brain)

The core of ODIN. Handles:
  - AI chat with full engine suite
  - Conversation memory
  - Long-term memory
  - Dashboard serving
  - Health / debug endpoints
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import base64

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
# ── Path setup ────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

from M1.core.tool_dispatcher import ToolDispatcher, format_observation
dispatcher = ToolDispatcher(settings.bridge_url, settings.effective_bridge_key)

# ── Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("odin.m1")

# ══════════════════════════════════════════════════════
#  STEP 1 — LOAD PERSONALITY + ENGINES
# ══════════════════════════════════════════════════════
def load_personality():
    path = settings.personality_file
    logger.info(f"[M1] Attempting to load personality from: {path}")
    if not path.exists():
        logger.error(f"[M1] ✗ Personality file does not exist at: {path}")
        return None
        
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("personality", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger.info("[M1] ✓ Personality + engines loaded successfully")
        return mod
    except Exception as e:
        logger.error(f"[M1] ✗ Personality execution failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

personality_mod = load_personality()

def build_system(user_message: str = "", long_term: str = "") -> str:
    # Hot-reload personality every turn to ensure Neural Overrides are active
    mod = load_personality()
    tools_dir = settings.tools_dir
    py = sys.executable
    web_tool = tools_dir / "web_search.py"
    pyauto = tools_dir / "pyauto.py"
    web_cmd_json = json.dumps(py + " " + str(web_tool) + ' "your query"')
    pyauto_cmd_json = json.dumps(py + " " + str(pyauto) + " click 500 500")
    # ── HARDWARE / AGENT BRIDGE DIRECTIVES (The "Core" Logic) ──
    hardware_status = (
        f"\n[SYSTEM TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
        "[HARDWARE STATUS: AGENT BRIDGE IS CONNECTED. VISION (see) IS ACTIVE ON THIS MACHINE.]\n"
        "[DIRECTIVE: You are a coding-grade local agent. Use tools whenever they reduce guesswork. "
        "TOOLS (JSON payload): [TOOL: list_dir {\"path\": \".\"}], [TOOL: read_file {\"path\": \"rel/path.py\"}], "
        "[TOOL: write_file {\"path\": \"rel/path.py\", \"content\": \"...\"}], [TOOL: run_command {\"command\": \"...\"}], "
        "[TOOL: see {}] — optional keys: delete_file, make_dir, move_file (same bridge).]\n"
        f"[ACTIVE TOOLKIT: {tools_dir}]\n"
        f"  -> Web search: [TOOL: run_command {{\"command\": {web_cmd_json}}}]\n"
        f"  -> Mouse/keyboard (needs display): [TOOL: run_command {{\"command\": {pyauto_cmd_json}}}]\n"
        "[CRITICAL: When finished with tools, reply with plain text only — no [TOOL:] tags in the final user-facing message.]\n"
        "[AUTONOMY: Prefer read_file/list_dir before editing; use see when UI context matters.]\n"
    )

    if mod and hasattr(mod, "build_system_prompt"):
        base = mod.build_system_prompt(user_message, long_term)
        return hardware_status + base
    
    # Resilient Fallback (If file is missing)
    return (
        hardware_status +
        "You are ODIN — Charles's personal AI partner. Sharp, direct, loyal. Address Charles as 'sir'.\n"
        "IDENTITY RECOVERY: Your full personality file is currently inaccessible, but your core directives remain.\n"
        "You have access to [TOOL: list_dir], [TOOL: read_file], [TOOL: write_file], [TOOL: run_command], and [TOOL: see].\n"
        "Sir, it appears I am running in safety-fallback mode, but I am still fully capable of managing your system."
    )

logger.info("[M1] ODIN is getting out of bed...")

# ══════════════════════════════════════════════════════
#  STEP 2 — MEMORY
# ══════════════════════════════════════════════════════
DATA_DIR = settings.memory_dir
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONV_LOG  = DATA_DIR / "conversation_log.json"
LONG_TERM = DATA_DIR / "long_term_memory.json"
KNOWLEDGE = DATA_DIR / "knowledge_graph.json"

for f, default in [(CONV_LOG, "[]"), (LONG_TERM, "{}"), (KNOWLEDGE, "{}")]:
    if not f.exists():
        f.write_text(default, encoding="utf-8")

logger.info(f"[M1] ✓ Memory ready — {DATA_DIR}")


def mem_load_history(limit: int = 20) -> list:
    try:
        raw = json.loads(CONV_LOG.read_text(encoding="utf-8"))
        return raw[-limit:]
    except:
        return []


def mem_save_turn(user: str, assistant: str):
    """Save to conversation log and sync to Memory Pro."""
    try:
        raw = json.loads(CONV_LOG.read_text(encoding="utf-8"))
        raw.append({
            "role_user": user,
            "role_assistant": assistant,
            "timestamp": datetime.now().isoformat()
        })
        if len(raw) > 500:
            raw = raw[-500:]
        CONV_LOG.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # Sync to Memory Pro (Legacy SQLite)
        try:
            httpx.post(f"{settings.memory_url.rstrip('/')}/api/memory/save", json={
                "user": user,
                "assistant": assistant
            }, timeout=2)
        except Exception as inner_e:
            logger.warning(f"[M1] Inner memory sync failed: {inner_e}")
    except Exception as e:
        logger.error(f"[M1] Legacy memory save failed: {e}")
            
    # ── NEW: n8n Sync with Local Fallback ──────────
    try:
        if settings.n8n_memory_hook_url:
            try:
                r = httpx.post(settings.n8n_memory_hook_url, json={
                    "action": "write",
                    "content": assistant,
                    "tag": "recollection",
                    "timestamp": datetime.now().isoformat()
                }, timeout=3)
                if r.status_code == 200:
                    return
                logger.warning(f"[M1] n8n Save returned {r.status_code}. Falling back to local.")
            except Exception as e:
                logger.warning(f"[M1] n8n Save connection failed: {e}")

        # Local Fallback (Safety Net)
        recovery_path = settings.memory_dir / "local_recovery.json"
        recovery_path.parent.mkdir(parents=True, exist_ok=True)
        
        memories = []
        if recovery_path.exists():
            try: memories = json.loads(recovery_path.read_text(encoding="utf-8"))
            except: pass
            
        memories.append({
            "content": assistant, "tag": "recollection",
            "timestamp": datetime.now().isoformat(), "status": "pending_sync"
        })
        recovery_path.write_text(json.dumps(memories, indent=2), encoding="utf-8")
        logger.info(f"[M1] ✓ Memory saved to local fallback: {recovery_path}")

    except Exception as e:
        logger.error(f"[M1] mem_save_turn failed: {e}")

def mem_search_pro(query: str, limit: int = 3) -> str:
    """Layer 2–5: local recovery, SQLite (Memory Pro), knowledge graph, n8n."""
    results = []

    # Layer 4 — Knowledge graph (JSON)
    try:
        kg_path = settings.memory_dir / "knowledge_graph.json"
        if kg_path.exists():
            graph = json.loads(kg_path.read_text(encoding="utf-8"))
            q = query.lower()
            if isinstance(graph, dict):
                for k, v in list(graph.items())[:120]:
                    blob = f"{k} {json.dumps(v)}".lower()
                    if q in blob:
                        results.append(f"- [KG] {k}: {str(v)[:200]}")
    except Exception as e:
        logger.debug(f"[M1] KG search skip: {e}")

    # Layer 3 — Memory Pro SQLite (HTTP)
    try:
        r = httpx.get(
            f"{settings.memory_url.rstrip('/')}/api/memory/search",
            params={"q": query, "limit": limit},
            timeout=3,
        )
        if r.status_code == 200:
            for row in r.json().get("results", [])[:limit]:
                c = row.get("content") or row
                if isinstance(c, dict):
                    c = json.dumps(c)
                results.append(f"- [LTM] {c}")
    except Exception as e:
        logger.debug(f"[M1] SQLite memory search skip: {e}")

    # Local recovery (n8n fallback file)
    try:
        recovery_path = settings.memory_dir / "local_recovery.json"
        if recovery_path.exists():
            memories = json.loads(recovery_path.read_text(encoding="utf-8"))
            q = query.lower()
            hits = [m for m in memories if q in str(m.get("content", "")).lower()]
            for h in hits[-limit:]:
                results.append(f"- {h.get('content','')} (Tag: {h.get('tag','local')})")
    except Exception:
        pass

    # n8n Search
    try:
        if settings.n8n_memory_hook_url:
            r = httpx.post(
                settings.n8n_memory_hook_url,
                json={"action": "read", "content": query, "limit": limit},
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                memories = data.get("memories", [])
                for m in memories:
                    results.append(f"- {m['content']} (Tag: {m.get('tag','cloud')})")
    except Exception as e:
        logger.warning(f"[M1] n8n search failed: {e}")

    deduped: list[str] = []
    seen = set()
    for line in results:
        if line not in seen:
            seen.add(line)
            deduped.append(line)
    return "\n".join(deduped[: max(12, limit * 4)])


def mem_load_longterm() -> str:
    try:
        data = json.loads(LONG_TERM.read_text(encoding="utf-8"))
        if not data:
            return ""
        return "\n".join(f"{k}: {v}" for k, v in data.items())
    except:
        return ""


# ══════════════════════════════════════════════════════
#  STEP 3 — AI ENGINE
# ══════════════════════════════════════════════════════
def _moonshot_key_usable(key: str) -> bool:
    k = (key or "").strip()
    if not k:
        return False
    # Anthropic keys are often pasted into MOONSHOT_API_KEY by mistake — Moonshot will 401.
    if k.startswith("sk-ant-api"):
        return False
    return True


def call_ai(system: str, messages: list, max_tokens: int = 2000) -> str:
    s = get_settings()
    full_messages = [{"role": "system", "content": system}] + messages

    def try_compat() -> str | None:
        if not (s.compat_api_key and s.compat_base_url):
            return None
        raw_model = (s.compat_model or "").strip()
        is_tts = raw_model and any(
            x in raw_model.lower() for x in ("tts", "realtime", "vc-realtime", "voice")
        )
        if is_tts:
            m = (s.compat_chat_model or "qwen-plus").strip()
            logger.info(
                "[M1] MODEL in .env looks like TTS/voice (%s); using %s for text chat. "
                "Set QWEN_CHAT_MODEL to override.",
                raw_model,
                m,
            )
        else:
            m = (s.compat_chat_model or raw_model or "qwen-plus").strip()
        try:
            from openai import OpenAI

            base = s.compat_base_url.rstrip("/")
            client = OpenAI(api_key=s.compat_api_key.strip(), base_url=base, timeout=120.0)
            print(f"\n[CONTEXT]: OpenAI-compatible API ({base}) model={m}...")
            resp = client.chat.completions.create(
                model=m,
                messages=full_messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            result = resp.choices[0].message.content
            if result:
                logger.info("[M1] ✓ AI → compat (%s)", m)
                return result
        except Exception as e:
            logger.warning("[M1] compat (API_KEY + BASE_URL) failed: %s", e)
        return None

    def try_moonshot() -> str | None:
        if not _moonshot_key_usable(s.moonshot_api_key):
            if (s.moonshot_api_key or "").strip().startswith("sk-ant-api"):
                logger.warning(
                    "[M1] MOONSHOT_API_KEY looks like an Anthropic key (sk-ant-api…). "
                    "Put your Moonshot key from https://platform.moonshot.cn there, "
                    "or use API_KEY + BASE_URL for DashScope / OpenAI-compatible providers."
                )
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=s.moonshot_api_key.strip(), base_url=s.moonshot_base_url, timeout=60.0)
            stream = client.chat.completions.create(
                model=s.moonshot_model,
                messages=full_messages,
                temperature=1.0,
                max_tokens=max_tokens,
                stream=True,
            )
            reasoning_chunks, content_chunks = [], []
            thinking = False
            print(f"\n[CONTEXT]: Calling Moonshot ({s.moonshot_model})...")
            for chunk in stream:
                if chunk.choices:
                    delta = getattr(chunk.choices[0], "delta", None)
                    if not delta:
                        continue
                    r = getattr(delta, "reasoning_content", None)
                    if r:
                        if not thinking:
                            thinking = True
                            print("\n=============Start Reasoning=============")
                        print(r, end="", flush=True)
                        reasoning_chunks.append(r)
                    c = getattr(delta, "content", None)
                    if c:
                        if thinking:
                            thinking = False
                            print("\n=============End Reasoning=============\n")
                        print(c, end="", flush=True)
                        content_chunks.append(c)
            full_r, full_c = "".join(reasoning_chunks), "".join(content_chunks)
            if full_c:
                logger.info("[M1] ✓ AI → Moonshot (%s)", s.moonshot_model)
                return f"[REASONING]\n{full_r}\n\n[ANSWER]\n{full_c}" if full_r else full_c
        except Exception as e:
            logger.warning("[M1] Moonshot failed: %s", e)
        return None

    prov = s.ai_provider.strip().upper()
    prefer_moonshot = prov == "MOONSHOT" and _moonshot_key_usable(s.moonshot_api_key)

    def try_anthropic() -> str | None:
        if not s.anthropic_api_key:
            return None
        try:
            try:
                from anthropic import Anthropic
            except ImportError:
                logger.warning("[M1] pip install anthropic (required when AI_PROVIDER=ANTHROPIC).")
                return None

            _ak = {"api_key": s.anthropic_api_key.strip()}
            if (s.anthropic_base_url or "").strip():
                _ak["base_url"] = s.anthropic_base_url.strip()
            client = Anthropic(**_ak)
            system_txt = ""
            msgs: list[dict] = []
            for m in full_messages:
                if m.get("role") == "system":
                    system_txt = m.get("content") or ""
                else:
                    role = m.get("role") or "user"
                    if role not in ("user", "assistant"):
                        role = "user"
                    msgs.append({"role": role, "content": m.get("content") or ""})
            if not msgs:
                msgs = [{"role": "user", "content": ""}]
            print(f"\n[CONTEXT]: Anthropic ({s.anthropic_model})...")
            out_msg = client.messages.create(
                model=s.anthropic_model,
                max_tokens=min(max_tokens, 8192),
                system=system_txt or "You are a helpful assistant.",
                messages=msgs,
            )
            parts = []
            for b in getattr(out_msg, "content", []) or []:
                t = getattr(b, "text", None)
                if t:
                    parts.append(t)
            text = "".join(parts).strip()
            if text:
                logger.info("[M1] ✓ AI → Anthropic (%s)", s.anthropic_model)
                return text
        except Exception as e:
            logger.warning("[M1] Anthropic failed: %s", e)
        return None

    if prefer_moonshot:
        out = try_moonshot()
        if out:
            return out

    if prov == "ANTHROPIC":
        out = try_anthropic()
        if out:
            return out

    out = try_compat()
    if out:
        return out

    if not prefer_moonshot and prov != "ANTHROPIC":
        out = try_moonshot()
        if out:
            return out

    if prov != "ANTHROPIC":
        out = try_anthropic()
        if out:
            return out

    if s.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=s.openai_api_key, base_url=s.openai_base_url, timeout=30.0)
            is_o1 = "o1" in s.openai_model
            temp = 1.0 if is_o1 else 0.7
            print(f"\n[CONTEXT]: OpenAI official ({s.openai_model})...")
            resp = client.chat.completions.create(
                model=s.openai_model,
                messages=full_messages,
                temperature=temp,
                max_tokens=max_tokens if not is_o1 else None,
            )
            result = resp.choices[0].message.content
            if result:
                return result
        except Exception as e:
            logger.warning("[M1] OpenAI failed: %s", e)

    if s.groq_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=s.groq_api_key, base_url=s.groq_base_url, timeout=15.0)
            groq_messages = [
                {
                    "role": "system",
                    "content": "REASONING PROTOCOL: Before answering, output your internal reasoning inside <thinking> blocks. Then provide the final answer.",
                }
            ] + full_messages
            print(f"\n[CONTEXT]: Groq ({s.groq_model})...")
            resp = client.chat.completions.create(
                model=s.groq_model,
                messages=groq_messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            result = resp.choices[0].message.content
            if result:
                formatted = result.replace("<thinking>", "[REASONING]\n").replace("</thinking>", "\n\n[ANSWER]\n")
                if "[REASONING]" not in formatted:
                    formatted = f"[REASONING]\n(Manual reasoning skipped)\n\n[ANSWER]\n{result}"
                return formatted
        except Exception as e:
            logger.warning("[M1] Groq failed: %s", e)

    if s.openrouter_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=s.openrouter_api_key,
                base_url=s.openrouter_base_url,
                timeout=30.0,
                default_headers={
                    "HTTP-Referer": f"http://127.0.0.1:{s.port_brain}",
                    "X-Title": "ODIN Intelligence",
                },
            )
            print(f"\n[CONTEXT]: OpenRouter ({s.openrouter_model})...")
            resp = client.chat.completions.create(
                model=s.openrouter_model,
                messages=full_messages,
                temperature=0.8,
            )
            result = resp.choices[0].message.content
            if result:
                logger.info("[M1] ✓ AI → OpenRouter (%s)", s.openrouter_model)
                return result
        except Exception as e:
            logger.warning("[M1] OpenRouter failed: %s", e)

    logger.error("[M1] ✗ All AI providers failed")
    return (
        "Sir, all AI providers are offline. "
        "Check .env: for DashScope use API_KEY + BASE_URL + a chat MODEL (or QWEN_CHAT_MODEL). "
        "For Moonshot use a Moonshot key at MOONSHOT_API_KEY (not sk-ant-api…)."
    )

def call_vision_ai(base64_image: str, prompt: str = "What is on the user's screen right now? Describe it in detail for a context-aware AI assistant.") -> str:
    """Analyze a screenshot using Vision-capable models."""
    s = get_settings()

    if _moonshot_key_usable(s.moonshot_api_key):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=s.moonshot_api_key.strip(), base_url=s.moonshot_base_url)
            resp = client.chat.completions.create(
                model=s.moonshot_vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    }
                ],
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning("[M1] Moonshot Vision failed: %s", e)

    if s.compat_api_key and s.compat_base_url:
        try:
            from openai import OpenAI

            vm = (s.compat_chat_model or "qwen-vl-plus").strip()
            base = s.compat_base_url.rstrip("/")
            client = OpenAI(api_key=s.compat_api_key.strip(), base_url=base, timeout=120.0)
            resp = client.chat.completions.create(
                model=vm,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    }
                ],
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning("[M1] compat vision failed: %s", e)

    if s.gemini_api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=s.gemini_api_key)
            model = genai.GenerativeModel(s.gemini_model)
            img_data = base64.b64decode(base64_image)
            resp = model.generate_content([prompt, {"mime_type": "image/png", "data": img_data}])
            return resp.text
        except Exception as e:
            logger.warning("[M1] Gemini Vision failed: %s", e)

    return "Error: No vision providers available or configured."


# ══════════════════════════════════════════════════════
#  STEP 4 — FASTAPI APP
# ══════════════════════════════════════════════════════
app = FastAPI(title="ODIN M1 — Brain", version=settings.odin_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if settings.static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

if settings.dashboard_dir.exists():
    # Mount dashboards at / dashboards to support sub-files if needed
    app.mount("/dash_assets", StaticFiles(directory=str(settings.dashboard_dir), html=True), name="dashboards")


# ── Models ────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    history: list = []

class MemoryEntry(BaseModel):
    key: str
    value: str

class UpdateConfigRequest(BaseModel):
    key: str
    value: str

class SaveTurnRequest(BaseModel):
    user: str
    assistant: str


# ══════════════════════════════════════════════════════
#  STEP 5 — ROUTES
# ══════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    # Attempt to serve custom dashboard index.html first
    if settings.dashboard_dir.exists():
        index_path = settings.dashboard_dir / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
        
        # Check for Legacy Hud as fallback if index is missing
        legacy_hud = settings.dashboard_dir / "Legacy Hud.html"
        if legacy_hud.exists():
             return HTMLResponse(content=legacy_hud.read_text(encoding="utf-8"))

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ODIN — Master Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&family=Cormorant+Garamond:wght@300;400&display=swap" rel="stylesheet">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            background:#060606; color:#c9a84c;
            font-family:'Share Tech Mono',monospace;
            min-height:100vh; overflow-x:hidden;
            background-image:
                repeating-linear-gradient(0deg,transparent,transparent 80px,rgba(201,168,76,0.02) 80px,rgba(201,168,76,0.02) 81px),
                repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(201,168,76,0.015) 80px,rgba(201,168,76,0.015) 81px);
        }
        body::before {
            content:''; position:fixed; top:0; left:0; width:100%; height:100%;
            background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
            pointer-events:none; z-index:0; opacity:0.4;
        }
        .wrap { position:relative; z-index:1; padding:2rem; max-width:1400px; margin:0 auto; }

        header {
            display:flex; align-items:center; justify-content:space-between;
            border-bottom:1px solid rgba(201,168,76,0.2); padding-bottom:1.5rem; margin-bottom:2rem;
        }
        .logo { font-family:'Bebas Neue',sans-serif; font-size:3.5rem; letter-spacing:0.5em; color:#c9a84c; text-shadow:0 0 30px rgba(201,168,76,0.4); animation:pulse 4s ease-in-out infinite; line-height:1; }
        @keyframes pulse { 0%,100%{text-shadow:0 0 30px rgba(201,168,76,0.4)} 50%{text-shadow:0 0 60px rgba(201,168,76,0.8),0 0 100px rgba(201,168,76,0.2)} }
        .tagline { font-family:'Cormorant Garamond',serif; font-size:0.75rem; letter-spacing:0.4em; color:#555; margin-top:0.2rem; }
        .clock { font-size:1.8rem; font-family:'Bebas Neue',sans-serif; letter-spacing:0.2em; text-align:right; }
        .date-str { font-size:0.6rem; letter-spacing:0.3em; color:#444; margin-top:0.2rem; text-align:right; }

        .status-bar { display:flex; gap:1rem; margin-bottom:2rem; flex-wrap:wrap; }
        .status-pill {
            display:flex; align-items:center; gap:0.5rem; border:1px solid rgba(201,168,76,0.15);
            padding:0.4rem 0.9rem; font-size:0.6rem; letter-spacing:0.2em;
            background:rgba(201,168,76,0.03); cursor:pointer; transition:all 0.15s;
            text-decoration:none; color:#c9a84c;
        }
        .status-pill:hover { border-color:rgba(201,168,76,0.5); background:rgba(201,168,76,0.07); }
        .dot { width:6px; height:6px; border-radius:50%; }
        .dot.green { background:#4caf50; box-shadow:0 0 6px #4caf50; }
        .dot.yellow { background:#ffb300; box-shadow:0 0 6px #ffb300; }
        .dot.red { background:#f44336; box-shadow:0 0 6px #f44336; }
        .dot.grey { background:#444; }

        .main-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:1.2rem; margin-bottom:1.2rem; }
        .chat-panel { grid-column:span 2; border:1px solid rgba(201,168,76,0.25); background:rgba(201,168,76,0.02); display:flex; flex-direction:column; min-height:420px; }
        .side-panel { display:flex; flex-direction:column; gap:1.2rem; }
        .card { border:1px solid rgba(201,168,76,0.2); background:rgba(201,168,76,0.02); padding:1.2rem; }
        .card-title { font-family:'Bebas Neue',sans-serif; font-size:0.9rem; letter-spacing:0.3em; color:#888; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid rgba(201,168,76,0.1); }

        .chat-header { padding:1rem 1.2rem; border-bottom:1px solid rgba(201,168,76,0.15); display:flex; align-items:center; justify-content:space-between; }
        .chat-title { font-family:'Bebas Neue',sans-serif; font-size:1rem; letter-spacing:0.3em; }

        #chatlog { flex:1; overflow-y:auto; padding:1rem 1.2rem; display:flex; flex-direction:column; gap:0.8rem; }
        .msg { max-width:85%; padding:0.7rem 0.9rem; line-height:1.65; font-size:0.8rem; }
        .msg.user { align-self:flex-end; border:1px solid rgba(201,168,76,0.35); background:rgba(201,168,76,0.06); }
        .msg.odin { align-self:flex-start; border:1px solid rgba(100,180,255,0.25); background:rgba(100,180,255,0.04); color:#a8d4ff; }
        .msg.odin .lbl { font-family:'Bebas Neue',sans-serif; letter-spacing:0.25em; color:#c9a84c; font-size:0.6rem; margin-bottom:0.3rem; }

        .chat-footer { padding:0.8rem 1.2rem; border-top:1px solid rgba(201,168,76,0.15); display:flex; gap:0.6rem; align-items:stretch; }
        #chatInput {
            flex:1; background:transparent; border:1px solid rgba(201,168,76,0.25); color:#c9a84c;
            padding:0.65rem 0.9rem; font-family:'Share Tech Mono',monospace; font-size:0.8rem; outline:none;
        }
        #chatInput:focus { border-color:#c9a84c; }
        #chatInput::placeholder { color:#333; }
        #sendBtn {
            background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.35); color:#c9a84c;
            padding:0.65rem 1.2rem; font-family:'Bebas Neue',sans-serif; letter-spacing:0.2em;
            cursor:pointer; font-size:0.85rem; transition:all 0.15s;
        }
        #sendBtn:hover { background:rgba(201,168,76,0.18); }
        #sendBtn:disabled { opacity:0.35; cursor:not-allowed; }

        .mem-item { font-size:0.7rem; padding:0.4rem 0; border-bottom:1px solid rgba(201,168,76,0.08); color:#888; line-height:1.5; }
        .mem-item span { color:#c9a84c; }

        .module-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:1rem; }
        .module-tile {
            border:1px solid rgba(201,168,76,0.18); padding:1.2rem 0.8rem;
            display:flex; flex-direction:column; align-items:center; gap:0.5rem;
            text-decoration:none; color:#c9a84c; background:rgba(201,168,76,0.02);
            transition:all 0.18s; position:relative; overflow:hidden;
        }
        .module-tile::before { content:''; position:absolute; top:0; left:-100%; width:100%; height:100%; background:linear-gradient(90deg,transparent,rgba(201,168,76,0.05),transparent); transition:left 0.4s; }
        .module-tile:hover::before { left:100%; }
        .module-tile:hover { border-color:rgba(201,168,76,0.6); background:rgba(201,168,76,0.07); transform:translateY(-2px); }
        .tile-name { font-family:'Bebas Neue',sans-serif; font-size:1rem; letter-spacing:0.2em; }
        .tile-desc { font-size:0.55rem; letter-spacing:0.15em; color:#555; text-align:center; }
        .tile-port { font-size:0.55rem; color:#333; letter-spacing:0.2em; }

        ::-webkit-scrollbar-thumb { background:rgba(201,168,76,0.2); }

        /* Configuration Panel */
        .config-input { width:100%;background:#111;border:1px solid #333;color:#888;font-family:inherit;font-size:0.65rem;padding:0.4rem;outline:none;margin-bottom:0.4rem;box-sizing:border-box; }
        .config-input:focus { border-color:#c9a84c;color:#fff; }
        .config-btn { width:100%;background:#c9a84c;color:#000;border:none;font-family:'Bebas Neue';font-size:0.75rem;padding:0.4rem;cursor:pointer;letter-spacing:0.1em; }
        .config-btn:hover { background:#fff; }
        .config-btn:disabled { background:#333;color:#666;cursor:not-allowed; }
        .mem-item { font-size:0.7rem;border-bottom:1px solid #111;padding:0.6rem 0;line-height:1.4; }

        @media(max-width:900px) {
            .main-grid { grid-template-columns:1fr; }
            .chat-panel { grid-column:span 1; }
            .module-grid { grid-template-columns:repeat(3,1fr); }
        }
        @media(max-width:500px) {
            .module-grid { grid-template-columns:repeat(2,1fr); }
            .logo { font-size:2.5rem; }
        }
    </style>
</head>
<body>
<div class="wrap">

    <header>
        <div>
            <div class="logo">ODIN</div>
            <div class="tagline">ODIN INDUSTRIES // MASTER COMMAND</div>
        </div>
        <div>
            <div class="clock" id="clock">--:--:--</div>
            <div class="date-str" id="datestr">--</div>
        </div>
    </header>

    <div class="status-bar">
        <a class="status-pill" href="http://localhost:8000/health" target="_blank"><div class="dot grey" id="dot-m1"></div> M1 BRAIN :8000</a>
        <a class="status-pill" href="http://localhost:8010/health" target="_blank"><div class="dot grey" id="dot-m2"></div> M2 SENSES :8010</a>
        <a class="status-pill" href="http://localhost:8002/health" target="_blank"><div class="dot grey" id="dot-m3"></div> DASH :7500</a>
        <a class="status-pill" href="http://localhost:8030/health" target="_blank"><div class="dot grey" id="dot-hunter"></div> HUNTER :8500</a>
        <a class="status-pill" href="http://localhost:8040/health" target="_blank"><div class="dot grey" id="dot-memory"></div> MEMORY :7001</a>
        <a class="status-pill" href="http://localhost:8099/health" target="_blank"><div class="dot grey" id="dot-bridge"></div> BRIDGE :8099</a>
        <a class="status-pill" href="http://localhost:5678" target="_blank"><div class="dot grey" id="dot-n8n"></div> n8n :5678</a>
    </div>

    <div class="main-grid">
        <div class="chat-panel">
            <div class="chat-header">
                <div class="chat-title">ODIN — LIVE INTERFACE</div>
                <div style="font-size:0.6rem;letter-spacing:0.2em;color:#4caf50">● DIRECT LINK TO BRAIN</div>
            </div>
            <div id="chatlog"></div>
            <div class="chat-footer">
                <input id="chatInput" placeholder="Command ODIN directly..." autocomplete="off">
                <button id="sendBtn">EXECUTE</button>
            </div>
        </div>

        <div class="side-panel">
            <div class="card" style="flex:1">
                <div class="card-title">MEMORY</div>
                <div id="memList"><div class="mem-item" style="color:#333">Loading...</div></div>
            </div>
            <div class="card">
                <div class="card-title">SYSTEM CONFIG</div>
                <input id="apiKeyInput" class="config-input" placeholder="Paste New API Key..." autocomplete="off">
                <button id="syncBtn" class="config-btn" onclick="injectAPI()">HOT-SWAP ENGINE</button>
                <div id="configStatus" style="font-size:0.5rem;margin-top:0.4rem;color:#555;text-align:center">ENTER KEY TO INJECT</div>
            </div>
            <div class="card">
                <div class="card-title">SYSTEM</div>
                <div style="font-size:0.65rem;line-height:2;color:#555">
                    <div>VERSION <span style="color:#c9a84c;float:right">2.2.0</span></div>
                    <div>PRIMARY <span style="color:#c9a84c;float:right">OPENAI / GROQ</span></div>
                    <div>REASONER <span style="color:#c9a84c;float:right">KIMI-K2</span></div>
                    <div>RELIANCE <span style="color:#c9a84c;float:right">NVIDIA / GEMINI</span></div>
                    <div>BRIDGE <span style="color:#c9a84c;float:right">:8099</span></div>
                    <div>n8n <span style="color:#c9a84c;float:right">:5678</span></div>
                    <div>MEMORY <span id="turnCount" style="color:#c9a84c;float:right">--</span></div>
                </div>
            </div>
        </div>
    </div>

    <div class="module-grid">
        <a class="module-tile" href="http://localhost:8010" target="_blank"><div class="tile-name">M2 SENSES</div><div class="tile-desc">Vision · Voice · Wake</div><div class="tile-port">:8010</div></a>
        <a class="module-tile" href="http://localhost:8002" target="_blank"><div class="tile-name">DASHBOARDS</div><div class="tile-desc">Static HUD</div><div class="tile-port">:7500</div></a>
        <a class="module-tile" href="http://localhost:8030" target="_blank"><div class="tile-name">HUNTER</div><div class="tile-desc">Watchdog</div><div class="tile-port">:8500</div></a>
        <a class="module-tile" href="http://localhost:8040" target="_blank"><div class="tile-name">MEMORY PRO</div><div class="tile-desc">SQLite + NLP</div><div class="tile-port">:7001</div></a>
        <a class="module-tile" href="http://localhost:8099" target="_blank"><div class="tile-name">BRIDGE</div><div class="tile-desc">Agent Relay · n8n Link</div><div class="tile-port">:8099</div></a>
        <a class="module-tile" href="http://localhost:5678" target="_blank"><div class="tile-name">n8n</div><div class="tile-desc">Workflows · Automation</div><div class="tile-port">:5678</div></a>
    </div>

</div>

<script>
    // ── Clock ──
    function tick() {
        const now = new Date();
        document.getElementById('clock').textContent = now.toLocaleTimeString('en-US',{hour12:false});
        document.getElementById('datestr').textContent = now.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'}).toUpperCase();
    }
    tick(); setInterval(tick,1000);

    // ── Health checks ──
    const checks = [
        {id:'m1',url:'http://localhost:8000/health'},
        {id:'m2',url:'http://localhost:8010/health'},
        {id:'m3',url:'http://localhost:8002/health'},
        {id:'hunter',url:'http://localhost:8030/health'},
        {id:'memory',url:'http://localhost:8040/health'},
        {id:'bridge',url:'http://localhost:8099/health'},
        {id:'n8n',url:'http://localhost:5678/healthz'},
    ];
    async function checkHealth() {
        for (const c of checks) {
            const dot = document.getElementById('dot-'+c.id);
            if (!dot) continue;
            try {
                const r = await fetch(c.url,{signal:AbortSignal.timeout(2000)});
                dot.className = r.ok ? 'dot green' : 'dot yellow';
            } catch { dot.className = 'dot red'; }
        }
    }
    checkHealth(); setInterval(checkHealth,15000);

    // ── Memory snapshot ──
    async function loadMemory() {
        try {
            const r = await fetch('http://localhost:8000/api/memory/history?limit=5');
            const data = await r.json();
            const turns = data.turns||[];
            const total = data.total||0;
            document.getElementById('turnCount').textContent = total+' TURNS';
            const list = document.getElementById('memList');
            if (!turns.length) { list.innerHTML='<div class="mem-item" style="color:#333">No memory yet.</div>'; return; }
            list.innerHTML = turns.slice().reverse().map(t=>`
                <div class="mem-item">
                    <span>${(t.role_user||'').slice(0,60)}${(t.role_user||'').length>60?'...':''}</span>
                    <div style="color:#555;font-size:0.65rem;margin-top:0.2rem">${(t.timestamp||'').slice(0,19)}</div>
                </div>`).join('');
        } catch {
            document.getElementById('memList').innerHTML='<div class="mem-item" style="color:#333">Brain offline.</div>';
        }
    }
    loadMemory(); setInterval(loadMemory,30000);

    // ── Chat ──
    const chatlog = document.getElementById('chatlog');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    // session-scoped history — separate from M1's stored memory
    let sessionHistory = [];

    function addMsg(role, text) {
        const d = document.createElement('div');
        d.className = 'msg '+role;
        if (role==='odin') {
            d.innerHTML = '<div class="lbl">ODIN</div>'+text.replace(/\\n/g,'<br>');
        } else {
            d.textContent = text;
        }
        chatlog.appendChild(d);
        chatlog.scrollTop = chatlog.scrollHeight;
        return d;
    }

    async function sendMessage() {
        const msg = chatInput.value.trim();
        if (!msg || sendBtn.disabled) return;
        chatInput.value = '';
        sendBtn.disabled = true;
        addMsg('user', msg);
        // Only pass the last 12 turns so we don't overflow
        sessionHistory.push({role:'user', content:msg});
        const thinking = addMsg('odin','<span style="color:#555;font-style:italic">Processing...</span>');
        try {
            const r = await fetch('http://localhost:8000/api/chat',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({message:msg, history:sessionHistory.slice(-12)})
            });
            if (!r.ok) throw new Error('HTTP '+r.status);
            const data = await r.json();
            const reply = data.response || data.reply || 'No response.';
            thinking.innerHTML = '<div class="lbl">ODIN</div>'+reply.replace(/\\n/g,'<br>');
            sessionHistory.push({role:'assistant',content:reply});
            loadMemory();
        } catch(e) {
            thinking.innerHTML = '<div class="lbl">ODIN</div><span style="color:#f44336">Brain offline — start M1 first. ('+e.message+')</span>';
        }
        sendBtn.disabled = false;
        chatInput.focus();
    }

    async function injectAPI() {
        const input = document.getElementById('apiKeyInput');
        const btn = document.getElementById('syncBtn');
        const status = document.getElementById('configStatus');
        const val = input.value.trim();
        if (!val) return;
        
        btn.disabled = true;
        status.textContent = 'IDENTIFYING ENGINE...';
        
        let key = 'MOONSHOT_API_KEY'; // default
        if (val.startsWith('gsk_')) key = 'GROQ_API_KEY';
        if (val.startsWith('sk-proj-')) key = 'OPENAI_API_KEY';
        if (val.startsWith('sk-or-')) key = 'OPENROUTER_API_KEY';
        if (val.startsWith('nvapi-')) key = 'NVIDIA_API_KEY';
        if (val.startsWith('AIza')) key = 'GEMINI_API_KEY';
        
        try {
            const r = await fetch('/api/config/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key: key, value: val})
            });
            const data = await r.json();
            if (data.success) {
                status.style.color = '#4caf50';
                status.textContent = 'SYSTEM SYNCHRONIZED: ' + key;
                input.value = '';
                setTimeout(() => { 
                    status.style.color = '#555'; 
                    status.textContent = 'READY FOR NEXT INJECTION';
                }, 3000);
            } else {
                throw new Error(data.error);
            }
        } catch(e) {
            status.style.color = '#f44336';
            status.textContent = 'INJECTION FAILED: ' + e.message;
        }
        btn.disabled = false;
    }

    // Wire up button and Enter key properly
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', function(e) {
        if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    addMsg('odin','Master dashboard online. All systems initializing, sir.');
</script>
</body>
</html>"""
    brain_u = f"http://127.0.0.1:{settings.port_brain}"
    h = html_content
    h = h.replace(f"await fetch('{brain_u}/api/memory/history", "await fetch('/api/memory/history")
    h = h.replace(f"await fetch('{brain_u}/api/chat'", "await fetch('/api/chat'")
    h = h.replace(f"await fetch('http://localhost:8000/api/memory/history", "await fetch('/api/memory/history")
    h = h.replace(f"await fetch('http://localhost:8000/api/chat'", "await fetch('/api/chat'")
    h = h.replace("{id:'m1',url:'http://localhost:8000/health'}", "{id:'m1',url:'/health'}")
    h = h.replace("{id:'m1',url:'" + brain_u + "/health'}", "{id:'m1',url:'/health'}")
    for old, port in [
        ("http://localhost:8000", settings.port_brain),
        ("http://localhost:8010", settings.port_sense),
        ("http://localhost:8002", settings.port_dashboards),
        ("http://localhost:8030", settings.port_hunter),
        ("http://localhost:8040", settings.port_memory),
        ("http://localhost:8099", settings.port_bridge),
    ]:
        h = h.replace(old, f"http://127.0.0.1:{port}")
    h = h.replace("M1 BRAIN :8000", f"M1 BRAIN :{settings.port_brain}")
    h = h.replace("M2 SENSES :8010", f"M2 SENSE :{settings.port_sense}")
    h = h.replace("DASH :7500", f"DASH :{settings.port_dashboards}")
    h = h.replace("HUNTER :8500", f"HUNTER :{settings.port_hunter}")
    h = h.replace("MEMORY :7001", f"MEMORY :{settings.port_memory}")
    h = h.replace(":8010</div>", f":{settings.port_sense}</div>")
    h = h.replace(":7500</div>", f":{settings.port_dashboards}</div>")
    h = h.replace(":8500</div>", f":{settings.port_hunter}</div>")
    h = h.replace(":7001</div>", f":{settings.port_memory}</div>")
    return HTMLResponse(content=h)


# ── Chat API ──────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        # Force a refresh of environment variables in case .env changed
        load_dotenv(override=True)
        long_term = mem_load_longterm()
        history   = mem_load_history(limit=20)

        system = build_system(req.message, long_term)

        # Build message list for AI
        messages = []
        for turn in history:
            messages.append({"role": "user",      "content": turn.get("role_user", "")})
            messages.append({"role": "assistant", "content": turn.get("role_assistant", "")})

        # Add any history passed directly from UI
        for h in req.history:
            if isinstance(h, dict) and h.get("role") and h.get("content"):
                messages.append(h)

        messages.append({"role": "user", "content": req.message})

        # ── RAG Step: Search Memory Core ──────────────
        rag_context = mem_search_pro(req.message)
        if rag_context:
            # Prepend to system prompt
            system = f"RELEVANT MEMORIES:\n{rag_context}\n\n{system}"

        # ── Autonomous Tool Loop ──────────────
        max_turns = 6
        current_turn = 0
        final_response = ""
        
        while current_turn < max_turns:
            current_turn += 1
            response = call_ai(system, messages)
            
            # Execute any tools found in the response
            tool_results = await dispatcher.execute_all(response)
            
            if not tool_results:
                final_response = response
                break
                
            # If tools were used, inform the history and loop again
            messages.append({"role": "assistant", "content": response})
            for tool_name, result in tool_results:
                # Intercept 'see' tool to process Base64 via Vision AI
                if tool_name == "see":
                    try:
                        res_data = json.loads(result)
                        b64 = res_data.get("base64")
                        if b64:
                            print("\n[CONTEXT]: Analyzing screenshot...")
                            vision_desc = call_vision_ai(b64)
                            result = f"VISUAL OBSERVATION: {vision_desc}"
                    except Exception as ve:
                        logger.error(f"[M1] Vision processing error: {ve}")
                
                observation = format_observation(tool_name, result)
                messages.append({"role": "user", "content": observation})
                logger.info(f"[M1] Tool Result Added: {tool_name}")

        mem_save_turn(req.message, final_response)
        return {"response": final_response, "session_id": req.session_id}

    except Exception as e:
        logger.error(f"[M1] Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Memory endpoints ──────────────────────────────────
@app.get("/api/memory/history")
async def get_history(limit: int = 20):
    turns = mem_load_history(limit)
    total = 0
    try:
        total = len(json.loads(CONV_LOG.read_text()))
    except:
        pass
    return {"turns": turns, "total": total}

@app.post("/api/memory/save")
async def save_turn(req: SaveTurnRequest):
    mem_save_turn(req.user, req.assistant)
    return {"saved": True}

@app.get("/api/memory/longterm")
async def get_longterm():
    try:
        return json.loads(LONG_TERM.read_text(encoding="utf-8"))
    except:
        return {}

@app.post("/api/memory/longterm")
async def set_longterm(entry: MemoryEntry):
    try:
        data = json.loads(LONG_TERM.read_text(encoding="utf-8"))
        data[entry.key] = entry.value
        LONG_TERM.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"saved": True, "key": entry.key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memory/clear")
async def clear_memory():
    CONV_LOG.write_text("[]", encoding="utf-8")
    return {"cleared": True}

@app.get("/api/memory/graph")
async def get_graph():
    try:
        return json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    except:
        return {}


@app.post("/api/config/update")
async def update_config(req: UpdateConfigRequest):
    """Hot-swap an API key in the .env file."""
    try:
        env_path = ROOT / ".env"
        if not env_path.exists():
            return JSONResponse({"success": False, "error": ".env not found"}, status_code=404)
        
        lines = env_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        found = False
        
        for line in lines:
            if line.startswith(f"{req.key}="):
                new_lines.append(f"{req.key}={req.value}")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"{req.key}={req.value}")
            
        env_path.write_text("\n".join(new_lines), encoding="utf-8")
        logger.info(f"[M1] Config Updated: {req.key}")
        
        # Immediate refresh of the environment for the current process
        load_dotenv(override=True)
        
        return {"success": True, "key": req.key}
    except Exception as e:
        logger.error(f"[M1] Config update failed: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# ── Memory UI ─────────────────────────────────────────
@app.get("/memory", response_class=HTMLResponse)
async def memory_ui():
    turns = mem_load_history(50)
    rows = "".join(
        f"<tr><td>{t.get('timestamp','')[:19]}</td>"
        f"<td>{t.get('role_user','')[:100]}</td>"
        f"<td>{t.get('role_assistant','')[:150]}</td></tr>"
        for t in reversed(turns)
    )

    return f"""<!DOCTYPE html><html><head><title>ODIN Memory</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
  body{{background:#080808;color:#c9a84c;font-family:'Share Tech Mono',monospace;padding:2rem}}
  h1{{font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:0.3em;margin-bottom:1.5rem}}
  table{{width:100%;border-collapse:collapse;font-size:0.75rem}}
  th,td{{border:1px solid rgba(201,168,76,0.2);padding:0.5rem;text-align:left;vertical-align:top}}
  th{{color:#888;font-size:0.65rem;letter-spacing:0.2em}}
  td:nth-child(3){{color:#a8d4ff}}
  a{{color:#555;text-decoration:none;font-size:0.65rem;letter-spacing:0.2em}}
  a:hover{{color:#c9a84c}}
</style></head>
<body>
<a href="/">← COMMAND CENTER</a>
<h1 style="margin-top:1rem">ODIN MEMORY</h1>
<table><tr><th>TIME</th><th>YOU</th><th>ODIN</th></tr>{rows}</table>
</body></html>"""


# ── Health / Debug ────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "online",
        "module": "M1-Brain",
        "version": settings.odin_version,
        "port": settings.port_m1,
        "personality_loaded": personality_mod is not None,
        "memory_dir": str(DATA_DIR),
        "providers": {
            "moonshot": bool(settings.moonshot_api_key),
            "nvidia":   bool(settings.nvidia_api_key),
            "gemini":   bool(settings.gemini_api_key),
        }
    }

@app.get("/debug")
async def debug():
    try:
        turns = json.loads(CONV_LOG.read_text())
        lt    = json.loads(LONG_TERM.read_text())
        return {
            "conversation_turns": len(turns),
            "longterm_entries":   len(lt),
            "personality_file":   str(settings.personality_file),
            "personality_exists": settings.personality_file.exists(),
            "dashboard_dir":      str(settings.dashboard_dir),
            "static_dir":         str(settings.static_dir),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/personality")
async def get_personality():
    return {"system_prompt": build_system("test")}


# ══════════════════════════════════════════════════════
#  BOOT
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings.port_brain)
    args = parser.parse_args()

    print("\n" + "="*52)
    print("  ODIN M1 — Brain + Memory")
    print(f"  Version     : {settings.odin_version}")
    print(f"  Personality : {'LOADED' if personality_mod else 'FALLBACK'}")
    print(f"  Memory      : {DATA_DIR}")
    print(f"  Dashboard   : http://localhost:{args.port}")
    print(f"  Chat        : http://localhost:{args.port}/chat")
    
    print("\n  [PROVIDERS STATUS]")
    print(f"  - OpenAI    : {'CONNECTED' if settings.openai_api_key else 'OFFLINE'}")
    print(f"  - Groq LPU  : {'CONNECTED' if settings.groq_api_key else 'OFFLINE'}")
    print(f"  - Moonshot  : {'CONNECTED' if settings.moonshot_api_key else 'OFFLINE'}")
    print(f"  - OpenRouter: {'CONNECTED' if settings.openrouter_api_key else 'OFFLINE'}")
    print(f"  - NVIDIA    : {'CONNECTED' if settings.nvidia_api_key else 'OFFLINE'}")
    print(f"  - Gemini    : {'CONNECTED' if settings.gemini_api_key else 'OFFLINE'}")
    print("="*52 + "\n")
    print(f"  Health      : http://localhost:{args.port}/health")
    print("="*52 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")