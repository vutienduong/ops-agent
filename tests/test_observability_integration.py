from __future__ import annotations

import json
from pathlib import Path

from app.agent.logs import LogService
from app.agent.monitoring import MonitoringService


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self) -> dict:
        return self._payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_monitoring_service_fetch_from_prometheus(monkeypatch, tmp_path: Path) -> None:
    sample_path = tmp_path / "sample_metrics.json"
    _write_json(sample_path, {"cpu_usage": 10, "disk_usage": 10})

    def fake_get(url: str, params: dict, timeout: float) -> DummyResponse:
        query = params["query"]
        values = {
            "cpu_query": "91.2",
            "disk_query": "94.4",
        }
        return DummyResponse(
            {
                "status": "success",
                "data": {"result": [{"value": [1710000000, values.get(query, "0.0")]}]},
            }
        )

    monkeypatch.setattr("app.agent.monitoring.httpx.get", fake_get)

    service = MonitoringService(
        sample_metrics_path=str(sample_path),
        source="prometheus",
        prometheus_url="http://prometheus.local",
        prometheus_queries={"cpu_usage": "cpu_query", "disk_usage": "disk_query"},
    )
    metrics = service.fetch_metrics()
    assert metrics["cpu_usage"] == 91.2
    assert metrics["disk_usage"] == 94.4


def test_monitoring_service_fallback_to_sample(monkeypatch, tmp_path: Path) -> None:
    sample_path = tmp_path / "sample_metrics.json"
    _write_json(sample_path, {"cpu_usage": 50.0, "disk_usage": 55.0})

    def fake_get(url: str, params: dict, timeout: float) -> DummyResponse:
        raise RuntimeError("prometheus down")

    monkeypatch.setattr("app.agent.monitoring.httpx.get", fake_get)

    service = MonitoringService(
        sample_metrics_path=str(sample_path),
        source="prometheus",
        prometheus_url="http://prometheus.local",
        prometheus_queries={"cpu_usage": "cpu_query"},
    )
    assert service.fetch_metrics() == {"cpu_usage": 50.0, "disk_usage": 55.0}


def test_log_service_fetch_from_loki(monkeypatch, tmp_path: Path) -> None:
    sample_path = tmp_path / "sample_logs.txt"
    sample_path.write_text("fallback line\n", encoding="utf-8")

    def fake_get(url: str, params: dict, timeout: float) -> DummyResponse:
        return DummyResponse(
            {
                "status": "success",
                "data": {
                    "result": [
                        {
                            "stream": {"app": "ops"},
                            "values": [
                                ["1710000001000000000", "newest log line"],
                                ["1710000000000000000", "older log line"],
                            ],
                        }
                    ]
                },
            }
        )

    monkeypatch.setattr("app.agent.logs.httpx.get", fake_get)

    service = LogService(
        sample_logs_path=str(sample_path),
        source="loki",
        loki_url="http://loki.local",
        loki_query='{app="ops"}',
    )
    logs = service.read_logs(limit=10)
    assert logs == ["older log line", "newest log line"]


def test_log_service_fallback_to_sample(monkeypatch, tmp_path: Path) -> None:
    sample_path = tmp_path / "sample_logs.txt"
    sample_path.write_text("line one\nline two\n", encoding="utf-8")

    def fake_get(url: str, params: dict, timeout: float) -> DummyResponse:
        raise RuntimeError("loki down")

    monkeypatch.setattr("app.agent.logs.httpx.get", fake_get)

    service = LogService(
        sample_logs_path=str(sample_path),
        source="loki",
        loki_url="http://loki.local",
    )
    assert service.read_logs(limit=10) == ["line one", "line two"]
