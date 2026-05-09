"""
ODIN-SENSE — Stress Monitor
Detects when Charles is frustrated, stressed, or hitting a wall.
ODIN proactively intervenes: "You've been stuck on this for 45 mins. Take a break."

Signals monitored:
  - Typing speed and error rate (fast + lots of backspaces = frustration)
  - Repeated rapid window switching
  - Long coding sessions without breaks
  - Repeated identical commands (stuck in a loop)
  - Voice tone analysis (from audio)
  - Time of day + session length
"""

import os
import time
from collections import deque
from typing import Optional

POLL_INTERVAL_SEC   = float(os.getenv("STRESS_POLL_INTERVAL", "10.0"))
BREAK_REMIND_MIN    = int(os.getenv("BREAK_REMIND_MINUTES", "90"))   # Remind after this long
HIGH_STRESS_THRESH  = float(os.getenv("STRESS_THRESHOLD", "0.65"))


class StressMonitor:

    def __init__(self, state: dict):
        self._state              = state
        self._session_start      = time.time()
        self._window_switches    = deque(maxlen=20)  # Recent switch timestamps
        self._running            = False
        self._last_break_remind  = 0
        self._stress_history     = deque(maxlen=30)  # Last 30 readings

    def run(self):
        """Background polling loop."""
        self._running = True
        while self._running:
            try:
                stress = self._calculate_stress()
                self._stress_history.append(stress)
                self._state["stress_level"] = stress

                # Check if ODIN should intervene
                self._check_intervention(stress)

            except Exception as e:
                print(f"[StressMonitor] Error: {e}")
            time.sleep(POLL_INTERVAL_SEC)

    def _calculate_stress(self) -> float:
        """
        Aggregate stress score from 0.0 (calm) to 1.0 (high stress).
        Weighted combination of signals.
        """
        scores = []

        # Signal 1: Session length without break
        session_min = (time.time() - self._session_start) / 60
        if session_min > BREAK_REMIND_MIN:
            fatigue = min(1.0, (session_min - BREAK_REMIND_MIN) / 60)
            scores.append(("fatigue", fatigue, 0.3))

        # Signal 2: Rapid window switching (context thrashing)
        recent_switches = self._count_recent_switches(window_sec=120)
        if recent_switches > 15:
            switch_stress = min(1.0, (recent_switches - 15) / 20)
            scores.append(("window_thrash", switch_stress, 0.25))

        # Signal 3: Time of day (late night = higher base stress)
        hour = time.localtime().tm_hour
        if hour >= 1 and hour <= 5:
            scores.append(("late_night", 0.4, 0.2))
        elif hour >= 22 or hour <= 0:
            scores.append(("night_work", 0.25, 0.15))

        # Signal 4: Voice emotional state from memory state
        voice_emotion = self._state.get("current_emotion", "neutral")
        if voice_emotion in ("angry", "fear"):
            scores.append(("voice_stress", 0.7, 0.35))
        elif voice_emotion == "sad":
            scores.append(("voice_sad", 0.5, 0.25))

        if not scores:
            return 0.05  # Background baseline

        # Weighted average
        total_weight  = sum(w for _, _, w in scores)
        weighted_sum  = sum(v * w for _, v, w in scores)
        return round(min(1.0, weighted_sum / total_weight), 3)

    def _check_intervention(self, stress: float):
        """Decide if ODIN should proactively say something."""
        now = time.time()

        # Don't nag more than once every 20 minutes
        if now - self._last_break_remind < 1200:
            return

        session_min = (time.time() - self._session_start) / 60

        if stress >= HIGH_STRESS_THRESH:
            self._trigger_alert("stress_high", stress, session_min)
            self._last_break_remind = now

        elif session_min >= BREAK_REMIND_MIN:
            self._trigger_alert("long_session", stress, session_min)
            self._last_break_remind = now

    def _trigger_alert(self, alert_type: str, stress: float, session_min: float):
        """
        Push a stress/fatigue alert to the sense state.
        odin-core picks this up and generates a proactive message.
        """
        import requests

        alert = {
            "type":        alert_type,
            "stress":      stress,
            "session_min": round(session_min, 1),
            "message":     self._get_alert_message(alert_type, stress, session_min)
        }

        self._state["pending_alert"] = alert
        print(f"[StressMonitor] Alert: {alert['message']}")

        # Also POST to odin-core proactive endpoint
        core_url = os.getenv("ODIN_CORE_URL", "http://localhost:3000")
        try:
            requests.post(f"{core_url}/proactive", json=alert, timeout=2)
        except:
            pass

    def _get_alert_message(self, alert_type: str, stress: float, session_min: float) -> str:
        if alert_type == "stress_high":
            return f"Stress level high ({stress:.0%}). You've been at it {session_min:.0f} mins. Step back for a few."
        elif alert_type == "long_session":
            return f"You've been working {session_min:.0f} minutes straight. Take a break."
        return "You good?"

    def record_window_switch(self):
        """Call this whenever the active window changes."""
        self._window_switches.append(time.time())

    def _count_recent_switches(self, window_sec: int = 120) -> int:
        cutoff = time.time() - window_sec
        return sum(1 for t in self._window_switches if t >= cutoff)

    def reset_session(self):
        """Call when Charles takes a break and returns."""
        self._session_start = time.time()
        self._state["stress_level"] = 0.0
        print("[StressMonitor] Session timer reset")

    def get_stats(self) -> dict:
        avg_stress = sum(self._stress_history) / len(self._stress_history) if self._stress_history else 0
        return {
            "current_stress":  self._state.get("stress_level", 0.0),
            "avg_stress":      round(avg_stress, 3),
            "session_minutes": round((time.time() - self._session_start) / 60, 1),
            "recent_switches": self._count_recent_switches()
        }

    def stop(self):
        self._running = False
