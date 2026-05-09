"""
ODIN-SENSE — Sound Classifier
Identifies ambient sounds in the environment.
Lightweight approach using RMS + spectral features — no heavy ML model.
Classifies: speech, music, keyboard, silence, background_noise, alarm.

Helps ODIN decide:
  - Is Charles actively talking (speech detected)?
  - Is music playing (don't interrupt)?
  - Is there keyboard activity (he's working)?
  - Is it silent (is he away or asleep)?
"""

import numpy as np
import time
from collections import deque
from typing import Optional


class SoundClassifier:

    # RMS thresholds
    SILENCE_THRESH   = 0.01
    SPEECH_THRESH    = 0.05
    LOUD_THRESH      = 0.3

    def __init__(self):
        self._recent_classifications = deque(maxlen=10)

    def classify(self, audio: np.ndarray, sample_rate: int = 16000) -> dict:
        """
        Classify a chunk of audio.
        Returns {label, confidence, rms, is_speech}
        """
        if audio is None or len(audio) == 0:
            return self._result("silence", 1.0, 0.0)

        rms         = float(np.sqrt(np.mean(audio ** 2)))
        spectral    = self._get_spectral_features(audio, sample_rate)
        label, conf = self._classify_features(rms, spectral)

        result = self._result(label, conf, rms)
        self._recent_classifications.append(result)
        return result

    def _classify_features(self, rms: float, spectral: dict) -> tuple[str, float]:
        """Rule-based classification using RMS + spectral features."""

        # Silence
        if rms < self.SILENCE_THRESH:
            return "silence", 0.95

        centroid    = spectral.get("centroid", 0)
        rolloff     = spectral.get("rolloff", 0)
        flatness    = spectral.get("flatness", 0)
        zero_cross  = spectral.get("zero_crossing_rate", 0)

        # Speech detection: mid-range centroid, moderate zero-crossing
        if 300 < centroid < 3500 and 0.01 < zero_cross < 0.15:
            if rms >= self.SPEECH_THRESH:
                conf = min(1.0, rms / self.LOUD_THRESH + 0.5)
                return "speech", round(conf, 3)

        # Music: high spectral flatness, broad frequency distribution
        if flatness > 0.1 and rolloff > 4000 and rms > self.SILENCE_THRESH:
            return "music", 0.7

        # Keyboard: very short transients, low RMS
        if rms < 0.1 and zero_cross > 0.2:
            return "keyboard", 0.6

        # Generic background noise
        if rms >= self.SILENCE_THRESH:
            return "background_noise", 0.5

        return "silence", 0.8

    def _get_spectral_features(self, audio: np.ndarray, sample_rate: int) -> dict:
        """Extract spectral features using numpy (no librosa dependency needed)."""
        try:
            n_fft    = min(512, len(audio))
            spectrum = np.abs(np.fft.rfft(audio[:n_fft]))
            freqs    = np.fft.rfftfreq(n_fft, d=1/sample_rate)

            if spectrum.sum() == 0:
                return {}

            # Spectral centroid: weighted average frequency
            centroid = float(np.sum(freqs * spectrum) / np.sum(spectrum))

            # Spectral rolloff: frequency below which 85% of energy is
            cumsum     = np.cumsum(spectrum)
            rolloff_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1])
            rolloff    = float(freqs[min(rolloff_idx, len(freqs)-1)])

            # Spectral flatness: ratio of geometric to arithmetic mean
            geo_mean  = np.exp(np.mean(np.log(spectrum + 1e-10)))
            arith_mean = np.mean(spectrum)
            flatness  = float(geo_mean / (arith_mean + 1e-10))

            # Zero crossing rate
            zero_crossings  = np.where(np.diff(np.sign(audio)))[0]
            zcr             = len(zero_crossings) / len(audio)

            return {
                "centroid":           round(centroid, 1),
                "rolloff":            round(rolloff, 1),
                "flatness":           round(flatness, 4),
                "zero_crossing_rate": round(zcr, 4)
            }
        except:
            return {}

    def _result(self, label: str, confidence: float, rms: float) -> dict:
        return {
            "label":      label,
            "confidence": confidence,
            "rms":        round(rms, 4),
            "is_speech":  label == "speech",
            "timestamp":  time.time()
        }

    def get_dominant_sound(self, window: int = 5) -> str:
        """Get the most common sound in recent history."""
        if not self._recent_classifications:
            return "silence"
        recent = list(self._recent_classifications)[-window:]
        labels = [r["label"] for r in recent]
        return max(set(labels), key=labels.count)

    def is_environment_quiet(self) -> bool:
        """True if environment is consistently quiet."""
        dominant = self.get_dominant_sound()
        return dominant in ("silence", "keyboard")
