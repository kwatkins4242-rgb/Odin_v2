import shutil
import os
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

# --- Path Setup ---
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from settings import get_settings
settings = get_settings()

def get_weekly_backup_name():
    now = datetime.now()
    return f"ODIN_WEEKLY_{now.strftime('%Y_W%U')}"

def save_now(mode="checkpoint", custom_name=None):
    """
    Performs a full project backup.
    Modes: 
      - 'checkpoint': Overwrites the 'last_restore_point' folder.
      - 'weekly': Creates a permanent weekly archive.
      - 'manual': Creates a timestamped snapshot.
    """
    source = settings.root_dir
    backup_base = Path(settings.backup_root)
    
    if not backup_base.exists():
        backup_base.mkdir(parents=True, exist_ok=True)
        
    if mode == "checkpoint":
        target = backup_base / "last_restore_point"
    elif mode == "weekly":
        target = backup_base / get_weekly_backup_name()
    else:
        name = custom_name or f"ODIN_MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target = backup_base / name

    print(f"[HEARTBEAT] Saving to: {target} (Mode: {mode})")
    
    try:
        # Clear target if it exists and we're in checkpoint mode
        if target.exists() and mode == "checkpoint":
            shutil.rmtree(target)
            
        # Define ignore patterns
        ignore_patterns = shutil.ignore_patterns(
            '.venv', 'node_modules', '.git', '__pycache__', 
            '*.log', '.DS_Store', 'ODIN_Backups'
        )
        
        shutil.copytree(source, target, ignore=ignore_patterns, dirs_exist_ok=True)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Save completed successfully.")
        return True
    except Exception as e:
        print(f"[HEARTBEAT] Save failed: {e}")
        return False

def heartbeat_loop():
    print("ODIN Heartbeat started. Monitoring for save events...")
    
    last_checkpoint_time = 0
    last_weekly_time = 0
    
    # 15 minutes = 900 seconds
    CHECKPOINT_INTERVAL = 900 
    
    while True:
        now = time.time()
        
        # 1. Checkpoint Save (15 mins)
        if now - last_checkpoint_time >= CHECKPOINT_INTERVAL:
            save_now(mode="checkpoint")
            last_checkpoint_time = now
            
        # 2. Weekly Save Check
        # We check if a backup for this week already exists
        weekly_name = get_weekly_backup_name()
        if not (Path(settings.backup_root) / weekly_name).exists():
            save_now(mode="weekly")
            
        time.sleep(60) # Wake up every minute to check schedule

if __name__ == "__main__":
    # If run directly, start the background loop
    heartbeat_loop()
