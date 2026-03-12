from __future__ import annotations

from pathlib import Path

from app.agent.history import IncidentHistoryStore
from app.agent.models import Anomaly, IncidentHistoryEntry
from app.agent.reasoner import Reasoner


def _disk_anomaly() -> Anomaly:
    return Anomaly(
        signal="disk_usage",
        value=93.7,
        threshold=90.0,
        severity="high",
        summary="disk_usage is 93.7% (> 90.0%)",
    )


def test_reasoner_uses_history_for_confidence_and_root_cause() -> None:
    reasoner = Reasoner(context_window_size=5)
    anomalies = [_disk_anomaly()]
    evidence = ["kernel ERROR No space left on device"]

    baseline = reasoner.diagnose(
        incident="Disk usage > 90%",
        anomalies=anomalies,
        evidence=evidence,
        history_context=[],
    )

    history = [
        IncidentHistoryEntry(
            timestamp="2026-03-10T00:00:00+00:00",
            incident="Disk usage > 90%",
            anomaly_signals=["disk_usage"],
            root_cause="Disk usage exceeded threshold due to runaway log growth.",
            confidence=0.86,
        ),
        IncidentHistoryEntry(
            timestamp="2026-03-11T00:00:00+00:00",
            incident="Disk usage > 90%",
            anomaly_signals=["disk_usage"],
            root_cause="Disk usage exceeded threshold due to runaway log growth.",
            confidence=0.88,
        ),
    ]

    with_history = reasoner.diagnose(
        incident="Disk usage > 90%",
        anomalies=anomalies,
        evidence=evidence,
        history_context=history,
    )

    assert with_history.confidence >= baseline.confidence
    assert "Similar to recent incidents" in with_history.root_cause
    assert any("History context:" in line for line in with_history.evidence)


def test_reasoner_applies_context_window_limit() -> None:
    reasoner = Reasoner(context_window_size=2)
    anomalies = [_disk_anomaly()]
    history = [
        IncidentHistoryEntry(
            timestamp=f"2026-03-1{i}T00:00:00+00:00",
            incident="Disk usage > 90%",
            anomaly_signals=["disk_usage"],
            root_cause="Disk usage exceeded threshold due to runaway log growth.",
            confidence=0.8,
        )
        for i in range(0, 4)
    ]

    diagnosis = reasoner.diagnose(
        incident="Disk usage > 90%",
        anomalies=anomalies,
        evidence=["No space left on device"],
        history_context=history,
    )
    assert any("2 related incidents" in line for line in diagnosis.evidence)


def test_incident_history_store_append_and_load(tmp_path: Path) -> None:
    history_path = tmp_path / "incident_history.jsonl"
    store = IncidentHistoryStore(str(history_path), max_items=10)
    store.append(
        incident="Disk usage > 90%",
        anomaly_signals=["disk_usage"],
        root_cause="Disk usage exceeded threshold due to runaway log growth.",
        confidence=0.9,
    )
    store.append(
        incident="Server CPU spike",
        anomaly_signals=["cpu_usage"],
        root_cause="CPU spike likely caused by burst traffic and worker saturation.",
        confidence=0.83,
    )

    loaded = store.load_recent(limit=5)
    assert len(loaded) == 2
    assert loaded[-1].incident == "Server CPU spike"
