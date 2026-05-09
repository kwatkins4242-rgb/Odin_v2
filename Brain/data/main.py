"""
ODIN M1 — Brain
===============
Location: C:\\AI\\MyOdin\\M1\\main.py
Port: 8000

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

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Path setup ────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

# Import the modern cognitive suite
from .brain import get_brain
brain = get_brain()

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
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "personality", settings.personality_file
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger.info("[M1] ✓ Personality + engines loaded")
        return mod
    except Exception as e:
        logger.error(f"[M1] ✗ Personality load failed: {e}")
        return None

personality_mod = load_personality()

def build_system(user_message: str = "", long_term: str = "") -> str:
    if personality_mod and hasattr(personality_mod, "build_system_prompt"):
        return personality_mod.build_system_prompt(user_message, long_term)
    return (
        "You are ODIN — Charles's personal AI partner. "
        "Sharp, direct, loyal. Address Charles as 'sir'. "
        "WARNING: Full personality file failed to load."
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
    try:
        raw = json.loads(CONV_LOG.read_text(encoding="utf-8"))
        raw.append({
            "role_user": user,
            "role_assistant": assistant,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(raw) > 500:
            raw = raw[-500:]
        CONV_LOG.write_text(
            json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"[M1] Failed to save turn: {e}")


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
def call_ai(system: str, messages: list, max_tokens: int = 2000) -> str:

    full_messages = [{"role": "system", "content": system}] + messages

    # 1. Moonshot
    if settings.moonshot_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.moonshot_api_key,
                base_url=settings.moonshot_base_url
            )
            resp = client.chat.completions.create(
                model=settings.moonshot_model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            result = resp.choices[0].message.content
            if result:
                logger.info("[M1] ✓ AI → Moonshot")
                return result
        except Exception as e:
            logger.warning(f"[M1] Moonshot failed: {e}")

    # 2. NVIDIA NIM
    if settings.nvidia_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=settings.nvidia_base_url,
                api_key=settings.nvidia_api_key
            )
            resp = client.chat.completions.create(
                model=settings.nvidia_model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            result = resp.choices[0].message.content
            if result:
                logger.info("[M1] ✓ AI → NVIDIA")
                return result
        except Exception as e:
            logger.warning(f"[M1] NVIDIA failed: {e}")

    # 3. Gemini
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=system
            )
            gemini_msgs = []
            for m in messages:
                role = "user" if m["role"] == "user" else "model"
                gemini_msgs.append({"role": role, "parts": [m["content"]]})
            
            if gemini_msgs:
                chat = model.start_chat(history=gemini_msgs[:-1])
                result = chat.send_message(gemini_msgs[-1]["parts"][0]).text
                if result:
                    logger.info("[M1] ✓ AI → Gemini")
                    return result
        except Exception as e:
            logger.warning(f"[M1] Gemini failed: {e}")

    logger.error("[M1] ✗ All AI providers failed")
    return (
        "Sir, all AI providers are offline. "
        "Check your API keys in .env — at least one needs to be valid."
    )


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
    app.mount("/dash", StaticFiles(directory=str(settings.dashboard_dir), html=True), name="dashboards")


# ── Models ────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    history: list = []

class MemoryEntry(BaseModel):
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

        ::-webkit-scrollbar { width:4px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:rgba(201,168,76,0.2); }

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
        <a class="status-pill" href="http://localhost:8020/health" target="_blank"><div class="dot grey" id="dot-m3"></div> M3 CORE :8020</a>
        <a class="status-pill" href="http://localhost:8040/health" target="_blank"><div class="dot grey" id="dot-hunter"></div> P1 HUNTER :8040</a>
        <a class="status-pill" href="http://localhost:8030/health" target="_blank"><div class="dot grey" id="dot-mobile"></div> P2 MOBILE :8030</a>
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
                <div class="card-title">MEMORY SNAPSHOT</div>
                <div id="memList"><div class="mem-item" style="color:#333">Loading...</div></div>
            </div>
            <div class="card">
                <div class="card-title">SYSTEM</div>
                <div style="font-size:0.65rem;line-height:2;color:#555">
                    <div>VERSION <span style="color:#c9a84c;float:right">2.0.0</span></div>
                    <div>AI PRIMARY <span style="color:#c9a84c;float:right">MOONSHOT</span></div>
                    <div>AI FALLBACK <span style="color:#c9a84c;float:right">NVIDIA → GEMINI</span></div>
                    <div>BRIDGE <span style="color:#c9a84c;float:right">:8099</span></div>
                    <div>n8n <span style="color:#c9a84c;float:right">:5678</span></div>
                    <div>MEMORY <span id="turnCount" style="color:#c9a84c;float:right">--</span></div>
                </div>
            </div>
        </div>
    </div>

    <div class="module-grid">
        <a class="module-tile" href="http://localhost:8010" target="_blank"><div class="tile-name">M2 SENSES</div><div class="tile-desc">Vision · Voice · Wake</div><div class="tile-port">:8010</div></a>
        <a class="module-tile" href="http://localhost:8020" target="_blank"><div class="tile-name">M3 CORE</div><div class="tile-desc">Eng · Comms · Control</div><div class="tile-port">:8020</div></a>
        <a class="module-tile" href="http://localhost:8040" target="_blank"><div class="tile-name">P1 HUNTER</div><div class="tile-desc">Recon · Search · Gather</div><div class="tile-port">:8040</div></a>
        <a class="module-tile" href="http://localhost:8030" target="_blank"><div class="tile-name">P2 MOBILE</div><div class="tile-desc">Mobile Interface</div><div class="tile-port">:8030</div></a>
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
        {id:'m3',url:'http://localhost:8020/health'},
        {id:'hunter',url:'http://localhost:8040/health'},
        {id:'mobile',url:'http://localhost:8030/health'},
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

    // Wire up button and Enter key properly
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', function(e) {
        if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    addMsg('odin','Master dashboard online. All systems initializing, sir.');
</script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


# ── Chat API ──────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        # Route through the full cognitive suite (OdinBrain)
        # We pass the session_id and history for context
        result = await brain.process(
            session_id=req.session_id,
            message=req.message,
            raw_context={"history": req.history}
        )
        
        return {
            "response": result["response"], 
            "session_id": req.session_id,
            "confidence": result.get("confidence", 0),
            "thought_process": result.get("thought_process", [])
        }

    except Exception as e:
        logger.error(f"[M1] Brain execution error: {e}")
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
    print("\\n" + "="*52)
    print("  ODIN M1 — Brain + Memory")
    print(f"  Version     : {settings.odin_version}")
    print(f"  Personality : {'LOADED' if personality_mod else 'FALLBACK'}")
    print(f"  Memory      : {DATA_DIR}")
    print(f"  Dashboard   : http://localhost:8000")
    print(f"  Chat        : http://localhost:8000/chat")
    print(f"  Health      : http://localhost:8000/health")
    print("="*52 + "\\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")