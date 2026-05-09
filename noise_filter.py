"""
ODIN-SENSE — Noise Filter
Cleans audio before passing to Whisper.
Reduces background noise (fans, TV, keyboard, street).
Uses scipy signal processing — no ML, runs fast on CPU.
"""

import numpy as np
from scipy import signal
from typing import Optional

SAMPLE_RATE = 16000


class NoiseFilter:

    def __init__(self):
        self._noise_profile: Optional[np.ndarray] = None

    def filter(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction pipeline:
          1. High-pass filter (removes low-frequency rumble)
          2. Spectral subtraction (if noise profile available)
          3. Normalize amplitude
        """
        if audio is None or len(audio) == 0:
            return audio

        audio = self._highpass_filter(audio)
        audio = self._lowpass_filter(audio)

        if self._noise_profile is not None:
            audio = self._spectral_subtract(audio)

        audio = self._normalize(audio)
        return audio

    def calibrate_noise(self, ambient_audio: np.ndarray):
        """
        Record ambient noise baseline (2-3 seconds of background).
        Call this on startup or when environment changes significantly.
        ODIN can do this silently while it's idle.
        """
        if ambient_audio is None or len(ambient_audio) < SAMPLE_RATE:
            return
        self._noise_profile = self._get_magnitude_spectrum(ambient_audio)
        print("[NoiseFilter] Noise profile calibrated")

    def _highpass_filter(self, audio: np.ndarray, cutoff_hz: int = 80) -> np.ndarray:
        """Remove low-frequency rumble (AC, fan noise below 80Hz)."""
        nyq  = SAMPLE_RATE / 2
        norm = cutoff_hz / nyq
        b, a = signal.butter(4, norm, btype='high')
        return signal.filtfilt(b, a, audio).astype(np.float32)

    def _lowpass_filter(self, audio: np.ndarray, cutoff_hz: int = 7500) -> np.ndarray:
        """Remove ultrasonic frequencies above speech range."""
        nyq  = SAMPLE_RATE / 2
        norm = cutoff_hz / nyq
        b, a = signal.butter(4, norm, btype='low')
        return signal.filtfilt(b, a, audio).astype(np.float32)

    def _spectral_subtract(self, audio: np.ndarray, alpha: float = 2.0) -> np.ndarray:
        """
        Spectral subtraction noise reduction.
        Subtracts estimated noise spectrum from signal spectrum.
        """
        try:
            n_fft   = 512
            hop     = n_fft // 4
            frames  = self._frame_audio(audio, n_fft, hop)
            result  = np.zeros_like(audio)

            noise = self._noise_profile[:n_fft // 2 + 1]
            noise_pad = np.zeros(n_fft // 2 + 1)
            noise_pad[:len(noise)] = noise[:len(noise_pad)]

            clean_frames = []
            for frame in frames:
                windowed  = frame * np.hanning(len(frame))
                spectrum  = np.fft.rfft(windowed, n=n_fft)
                magnitude = np.abs(spectrum)
                phase     = np.angle(spectrum)

                # Subtract noise
                clean_mag = magnitude - alpha * noise_pad
                clean_mag = np.maximum(clean_mag, 0.01 * magnitude)  # Spectral floor

                clean_spectrum = clean_mag * np.exp(1j * phase)
                clean_frame    = np.fft.irfft(clean_spectrum)[:len(frame)]
                clean_frames.append(clean_frame)

            # Overlap-add reconstruction
            for i, frame in enumerate(clean_frames):
                start = i * hop
                end   = start + len(frame)
                if end <= len(result):
                    result[start:end] += frame

            return result.astype(np.float32)

        except Exception:
            return audio  # Return unmodified if spectral subtraction fails

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to -1..1 range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio

    def _get_magnitude_spectrum(self, audio: np.ndarray) -> np.ndarray:
        """Get average magnitude spectrum of audio (for noise profiling)."""
        n_fft     = 512
        hop       = n_fft // 4
        frames    = self._frame_audio(audio, n_fft, hop)
        spectra   = []
        for frame in frames:
            windowed = frame * np.hanning(len(frame))
            spectrum = np.abs(np.fft.rfft(windowed, n=n_fft))
            spectra.append(spectrum)
        if not spectra:
            return np.zeros(n_fft // 2 + 1)
        return np.mean(spectra, axis=0)

    def _frame_audio(self, audio: np.ndarray, n_fft: int, hop: int) -> list:
        """Split audio into overlapping frames."""
        frames = []
        for start in range(0, len(audio) - n_fft, hop):
            frames.append(audio[start:start + n_fft].copy())
        return frames

    def get_rms(self, audio: np.ndarray) -> float:
        """Get RMS level of audio (0.0-1.0). Used for noise level monitoring."""
        if audio is None or len(audio) == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio ** 2)))
