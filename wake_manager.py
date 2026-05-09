"""
ODIN-SENSE — Wake Manager
Manages hundreds of wake word .ppn files.
Porcupine has a max of ~20 keywords per instance, so WakeManager
rotates through batches to cover all variants without crashing.

Also supports text-based triggers for simulation/fallback.
"""

import os
from pathlib import Path
from typing import Tuple

CUSTOM_WORDS_DIR = Path(__file__).parent / "custom_words"

# Porcupine max keywords per instance
BATCH_SIZE = 16

# Built-in Porcupine keywords (no .ppn file needed, works on free tier)
BUILTIN_TRIGGERS = [
    "hey siri",     # repurpose as fallback
    "alexa",        # we won't use these but they ship with Porcupine
    "computer",     # star trek mode 😄
]

# Text-based fallback trigger words (for simulation mode / STT path)
TEXT_TRIGGERS = [
    "hey odin", "yo odin", "odin", "hey o", "odin you there",
    "wake up odin", "odin wake up", "odin listen", "listen odin",
    "odin help", "help odin", "odin come in", "odin you copy",
    "alright odin", "okay odin", "aye odin", "odin check in",
    "odin i need you", "what up odin", "odin what's up",
]

SENSITIVITY_DEFAULT = float(os.getenv("WAKE_SENSITIVITY", "0.6"))
SENSITIVITY_HIGH    = 0.8
SENSITIVITY_LOW     = 0.4


class WakeManager:

    def __init__(self):
        CUSTOM_WORDS_DIR.mkdir(exist_ok=True)
        self._batch_index = 0
        self._all_ppn     = self._scan_ppn_files()
        print(f"[WakeManager] Found {len(self._all_ppn)} .ppn wake word files")

    def _scan_ppn_files(self) -> list[Path]:
        """Scan the custom_words folder for all .ppn files."""
        return sorted(CUSTOM_WORDS_DIR.glob("*.ppn"))

    def get_active_batch(self) -> Tuple[list[str], list[str], list[float]]:
        """
        Returns (keyword_paths, keyword_names, sensitivities) for the current batch.
        Rotates to the next batch on each call so all variants get coverage over time.
        """
        if not self._all_ppn:
            return [], [], []

        # Refresh scan in case new .ppn files were dropped in
        self._all_ppn = self._scan_ppn_files()

        total   = len(self._all_ppn)
        start   = (self._batch_index * BATCH_SIZE) % total
        end     = min(start + BATCH_SIZE, total)
        batch   = self._all_ppn[start:end]

        # Wrap around if needed
        if len(batch) < BATCH_SIZE and total > BATCH_SIZE:
            batch += self._all_ppn[:BATCH_SIZE - len(batch)]

        self._batch_index = (self._batch_index + 1) % max(1, total // BATCH_SIZE)

        keyword_paths   = [str(p) for p in batch]
        keyword_names   = [p.stem for p in batch]
        sensitivities   = [self._get_sensitivity(name) for name in keyword_names]

        return keyword_paths, keyword_names, sensitivities

    def _get_sensitivity(self, keyword_name: str) -> float:
        """
        Higher sensitivity for shorter/simpler triggers (more false positives OK).
        Lower sensitivity for long phrases (want precision).
        """
        name = keyword_name.lower()
        if len(name.replace("-", "").replace("_", "")) <= 6:
            return SENSITIVITY_HIGH
        if len(name) > 20:
            return SENSITIVITY_LOW
        return SENSITIVITY_DEFAULT

    def count(self) -> int:
        return len(self._all_ppn)

    def is_text_trigger(self, text: str) -> bool:
        """
        Check if a transcribed utterance starts with a known text trigger.
        Used as fallback when wake word hardware detection isn't available.
        """
        text_lower = text.lower().strip()
        for trigger in TEXT_TRIGGERS:
            if text_lower.startswith(trigger):
                return True
        return False

    def get_text_triggers(self) -> list[str]:
        return TEXT_TRIGGERS.copy()

    def add_ppn_file(self, ppn_path: str) -> bool:
        """Copy a new .ppn file into the custom_words folder."""
        import shutil
        src = Path(ppn_path)
        if not src.exists():
            return False
        dest = CUSTOM_WORDS_DIR / src.name
        shutil.copy2(src, dest)
        self._all_ppn = self._scan_ppn_files()
        return True

    def list_all_triggers(self) -> dict:
        return {
            "ppn_files":     [p.stem for p in self._all_ppn],
            "text_triggers": TEXT_TRIGGERS,
            "batch_size":    BATCH_SIZE,
            "total_ppn":     len(self._all_ppn)
        }
