from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from app.agent.models import Anomaly


class LogService:
    def __init__(
        self,
        sample_logs_path: str,
        source: str = "sample",
        loki_url: str | None = None,
        loki_query: str = '{job="varlogs"}',
        timeout_seconds: float = 5.0,
    ) -> None:
        self.sample_logs_path = Path(sample_logs_path)
        self.source = source.lower().strip()
        self.loki_url = loki_url.rstrip("/") if loki_url else None
        self.loki_query = loki_query
        self.timeout_seconds = timeout_seconds

    def read_logs(self, limit: int = 120) -> list[str]:
        if self.source == "loki":
            lines = self._read_logs_from_loki(limit=limit)
            if lines:
                return lines[-limit:]
        return self._read_logs_from_sample(limit=limit)

    def _read_logs_from_sample(self, limit: int = 120) -> list[str]:
        with self.sample_logs_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines[-limit:]

    def _read_logs_from_loki(self, limit: int = 120) -> list[str]:
        if not self.loki_url:
            return []

        endpoint = f"{self.loki_url}/loki/api/v1/query_range"
        end_dt = datetime.now(tz=UTC)
        start_dt = end_dt - timedelta(hours=1)
        params = {
            "query": self.loki_query,
            "limit": str(limit),
            "direction": "backward",
            "start": str(int(start_dt.timestamp() * 1_000_000_000)),
            "end": str(int(end_dt.timestamp() * 1_000_000_000)),
        }

        try:
            response = httpx.get(endpoint, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "success":
                return []

            streams = payload.get("data", {}).get("result", [])
            logs: list[str] = []
            for stream in streams:
                values = stream.get("values", [])
                for value in values:
                    if len(value) < 2:
                        continue
                    line = value[1].strip()
                    if line:
                        logs.append(line)
            logs.reverse()
            return logs
        except Exception:
            return []

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
