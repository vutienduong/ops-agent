from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.agent.models import IncidentHistoryEntry


class IncidentHistoryStore:
    def __init__(self, history_path: str, max_items: int = 500) -> None:
        self.history_path = Path(history_path)
        self.max_items = max_items
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def load_recent(self, limit: int = 20) -> list[IncidentHistoryEntry]:
        if not self.history_path.exists():
            return []

        entries: list[IncidentHistoryEntry] = []
        with self.history_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    entries.append(IncidentHistoryEntry(**payload))
                except Exception:
                    continue
        return entries[-limit:]

    def append(
        self,
        incident: str | None,
        anomaly_signals: list[str],
        root_cause: str,
        confidence: float,
    ) -> IncidentHistoryEntry:
        entry = IncidentHistoryEntry(
            timestamp=datetime.now(tz=UTC).isoformat(),
            incident=incident,
            anomaly_signals=anomaly_signals,
            root_cause=root_cause,
            confidence=confidence,
        )
        with self.history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.model_dump()) + "\n")

        self._trim_if_needed()
        return entry

    def _trim_if_needed(self) -> None:
        entries = self.load_recent(limit=self.max_items + 20)
        if len(entries) <= self.max_items:
            return
        kept = entries[-self.max_items :]
        with self.history_path.open("w", encoding="utf-8") as f:
            for entry in kept:
                f.write(json.dumps(entry.model_dump()) + "\n")
