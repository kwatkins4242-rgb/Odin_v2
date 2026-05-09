#!/usr/bin/env python3
import os
import json
import hashlib
import pathlib
import datetime
import time
import logging
from pathlib import Path

# ODIN Vacuum — Filesystem Sanity Checker
# Scans for invalid characters, oversized files, and reports issues.

CONFIG_PATH = Path(__file__).parent / "vacuum_config.json"

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def run_vacuum():
    cfg = load_config()
    root = Path(cfg['odin_root'])
    reports_dir = Path(cfg['reports_dir'])
    logs_dir = Path(cfg['logs_dir'])
    
    # Setup Logging
    log_file = logs_dir / "vacuum.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger('vacuum')

    print(f"[VACUUM] Starting scan on {root}...")
    
    try:
        # We only scan 2 levels deep to avoid hanging on deep node_modules etc.
        # But for ODIN, we might want rglob. Let's stick to rglob but ignore common junk.
        for p in root.rglob('*'):
            # Skip common noise folders
            if any(part in p.parts for part in ['.git', '__pycache__', '.venv', 'node_modules']):
                continue
                
            issues = []
            
            # 1. Banned Characters
            if any(c in p.name for c in cfg['banned_chars']):
                issues.append("illegal_char")
            
            # 2. Oversized Files
            if p.is_file():
                try:
                    size_mb = p.stat().st_size / (1024 * 1024)
                    if size_mb > cfg['max_file_size_mb']:
                        issues.append("oversized")
                except: pass

            # 3. Dangling Symlinks (Less common on Windows but good to have)
            if p.is_symlink() and not p.exists():
                issues.append("dangling_symlink")

            if issues:
                report = {
                    "path": str(p),
                    "issues": issues,
                    "time": datetime.datetime.utcnow().isoformat(),
                    "size_mb": round(p.stat().st_size / (1024 * 1024), 2) if p.is_file() else 0
                }
                
                # Generate unique report filename
                report_id = hashlib.md5(str(p).encode()).hexdigest()
                report_file = reports_dir / f"{report_id}.json"
                
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                
                logger.warning(f"Issue found: {p} -> {issues}")

    except Exception as e:
        logger.error(f"Scan failed: {e}")

if __name__ == "__main__":
    cfg = load_config()
    print(f"[VACUUM] Initialized. Cycle: {cfg['duty_cycle_seconds']}s")
    while True:
        run_vacuum()
        time.sleep(cfg['duty_cycle_seconds'])
