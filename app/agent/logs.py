from __future__ import annotations

from pathlib import Path

from app.agent.models import Anomaly


class LogService:
    def __init__(self, sample_logs_path: str) -> None:
        self.sample_logs_path = Path(sample_logs_path)

    def read_logs(self, limit: int = 120) -> list[str]:
        with self.sample_logs_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines[-limit:]

    def select_evidence(self, anomalies: list[Anomaly], logs: list[str], limit: int = 8) -> list[str]:
        if not anomalies:
            return logs[-limit:]

        keywords: set[str] = set()
        for anomaly in anomalies:
            if "disk" in anomaly.signal:
                keywords.update({"disk", "space", "inode", "No space left"})
            if "cpu" in anomaly.signal:
                keywords.update({"cpu", "throttle", "load", "spike"})
            if "memory" in anomaly.signal:
                keywords.update({"oom", "memory", "swap"})

        evidence: list[str] = []
        for line in logs:
            low = line.lower()
            if any(kw.lower() in low for kw in keywords):
                evidence.append(line)
        return evidence[-limit:] if evidence else logs[-limit:]
