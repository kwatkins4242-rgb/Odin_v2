"""
ODIN-SENSE — Sensitivity Tuner
Automatically adjusts wake word detection sensitivity
based on ambient noise level and recent false positive rate.

High noise (TV, music, street) → lower sensitivity (fewer false triggers)
Quiet room → higher sensitivity (catches soft speech)
"""

import time
import math
from collections import deque


class SensitivityTuner:

    # Sensitivity bounds
    MIN_SENSITIVITY = 0.3
    MAX_SENSITIVITY = 0.9
    DEFAULT         = 0.6

    # How many noise samples to average
    NOISE_WINDOW    = 30  # samples
    FALSE_POS_WINDOW = 10  # recent detections to track

    def __init__(self):
        self._noise_levels    = deque(maxlen=self.NOISE_WINDOW)
        self._detection_times = deque(maxlen=self.FALSE_POS_WINDOW)
        self._base_sensitivity = self.DEFAULT
        self._current          = self.DEFAULT

    def update_noise(self, rms_level: float):
        """
        Feed current ambient RMS noise level (0.0-1.0).
        Called by AudioManager continuously.
        """
        self._noise_levels.append(rms_level)
        self._recalculate()

    def record_detection(self, confirmed: bool):
        """
        Record a wake word detection event.
        confirmed=True if user actually spoke after (true positive)
        confirmed=False if silence followed (likely false positive)
        """
        self._detection_times.append({
            "time":      time.time(),
            "confirmed": confirmed
        })
        self._recalculate()

    def get_sensitivity(self) -> float:
        return round(self._current, 3)

    def get_sensitivity_for_batch(self, count: int) -> list[float]:
        """Return a list of sensitivity values for a batch of keywords."""
        return [self._current] * count

    def _recalculate(self):
        """
        Sensitivity = base - noise_penalty - false_positive_penalty
        """
        sensitivity = self._base_sensitivity

        # Noise penalty: louder environment = lower sensitivity
        if self._noise_levels:
            avg_noise    = sum(self._noise_levels) / len(self._noise_levels)
            noise_penalty = avg_noise * 0.3  # max -0.3 at full noise
            sensitivity  -= noise_penalty

        # False positive penalty: if we're getting too many unconfirmed hits,
        # tighten the threshold
        if len(self._detection_times) >= 3:
            recent       = list(self._detection_times)[-5:]
            false_pos    = sum(1 for d in recent if not d["confirmed"])
            fp_rate      = false_pos / len(recent)
            fp_penalty   = fp_rate * 0.2
            sensitivity -= fp_penalty

        # Clamp
        self._current = max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, sensitivity))

    def set_base(self, value: float):
        """Manually set base sensitivity (from user preference)."""
        self._base_sensitivity = max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, value))
        self._recalculate()

    def get_stats(self) -> dict:
        avg_noise = sum(self._noise_levels) / len(self._noise_levels) if self._noise_levels else 0
        recent    = list(self._detection_times)
        return {
            "current_sensitivity": self._current,
            "base_sensitivity":    self._base_sensitivity,
            "avg_noise_level":     round(avg_noise, 3),
            "recent_detections":   len(recent),
            "false_positives":     sum(1 for d in recent if not d["confirmed"])
        }