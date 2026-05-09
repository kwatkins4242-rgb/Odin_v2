"""
ODIN-SENSE — Voice Identifier
Recognizes WHO is speaking by their voice embedding (voice print).
Uses Resemblyzer to create 256-dim speaker embeddings.
No training needed — just provide a 5-10 second audio sample per person.

Voice profiles stored in voice_profiles/ as .npy files.
ODIN knows Charles's voice by default — add others as needed.
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional

PROFILES_DIR = Path(__file__).parent / "voice_profiles"
PROFILES_DIR.mkdir(exist_ok=True)

MATCH_THRESHOLD = float(os.getenv("VOICE_MATCH_THRESHOLD", "0.75"))  # Cosine similarity


class VoiceIdentifier:

    def __init__(self):
        self._encoder  = None
        self._profiles = {}
        self._load_encoder()
        self._load_profiles()

    def _load_encoder(self):
        try:
            from resemblyzer import VoiceEncoder
            self._encoder = VoiceEncoder()
            print("[VoiceID] Resemblyzer encoder loaded")
        except ImportError:
            print("[VoiceID] resemblyzer not installed — voice ID disabled")
        except Exception as e:
            print(f"[VoiceID] Failed to load encoder: {e}")

    def _load_profiles(self):
        """Load all saved voice profiles from disk."""
        for npy_file in PROFILES_DIR.glob("*.npy"):
            name = npy_file.stem
            embedding = np.load(npy_file)
            self._profiles[name] = embedding
        print(f"[VoiceID] Loaded {len(self._profiles)} voice profiles: {list(self._profiles.keys())}")

    def identify(self, audio: np.ndarray) -> Optional[str]:
        """
        Identify who is speaking.
        Returns name string (e.g. "charles") or None if no match above threshold.
        """
        if not self._encoder or not self._profiles:
            return None

        embedding = self._get_embedding(audio)
        if embedding is None:
            return None

        best_name  = None
        best_score = 0.0

        for name, profile_emb in self._profiles.items():
            score = self._cosine_similarity(embedding, profile_emb)
            if score > best_score:
                best_score = score
                best_name  = name

        if best_score >= MATCH_THRESHOLD:
            return best_name
        return None  # Unknown speaker

    def enroll(self, name: str, audio: np.ndarray) -> bool:
        """
        Enroll a new speaker by name from a 5-30s audio sample.
        Saves embedding to disk. Call this once per person.

        Usage:
            voice_id.enroll("charles", audio_array)
        """
        if not self._encoder:
            return False

        embedding = self._get_embedding(audio)
        if embedding is None:
            return False

        # If profile already exists, average with new sample for robustness
        if name in self._profiles:
            old = self._profiles[name]
            embedding = (old + embedding) / 2
            embedding = embedding / np.linalg.norm(embedding)  # Re-normalize

        self._profiles[name] = embedding
        np.save(PROFILES_DIR / f"{name}.npy", embedding)
        print(f"[VoiceID] Enrolled/updated: '{name}'")
        return True

    def delete_profile(self, name: str) -> bool:
        path = PROFILES_DIR / f"{name}.npy"
        if name in self._profiles:
            del self._profiles[name]
        if path.exists():
            path.unlink()
            return True
        return False

    def list_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def _get_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        """Get 256-dim voice embedding from audio array."""
        try:
            from resemblyzer import preprocess_wav
            # Resemblyzer expects a specific preprocessing
            processed  = preprocess_wav(audio, source_sr=16000)
            embedding  = self._encoder.embed_utterance(processed)
            return embedding
        except Exception as e:
            print(f"[VoiceID] Embedding error: {e}")
            return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two embeddings (0-1)."""
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
