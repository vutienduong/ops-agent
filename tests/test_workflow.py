from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_disk_usage_incident_flow() -> None:
    response = client.post("/agent/run", json={"incident": "Disk usage > 90%"})
    assert response.status_code == 200
    payload = response.json()

    anomaly_signals = {item["signal"] for item in payload["anomalies"]}
    assert "disk_usage" in anomaly_signals

    commands = [step.get("command") for step in payload["plan"] if step.get("command")]
    assert any("cleanup_disk.sh --mode cleanup" in command for command in commands)

    assert payload["verification"]["resolved"] is True
