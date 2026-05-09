"""
ROOT MAIN.PY — System Orchestrator
====================================
Location: ~/AI/brain/main.py
Author:   Built for Charles by Claude
Platform: Ubuntu / Linux

Boots the entire stack in order:
  1. Brain      :7000
  2. Dashboards :7500
  3. Sense      :8000
  4. Hunter     :8500
  5. Bridge     :8099
  6. n8n        :5678  (external, just checked)

Usage:
  python3 main.py              # boot everything
  python3 main.py --only brain # boot one module
  python3 main.py --skip sense # boot all except one
  python3 main.py --list       # show all modules
  python3 main.py --status     # check what's alive

Ctrl+C shuts everything down clean.
"""

import sys
import time
import signal
import argparse
import subprocess
import threading
from pathlib import Path
from datetime import datetime

import httpx  # pip install httpx

# ── Root path ─────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent

# Use python3 on Ubuntu — respects venv if active
PYTHON = sys.executable

# ── Color output (works on Windows 10+ terminals) ─────────────────────────────
class C:
    GOLD   = "\033[38;5;220m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    GREY   = "\033[90m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

def log(msg: str, color: str = C.GREY):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.GREY}[{ts}]{C.RESET} {color}{msg}{C.RESET}")

def banner():
    print(f"""
{C.GOLD}{C.BOLD}
  ██████╗ ██████╗  █████╗ ██╗███╗   ██╗
  ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║
  ██████╔╝██████╔╝███████║██║██╔██╗ ██║
  ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║
  ██████╔╝██║  ██║██║  ██║██║██║ ╚████║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
{C.RESET}
  {C.GREY}Root Orchestrator  //  Charles's AI Stack{C.RESET}
""")

# ── Module definitions ─────────────────────────────────────────────────────────
# Each entry:
#   name       - short id used in --only / --skip
#   label      - display name
#   script     - path relative to ROOT
#   port       - health check port (None = skip check)
#   health_url - override if not /health
#   delay      - seconds to wait AFTER launching before next module
#   required   - if True, failure aborts the whole boot

MODULES = [
    {
        "name":       "memory",
        "label":      "M1  MEMORY PRO",
        "script":     "M1/memory/main.py",
        "port":       7001,
        "health_url": "http://localhost:7001/health",
        "delay":      2,
        "required":   False,
    },
    {
        "name":       "brain",
        "label":      "M1  BRAIN",
        "script":     "M1/main.py",
        "port":       7000,
        "health_url": "http://localhost:7000/health",
        "delay":      3,
        "required":   True,
    },
    {
        "name":       "dashboards",
        "label":      "M1  DASHBOARDS",
        "script":     "M1/dashboards/server.py",
        "port":       7500,
        "health_url": "http://localhost:7500/health",
        "delay":      2,
        "required":   False,
    },
    {
        "name":       "sense",
        "label":      "M2  SENSE",
        "script":     "M2/main.py",
        "port":       8000,
        "health_url": "http://localhost:8000/health",
        "delay":      2,
        "required":   False,
    },
    {
        "name":       "hunter",
        "label":      "P1  HUNTER",
        "script":     "hunter/main.py",
        "port":       8500,
        "health_url": "http://localhost:8500/health",
        "delay":      2,
        "required":   False,
    },
    {
        "name":       "bridge",
        "label":      "BRIDGE",
        "script":     "bridge.py",
        "port":       8099,
        "health_url": "http://localhost:8099/health",
        "delay":      1,
        "required":   False,
    },
]

# n8n is NOT launched by Python — it's a separate process.
# We just check if it's already running and report status.
N8N_URL = "http://localhost:5678/healthz"

# ── Process registry ───────────────────────────────────────────────────────────
_procs: list[dict] = []   # {"name": str, "proc": subprocess.Popen}

# ── Launch a module ────────────────────────────────────────────────────────────
def launch(module: dict, dry_run: bool = False) -> subprocess.Popen | None:
    script = ROOT / module["script"]

    if not script.exists():
        log(f"  {module['label']:<20} MISSING  ({module['script']})", C.YELLOW)
        return None

    if dry_run:
        log(f"  {module['label']:<20} would launch  python {script}", C.GREY)
        return None

    log(f"  {module['label']:<20} launching...", C.GOLD)

    proc = subprocess.Popen(
        [PYTHON, str(script)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        # No Windows flags needed on Ubuntu
    )

    # Stderr forwarder — prints errors prefixed with module name
    def _forward_stderr(p: subprocess.Popen, label: str):
        for line in p.stderr:
            decoded = line.decode(errors="replace").rstrip()
            if decoded:
                print(f"{C.GREY}[{label}]{C.RESET} {C.RED}{decoded}{C.RESET}")

    t = threading.Thread(target=_forward_stderr, args=(proc, module["name"]), daemon=True)
    t.start()

    return proc

# ── Health check ──────────────────────────────────────────────────────────────
def wait_for_health(url: str, timeout: int = 20, label: str = "") -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

# ── Status table ──────────────────────────────────────────────────────────────
def print_status():
    print(f"\n{C.GOLD}{'─'*52}{C.RESET}")
    print(f"{C.GOLD}  SYSTEM STATUS{C.RESET}")
    print(f"{C.GOLD}{'─'*52}{C.RESET}")
    for m in MODULES:
        url = m.get("health_url", f"http://localhost:{m['port']}/health")
        try:
            r = httpx.get(url, timeout=2)
            alive = r.status_code < 500
        except Exception:
            alive = False
        dot  = f"{C.GREEN}●{C.RESET}" if alive else f"{C.RED}●{C.RESET}"
        stat = f"{C.GREEN}ONLINE {C.RESET}" if alive else f"{C.RED}OFFLINE{C.RESET}"
        port = m.get("port", "----")
        print(f"  {dot}  {m['label']:<20} :{port:<6}  {stat}")

    # n8n external check
    try:
        r = httpx.get(N8N_URL, timeout=2)
        alive = r.status_code < 500
    except Exception:
        alive = False
    dot  = f"{C.GREEN}●{C.RESET}" if alive else f"{C.YELLOW}●{C.RESET}"
    stat = f"{C.GREEN}ONLINE {C.RESET}" if alive else f"{C.YELLOW}NOT DETECTED{C.RESET}"
    print(f"  {dot}  {'n8n (external)':<20} :5678   {stat}")

    print(f"{C.GOLD}{'─'*52}{C.RESET}\n")

# ── Shutdown ───────────────────────────────────────────────────────────────────
def shutdown(signum=None, frame=None):
    print(f"\n{C.YELLOW}  Shutting down...{C.RESET}")
    for entry in reversed(_procs):
        p = entry["proc"]
        name = entry["name"]
        try:
            p.terminate()          # SIGTERM — clean shutdown
            p.wait(timeout=5)
            log(f"  {name} stopped", C.GREY)
        except subprocess.TimeoutExpired:
            log(f"  {name} not responding — killing", C.RED)
            p.kill()
        except Exception as e:
            log(f"  {name} error during shutdown ({e})", C.RED)
    print(f"{C.GOLD}  Stack offline. Good night, sir.{C.RESET}\n")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    banner()

    parser = argparse.ArgumentParser(description="Brain Orchestrator")
    parser.add_argument("--only",    help="Boot only this module")
    parser.add_argument("--skip",    help="Skip this module (comma-separated)")
    parser.add_argument("--list",    action="store_true", help="List modules and exit")
    parser.add_argument("--status",  action="store_true", help="Show live status and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print what would run, don't launch")
    args = parser.parse_args()

    # ── --list ──
    if args.list:
        print(f"{C.GOLD}  Available modules:{C.RESET}")
        for m in MODULES:
            req = " (required)" if m["required"] else ""
            print(f"    {m['name']:<15} :{m['port']}  {m['script']}{req}")
        return

    # ── --status ──
    if args.status:
        print_status()
        return

    skip_names = [s.strip() for s in (args.skip or "").split(",") if s.strip()]

    # Filter modules
    to_run = []
    for m in MODULES:
        if args.only and m["name"] != args.only:
            continue
        if m["name"] in skip_names:
            log(f"  {m['label']:<20} SKIPPED", C.GREY)
            continue
        to_run.append(m)

    if not to_run:
        log("  No modules selected. Use --list to see options.", C.YELLOW)
        return

    # Boot sequence
    print(f"{C.GOLD}  Boot sequence starting...{C.RESET}\n")

    for m in to_run:
        proc = launch(m, dry_run=args.dry_run)

        if proc is None:
            if m["required"] and not args.dry_run:
                log(f"  {m['label']} is REQUIRED and failed to launch. Aborting.", C.RED)
                shutdown()
            continue

        _procs.append({"name": m["name"], "proc": proc})

        # Wait for health
        url = m.get("health_url", f"http://localhost:{m['port']}/health")
        ok  = wait_for_health(url, timeout=20, label=m["label"])

        if ok:
            log(f"  {m['label']:<20} :{m['port']}  ONLINE", C.GREEN)
        else:
            log(f"  {m['label']:<20} :{m['port']}  NOT RESPONDING (still may be starting)", C.YELLOW)
            if m["required"]:
                log(f"  Required module failed health check. Aborting.", C.RED)
                shutdown()

        time.sleep(m.get("delay", 1))

    # Final status board
    print_status()

    if args.dry_run:
        log("  Dry run complete. Nothing was actually launched.", C.YELLOW)
        return

    log("  All systems up. Press Ctrl+C to shut down.\n", C.GREEN)

    # Keep alive — monitor for dead processes
    while True:
        time.sleep(10)
        for entry in _procs:
            p = entry["proc"]
            if p.poll() is not None:
                log(f"  WARNING: {entry['name']} has died (exit {p.returncode})", C.RED)


if __name__ == "__main__":
    main()