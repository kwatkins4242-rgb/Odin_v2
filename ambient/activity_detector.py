"""
ODIN-SENSE — Activity Detector
Detects what Charles is currently doing:
  - Which app is in focus (VS Code, browser, terminal, etc.)
  - What task/project context (coding, browsing, writing)
  - How long he's been at it

This gives ODIN ambient context without Charles having to narrate.
"You've been in VS Code for 3 hours — want me to help debug?"
"Looks like you're on YouTube — taking a break?"
"""

import os
import time
import psutil
from typing import Optional

POLL_INTERVAL_SEC = float(os.getenv("ACTIVITY_POLL_INTERVAL", "5.0"))

# App → task type mapping
APP_TASK_MAP = {
    # IDEs & Code
    "code":             "coding",
    "vscode":           "coding",
    "visual studio":    "coding",
    "pycharm":          "coding",
    "sublime":          "coding",
    "vim":              "coding",
    "nvim":             "coding",
    "emacs":            "coding",
    "cursor":           "coding",
    "terminal":         "terminal",
    "cmd":              "terminal",
    "powershell":       "terminal",
    "bash":             "terminal",
    "konsole":          "terminal",
    "gnome-terminal":   "terminal",
    # Browsers
    "chrome":           "browsing",
    "firefox":          "browsing",
    "edge":             "browsing",
    "brave":            "browsing",
    "safari":           "browsing",
    # Communication
    "slack":            "communication",
    "discord":          "communication",
    "zoom":             "communication",
    "teams":            "communication",
    "whatsapp":         "communication",
    "telegram":         "communication",
    # Productivity
    "notion":           "writing",
    "obsidian":         "writing",
    "word":             "writing",
    "docs":             "writing",
    "excel":            "spreadsheet",
    "sheets":           "spreadsheet",
    # Music / Entertainment
    "spotify":          "music",
    "vlc":              "media",
    "youtube":          "media",
    # Files
    "explorer":         "files",
    "finder":           "files",
    "nautilus":         "files",
}


class ActivityDetector:

    def __init__(self, state: dict):
        self._state           = state
        self._session_start   = {}   # app_name → start_time
        self._running         = False

    def run(self):
        """Background polling loop."""
        self._running = True
        while self._running:
            try:
                self._update()
            except Exception as e:
                print(f"[ActivityDetector] Error: {e}")
            time.sleep(POLL_INTERVAL_SEC)

    def _update(self):
        app_name   = self._get_active_window_app()
        window     = self._get_active_window_title()
        task_type  = self._classify_task(app_name)

        # Track session time per app
        now = time.time()
        if app_name and app_name not in self._session_start:
            self._session_start[app_name] = now

        self._state["active_app"]    = app_name
        self._state["active_window"] = window
        self._state["active_task"]   = task_type

        # Build duration info
        if app_name and app_name in self._session_start:
            duration = now - self._session_start[app_name]
            self._state["current_task_duration_min"] = round(duration / 60, 1)

    def _get_active_window_app(self) -> Optional[str]:
        """Get the process name of the currently active window."""
        try:
            import sys
            if sys.platform == "win32":
                return self._get_active_win32()
            elif sys.platform.startswith("linux"):
                return self._get_active_linux()
            elif sys.platform == "darwin":
                return self._get_active_macos()
        except Exception:
            pass
        return None

    def _get_active_window_title(self) -> Optional[str]:
        """Get window title of active app."""
        try:
            import sys
            if sys.platform == "win32":
                import ctypes
                hwnd  = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
                buf   = ctypes.create_unicode_buffer(length)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length)
                return buf.value or None
        except Exception:
            pass
        return None

    def _get_active_win32(self) -> Optional[str]:
        import ctypes
        import ctypes.wintypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid  = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            proc = psutil.Process(pid.value)
            return proc.name().lower().replace(".exe", "")
        except:
            return None

    def _get_active_linux(self) -> Optional[str]:
        try:
            from Xlib import display as xdisplay, X
            d      = xdisplay.Display()
            window = d.get_input_focus().focus
            pid    = window.get_full_property(
                d.intern_atom("_NET_WM_PID"), X.AnyPropertyType
            )
            if pid:
                proc = psutil.Process(pid.value[0])
                return proc.name().lower()
        except Exception:
            pass
        # Fallback: check running processes
        for proc in psutil.process_iter(["name", "status"]):
            if proc.info["status"] == "running":
                return proc.info["name"].lower()
        return None

    def _get_active_macos(self) -> Optional[str]:
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get name of first process whose frontmost is true'],
                capture_output=True, text=True
            )
            return result.stdout.strip().lower() if result.returncode == 0 else None
        except:
            return None

    def _classify_task(self, app_name: Optional[str]) -> Optional[str]:
        if not app_name:
            return None
        app_lower = app_name.lower()
        for key, task in APP_TASK_MAP.items():
            if key in app_lower:
                return task
        return "unknown"

    def get_snapshot(self) -> dict:
        return {
            "active_app":   self._state.get("active_app"),
            "active_window": self._state.get("active_window"),
            "active_task":  self._state.get("active_task"),
            "duration_min": self._state.get("current_task_duration_min", 0),
        }

    def stop(self):
        self._running = False
