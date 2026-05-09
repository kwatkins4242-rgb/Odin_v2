"""
ODIN Project Audit Tool
Run this from C:\AI\MyOdin\
It will generate odin_audit_report.txt with a full map of the project.
Usage: python odin_audit.py
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent
REPORT = ROOT / "odin_audit_report.txt"

IGNORE_DIRS = {".venv", "venv", "myenv", ".venv", "node_modules", "__pycache__", ".git", "Python_3.11.1"}
IGNORE_EXTS = {".pyc", ".pyo", ".exe", ".dll", ".so", ".bin"}

lines = []

def log(msg=""):
    lines.append(msg)
    print(msg)

def scan_files(root: Path):
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            fp = Path(dirpath) / f
            if fp.suffix.lower() not in IGNORE_EXTS:
                all_files.append(fp)
    return all_files

def categorize(files):
    cats = defaultdict(list)
    for f in files:
        ext = f.suffix.lower()
        if ext == ".py":
            cats["Python"].append(f)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            cats["JavaScript/Node"].append(f)
        elif ext == ".json":
            cats["JSON/Config"].append(f)
        elif ext in (".bat", ".sh", ".cmd"):
            cats["Scripts/Batch"].append(f)
        elif ext in (".env", ".ini", ".cfg", ".toml", ".yaml", ".yml"):
            cats["Config/Env"].append(f)
        elif ext in (".txt", ".md", ".log"):
            cats["Docs/Logs"].append(f)
        else:
            cats["Other"].append(f)
    return cats

def check_py_imports(filepath: Path):
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        imports = []
        broken = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line)
        return imports, content
    except:
        return [], ""

def find_memory_references(files):
    memory_files = []
    for f in files:
        if f.suffix == ".py":
            try:
                content = f.read_text(encoding="utf-8", errors="ignore").lower()
                if any(kw in content for kw in ["memory", "conversation_log", "long_term", "shortterm", "short_term"]):
                    memory_files.append(f)
            except:
                pass
    return memory_files

def find_path_definitions(files):
    path_info = []
    for f in files:
        if f.suffix == ".py":
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    if any(kw in line for kw in ["conversation_log", "long_term_memory", "CONV_LOG", "MEMORY_FILE", "LONG_TERM"]):
                        path_info.append((f, i, line.strip()))
            except:
                pass
    return path_info

def find_startup_files(files):
    starters = []
    for f in files:
        name = f.name.lower()
        if any(kw in name for kw in ["main", "start", "run", "launch", "core_start", "init"]):
            starters.append(f)
    return starters

def find_duplicates(files):
    name_map = defaultdict(list)
    for f in files:
        name_map[f.name.lower()].append(f)
    return {k: v for k, v in name_map.items() if len(v) > 1}

def check_json_health(files):
    broken = []
    large = []
    for f in files:
        if f.suffix == ".json":
            try:
                size = f.stat().st_size
                if size > 500_000:
                    large.append((f, size))
                if size < 10_000_000:  # Don't try to parse huge files
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    json.loads(content)
            except json.JSONDecodeError as e:
                broken.append((f, str(e)))
            except:
                pass
    return broken, large

def find_env_vars(files):
    env_keys = set()
    for f in files:
        if f.name == ".env":
            try:
                for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.startswith("#"):
                        key = line.split("=")[0].strip()
                        env_keys.add(key)
            except:
                pass
    return env_keys

def find_ports(files):
    ports = []
    for f in files:
        if f.suffix in (".py", ".js", ".json", ".env"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    if "port" in line.lower() and any(c.isdigit() for c in line):
                        ports.append((f, i, line.strip()))
            except:
                pass
    return ports

# ── RUN AUDIT ────────────────────────────────────────────────────────────────

log("=" * 70)
log("  ODIN PROJECT AUDIT REPORT")
log(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log(f"  Root: {ROOT}")
log("=" * 70)

log()
log("── SCANNING FILES ──────────────────────────────────────────────────────")
all_files = scan_files(ROOT)
log(f"Total files found: {len(all_files)}")

cats = categorize(all_files)
for cat, flist in sorted(cats.items()):
    log(f"  {cat}: {len(flist)} files")

# ── FOLDER STRUCTURE ─────────────────────────────────────────────────────────
log()
log("── TOP-LEVEL FOLDER STRUCTURE ──────────────────────────────────────────")
for item in sorted(ROOT.iterdir()):
    if item.name not in IGNORE_DIRS and not item.name.startswith("."):
        if item.is_dir():
            subcount = sum(1 for _ in item.rglob("*") if _.is_file())
            log(f"  📁 {item.name}/  ({subcount} files)")
        else:
            size = item.stat().st_size
            log(f"  📄 {item.name}  ({size:,} bytes)")

# ── STARTUP FILES ─────────────────────────────────────────────────────────────
log()
log("── STARTUP / ENTRY POINT FILES ─────────────────────────────────────────")
starters = find_startup_files(all_files)
for f in starters:
    rel = f.relative_to(ROOT)
    size = f.stat().st_size
    log(f"  {rel}  ({size:,} bytes)")

# ── MEMORY PIPELINE ──────────────────────────────────────────────────────────
log()
log("── MEMORY PIPELINE FILES ───────────────────────────────────────────────")
mem_files = find_memory_references(all_files)
for f in mem_files:
    rel = f.relative_to(ROOT)
    log(f"  {rel}")

log()
log("── MEMORY PATH DEFINITIONS (where paths are set) ───────────────────────")
path_defs = find_path_definitions(all_files)
for f, lineno, line in path_defs:
    rel = f.relative_to(ROOT)
    log(f"  {rel}:{lineno}  →  {line}")

# ── DUPLICATE FILES ───────────────────────────────────────────────────────────
log()
log("── DUPLICATE FILENAMES ─────────────────────────────────────────────────")
dupes = find_duplicates(all_files)
if dupes:
    for name, fpaths in sorted(dupes.items()):
        log(f"  ⚠️  {name}")
        for fp in fpaths:
            log(f"      {fp.relative_to(ROOT)}")
else:
    log("  None found.")

# ── JSON HEALTH ───────────────────────────────────────────────────────────────
log()
log("── JSON FILE HEALTH ────────────────────────────────────────────────────")
broken_json, large_json = check_json_health(all_files)
if broken_json:
    log("  BROKEN JSON FILES:")
    for f, err in broken_json:
        log(f"    ❌ {f.relative_to(ROOT)}: {err}")
else:
    log("  All JSON files parse cleanly.")

if large_json:
    log("  LARGE JSON FILES (>500KB):")
    for f, size in large_json:
        log(f"    📦 {f.relative_to(ROOT)}: {size/1024:.0f} KB")

# ── ENV VARS ──────────────────────────────────────────────────────────────────
log()
log("── .ENV KEYS FOUND ─────────────────────────────────────────────────────")
env_keys = find_env_vars(all_files)
if env_keys:
    for k in sorted(env_keys):
        log(f"  {k}")
else:
    log("  No .env file found or empty.")

# ── PORTS ─────────────────────────────────────────────────────────────────────
log()
log("── PORT DEFINITIONS ────────────────────────────────────────────────────")
ports = find_ports(all_files)
seen_ports = set()
for f, lineno, line in ports:
    if line not in seen_ports:
        seen_ports.add(line)
        rel = f.relative_to(ROOT)
        log(f"  {rel}:{lineno}  →  {line}")

# ── ALL PYTHON FILES ──────────────────────────────────────────────────────────
log()
log("── ALL PYTHON FILES ────────────────────────────────────────────────────")
for f in sorted(cats.get("Python", [])):
    rel = f.relative_to(ROOT)
    size = f.stat().st_size
    modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    log(f"  {rel}  ({size:,} bytes)  modified: {modified}")

# ── ALL BATCH/SCRIPT FILES ────────────────────────────────────────────────────
log()
log("── BATCH / SHELL SCRIPTS ───────────────────────────────────────────────")
for f in sorted(cats.get("Scripts/Batch", [])):
    rel = f.relative_to(ROOT)
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
        log(f"  {rel}:")
        for line in content.splitlines():
            if line.strip():
                log(f"    {line.strip()}")
    except:
        log(f"  {rel}: (could not read)")

# ── SUMMARY & RECOMMENDATIONS ─────────────────────────────────────────────────
log()
log("=" * 70)
log("  SUMMARY & KEY FINDINGS")
log("=" * 70)
log(f"  Total files scanned:     {len(all_files)}")
log(f"  Python files:            {len(cats.get('Python', []))}")
log(f"  JS/Node files:           {len(cats.get('JavaScript/Node', []))}")
log(f"  Duplicate filenames:     {len(dupes)}")
log(f"  Broken JSON files:       {len(broken_json)}")
log(f"  Large JSON files:        {len(large_json)}")
log(f"  Memory-related files:    {len(mem_files)}")
log(f"  Startup/entry files:     {len(starters)}")
log()
log("  ACTION ITEMS:")
log("  1. Check memory path definitions above — mismatched paths = blank memory")
log("  2. Review duplicate filenames — likely dead code")
log("  3. Large JSON files may need archiving or trimming")
log("  4. Startup files show what actually runs when Odin launches")
log()
log("  Run this audit again after cleanup to compare.")
log("=" * 70)

# Write report
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"\n✅ Report saved to: {REPORT}")