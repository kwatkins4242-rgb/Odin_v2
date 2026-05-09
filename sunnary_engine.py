"""
ODIN Layer 4 – Daily Summaries
"""
import json, logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

SUMMARY_FILE = Path(__file__).parent / "summaries.json"

class SummaryEngine:
    def __init__(self) -> None:
        self.file = SUMMARY_FILE
        self._ensure()

    def _ensure(self) -> None:
        if not self.file.exists():
            self.file.write_text(json.dumps({"summaries": []}))

    def add_summary(self, summary: Dict[str, Any]) -> None:
        data = json.loads(self.file.read_text(encoding="utf-8"))
        data["summaries"].append({**summary, "created": datetime.now().isoformat()})
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.file)

    def get_recent_summaries(self, days=7) -> List[Dict[str, Any]]:
        data = json.loads(self.file.read_text(encoding="utf-8"))
        cutoff = datetime.now() - timedelta(days=days)
        return [s for s in data["summaries"]
                if datetime.fromisoformat(s["created"]) > cutoff]

