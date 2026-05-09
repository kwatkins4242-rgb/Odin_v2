"""
ODIN-HUNTER | Main Entry Point
Bug bounty automation framework — ODIN Industries
Port: 8010
"""

import os
import asyncio
import uvicorn
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from settings import get_settings
load_dotenv()
settings = get_settings()

# ── Safe imports — stubs if modules not built yet ─────────────
try:
    from integrations.core_bridge import CoreBridge
    core_bridge = CoreBridge()
except ImportError:
    class CoreBridge:
        async def announce(self, msg): print(f"[CORE] {msg}")
        async def log(self, msg):     print(f"[CORE LOG] {msg}")
    core_bridge = CoreBridge()

try:
    from integrations.memory_bridge import MemoryBridge
    memory_bridge = MemoryBridge()
except ImportError:
    class MemoryBridge:
        async def store_finding(self, *args): pass
    memory_bridge = MemoryBridge()

try:
    from integrations.notify_bridge import NotifyBridge
    notify_bridge = NotifyBridge()
except ImportError:
    class NotifyBridge:
        async def send(self, msg): print(f"[NOTIFY] {msg}")
    notify_bridge = NotifyBridge()

try:
    from recon.target_manager import TargetManager
    target_mgr = TargetManager()
except ImportError:
    class TargetManager:
        async def run_full_recon(self, target): return {"target": target, "status": "stub"}
    target_mgr = TargetManager()

try:
    from legal.scope_checker import ScopeChecker
    scope_checker = ScopeChecker()
except ImportError:
    class ScopeChecker:
        async def check(self, target, program, platform): return True
    scope_checker = ScopeChecker()

try:
    from legal.rules_engine import RulesEngine
    rules_engine = RulesEngine()
except ImportError:
    class RulesEngine:
        async def check(self, platform, program): return True
    rules_engine = RulesEngine()

try:
    from platforms.platform_manager import PlatformManager
    platform_mgr = PlatformManager()
except ImportError:
    class PlatformManager:
        async def get_connected_platforms(self): return []
        async def get_all_programs(self):        return []
        async def get_programs(self, p):         return []
        async def submit_report(self, *args):    return {"status": "stub"}
    platform_mgr = PlatformManager()

try:
    from tracker.submission_tracker import SubmissionTracker
    submission_tracker = SubmissionTracker()
except ImportError:
    class SubmissionTracker:
        async def get_all(self):                     return []
        async def track(self, *args):                return "stub-id"
        async def submit(self, submission_id):       return {"status": "stub"}
    submission_tracker = SubmissionTracker()

try:
    from tracker.payout_tracker import PayoutTracker
    payout_tracker = PayoutTracker()
except ImportError:
    class PayoutTracker:
        async def get_all(self): return []
    payout_tracker = PayoutTracker()

try:
    from tracker.stats_dashboard import StatsDashboard
    stats_dashboard = StatsDashboard()
except ImportError:
    class StatsDashboard:
        async def get_summary(self):    return {"status": "no data yet"}
        async def get_full_stats(self): return {"status": "no data yet"}
    stats_dashboard = StatsDashboard()

try:
    from ai_engine.claude_hunter import ClaudeHunter
    claude_hunter = ClaudeHunter()
except ImportError:
    class ClaudeHunter:
        async def analyze_findings(self, findings, target, program):
            return [{"title": f["title"], "confidence": 0.5, **f} for f in findings]
    claude_hunter = ClaudeHunter()

try:
    from scanner.vuln_scanner import VulnScanner
    vuln_scanner = VulnScanner()
except ImportError:
    class VulnScanner:
        active_scan_count = 0
        async def scan_all(self, target, recon_data): return []
    vuln_scanner = VulnScanner()

try:
    from reporter.report_builder import ReportBuilder
    report_builder = ReportBuilder()
except ImportError:
    class ReportBuilder:
        async def build(self, finding, target, platform):
            return {"title": finding.get("title"), "target": target}
    report_builder = ReportBuilder()

try:
    from db.database import init_db
except ImportError:
    async def init_db(): pass

try:
    from integrations.kali_bridge import KaliBridge
    kali_bridge = KaliBridge()
except ImportError:
    class KaliBridge:
        async def get_available_tools(self): return []
    kali_bridge = KaliBridge()

try:
    from integrations.burp_bridge import BurpBridge
    burp_bridge = BurpBridge()
except ImportError:
    class BurpBridge:
        async def run_active_scan(self, target): return []
    burp_bridge = BurpBridge()

try:
    from scanner.swagger_scanner import SwaggerScanner
    swagger_scanner = SwaggerScanner()
except ImportError:
    class SwaggerScanner:
        async def scan(self, target, recon): return [], {}
    swagger_scanner = SwaggerScanner()


# ── Lifespan ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"""
+--------------------------------------+
|     ODIN-HUNTER ONLINE  :{settings.port_hunter}        |
|  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  |
|  Core:   {os.getenv('ODIN_CORE_URL', 'http://localhost:8000')}   |
|  AI:     {os.getenv('AI_PROVIDER', 'Open AI')} / {os.getenv('AI_MODEL', 'kimi-k2')}     |
+--------------------------------------+
    """)
    await core_bridge.announce("Hunter is online and ready to hunt.")
    yield


# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title="Hunter",
    description="Automated bug bounty hunting framework — ODIN Industries",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════
# DASHBOARD / ROOT
# ══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    # Try custom dashboard first
    custom_path = Path(__file__).resolve().parent / "static" / "index.html"
    if custom_path.exists():
        return HTMLResponse(content=custom_path.read_text(encoding="utf-8"))
    
    return HTMLResponse(
        content="<h1 style='font-family:monospace;color:#0f0'>ODIN-HUNTER root landing. Place dashboard HTML at static/index.html</h1>",
        status_code=200
    )

# ══════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "odin-hunter",
        "port": settings.port_hunter,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ping")
async def ping():
    return {"status": "online", "service": "odin-hunter"}

@app.get("/status")
async def status():
    stats = await stats_dashboard.get_summary()
    return {
        "hunter": "online",
        "stats": stats,
        "platforms_connected": await platform_mgr.get_connected_platforms(),
        "active_scans": vuln_scanner.active_scan_count
    }

# ══════════════════════════════════════════════════════════════
# MANUAL TOOL TRIGGERS
# ══════════════════════════════════════════════════════════════

@app.get("/kali/tools")
async def get_kali_tools():
    """Discover which offensive tools are available on the connected Kali Linux box."""
    tools = await kali_bridge.get_available_tools()
    return {"status": "ok", "kali_tools": tools}

@app.post("/burp/scan")
async def trigger_burp_scan(payload: dict):
    """Manually trigger a Burp Enterprise active scan via REST API."""
    target = payload.get("target")
    if not target:
        raise HTTPException(status_code=400, detail="target required")
    findings = await burp_bridge.run_active_scan(target)
    return {"status": "scan_complete", "findings": len(findings)}

@app.get("/swagger/surface")
async def inspect_swagger(target: str):
    """Attempt to find and parse a Swagger/OpenAPI spec on the target."""
    findings, surface = await swagger_scanner.scan(target, {})
    return {"status": "ok", "surface": surface, "instant_findings": findings}


# ══════════════════════════════════════════════════════════════
# HUNT PIPELINE
# ══════════════════════════════════════════════════════════════

@app.post("/hunt")
async def start_hunt(payload: dict, background_tasks: BackgroundTasks):
    """Start a full hunt on a target."""
    target   = payload.get("target")
    program  = payload.get("program_id", "")
    platform = payload.get("platform", "hackerone")

    if not target:
        raise HTTPException(status_code=400, detail="target is required")

    in_scope = await scope_checker.check(target, program, platform)
    if not in_scope:
        return {"error": f"{target} is OUT OF SCOPE. Hunt aborted.", "safe": False}

    allowed = await rules_engine.check(platform, program)
    if not allowed:
        return {"error": "Rules engine blocked this hunt.", "safe": False}

    background_tasks.add_task(run_full_hunt, target, program, platform)
    return {"status": "hunt_started", "target": target, "program": program}


async def run_full_hunt(target: str, program_id: str, platform: str):
    """Full automated hunt pipeline."""
    try:
        await notify_bridge.send(f"🎯 Hunt started on {target}")
        await core_bridge.log(f"Hunter scanning: {target}")

        # 1. Recon
        print(f"[RECON] {target}")
        recon_data = await target_mgr.run_full_recon(target)
        await memory_bridge.store_finding("recon", target, recon_data)

        # 2. Vuln scan
        print(f"[SCAN] {target}")
        findings = await vuln_scanner.scan_all(target, recon_data)

        if not findings:
            await notify_bridge.send(f"✅ {target} — No findings this run.")
            return

        # 3. AI analysis
        print(f"[AI] Analyzing {len(findings)} findings")
        analyzed = await claude_hunter.analyze_findings(findings, target, program_id)

        # 4. Build + track reports
        for finding in analyzed:
            if finding.get("confidence", 0) >= 0.7:
                report = await report_builder.build(finding, target, platform)
                submission_id = await submission_tracker.track(finding, report, platform)
                await memory_bridge.store_finding("vulnerability", target, finding)

                if os.getenv("HUNTER_AUTO_SUBMIT", "false").lower() == "true":
                    await platform_mgr.submit_report(platform, program_id, report)
                    await notify_bridge.send(f"📤 Report submitted: {finding.get('title')}")
                else:
                    await notify_bridge.send(
                        f"🐛 Ready for review: {finding.get('title')} "
                        f"[{finding.get('severity', 'unknown').upper()}] — ID: {submission_id}"
                    )

        await core_bridge.log(f"Hunt complete: {target} — {len(analyzed)} findings analyzed")

    except Exception as e:
        print(f"[HUNT ERROR] {e}")
        await core_bridge.log(f"Hunter error on {target}: {str(e)}")


# ══════════════════════════════════════════════════════════════
# PLATFORMS / TRACKER / STATS
# ══════════════════════════════════════════════════════════════

@app.get("/platforms")
async def get_platforms():
    return await platform_mgr.get_all_programs()

@app.get("/platforms/{platform}/programs")
async def get_programs(platform: str):
    return await platform_mgr.get_programs(platform)

@app.get("/submissions")
async def get_submissions():
    return await submission_tracker.get_all()

@app.get("/payouts")
async def get_payouts():
    return await payout_tracker.get_all()

@app.get("/stats")
async def get_stats():
    return await stats_dashboard.get_full_stats()

@app.post("/submit/{submission_id}")
async def manual_submit(submission_id: str):
    return await submission_tracker.submit(submission_id)


# ══════════════════════════════════════════════════════════════
# CORE WEBHOOK
# ══════════════════════════════════════════════════════════════

@app.post("/webhook/core")
async def core_webhook(payload: dict):
    """Receive hunt commands from odin-core."""
    command = payload.get("command")
    if command == "hunt":
        target   = payload.get("target")
        program  = payload.get("program_id", "")
        platform = payload.get("platform", "hackerone")
        asyncio.create_task(run_full_hunt(target, program, platform))
        return {"status": "hunt_queued", "target": target}
    return {"status": "unknown_command"}


# ══════════════════════════════════════════════════════════════
# STATIC / DASHBOARD
# ══════════════════════════════════════════════════════════════

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(
        content="<h1 style='font-family:monospace;color:#0f0'>ODIN-HUNTER online. Place dashboard HTML at static/index.html</h1>",
        status_code=200
    )

# Mount static files last — auto-create dir so it never crashes
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ══════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port_hunter, reload=True)
