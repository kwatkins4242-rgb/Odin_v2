import os
import sys
from pathlib import Path

# Add the current directory to sys.path to allow importing write_file
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from write_file import write_file

def run_demo():
    # PERMITTED WORKING DIRECTORY (Project Root)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    
    filename = "ODIN_CAPABILITIES.txt"
    content = """
======================================================
  ODIN SYSTEM CAPABILITIES REPORT
  TIMESTAMP: 2026-04-12
======================================================

[✓] STABILIZATION: ALL 17 MODULES SYNCHRONIZED
[✓] FILE OPERATIONS: AGENT ODIN ACTIVE
[✓] DASHBOARD: UNIFIED MASTER HUB (8080)
[✓] BRIDGE: N8N RELAY & MAIL SERVICE
[✓] MOBILE: PWA READY FOR INSTALLATION

This file was written automatically by Agent Odin's 
file-handling logic to demonstrate operational readiness.

ODIN INDUSTRIES // FORT WORTH, TX
======================================================
"""

    print(f"Executing Agent Odin file-writing demo...")
    # write_file(working_directory, file_path, content)
    result = write_file(str(PROJECT_ROOT), filename, content)
    print(result)

if __name__ == "__main__":
    run_demo()
