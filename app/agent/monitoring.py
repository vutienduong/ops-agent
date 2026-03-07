from __future__ import annotations

import json
from pathlib import Path

from app.agent.models import Anomaly


THRESHOLDS: dict[str, float] = {
    "cpu_usage": 85.0,
    "memory_usage": 90.0,
    "disk_usage": 90.0,
}


class MonitoringService:
    def __init__(self, sample_metrics_path: str) -> None:
        self.sample_metrics_path = Path(sample_metrics_path)

    def fetch_metrics(self) -> dict[str, float]:
        with self.sample_metrics_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return {k: float(v) for k, v in payload.items()}

    def detect_anomalies(self, metrics: dict[str, float]) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for signal, threshold in THRESHOLDS.items():
            value = metrics.get(signal)
            if value is None:
                continue
            if value > threshold:
                severity = "high" if value < threshold + 10 else "critical"
                anomalies.append(
                    Anomaly(
                        signal=signal,
                        value=value,
                        threshold=threshold,
                        severity=severity,
                        summary=f"{signal} is {value:.1f}% (> {threshold:.1f}%)",
                    )
                )
        return anomalies
