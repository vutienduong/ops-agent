from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.agent.models import Anomaly


THRESHOLDS: dict[str, float] = {
    "cpu_usage": 85.0,
    "memory_usage": 90.0,
    "disk_usage": 90.0,
}

DEFAULT_PROMETHEUS_QUERIES: dict[str, str] = {
    "cpu_usage": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    "memory_usage": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
    "disk_usage": '100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))',
}


class MonitoringService:
    def __init__(
        self,
        sample_metrics_path: str,
        source: str = "sample",
        prometheus_url: str | None = None,
        prometheus_queries: dict[str, str] | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.sample_metrics_path = Path(sample_metrics_path)
        self.source = source.lower().strip()
        self.prometheus_url = prometheus_url.rstrip("/") if prometheus_url else None
        self.prometheus_queries = prometheus_queries or dict(DEFAULT_PROMETHEUS_QUERIES)
        self.timeout_seconds = timeout_seconds

    def fetch_metrics(self) -> dict[str, float]:
        if self.source == "prometheus":
            metrics = self._fetch_metrics_from_prometheus()
            if metrics:
                return metrics
        return self._fetch_metrics_from_sample()

    def _fetch_metrics_from_sample(self) -> dict[str, float]:
        with self.sample_metrics_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return {k: float(v) for k, v in payload.items()}

    def _fetch_metrics_from_prometheus(self) -> dict[str, float]:
        if not self.prometheus_url:
            return {}

        metrics: dict[str, float] = {}
        for signal, query in self.prometheus_queries.items():
            value = self._query_prometheus(query)
            if value is not None:
                metrics[signal] = value
        return metrics

    def _query_prometheus(self, query: str) -> float | None:
        if not self.prometheus_url:
            return None
        endpoint = f"{self.prometheus_url}/api/v1/query"
        try:
            response = httpx.get(endpoint, params={"query": query}, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "success":
                return None

            results = payload.get("data", {}).get("result", [])
            if not results:
                return None

            value = results[0].get("value", [None, None])[1]
            return float(value) if value is not None else None
        except Exception:
            return None

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
