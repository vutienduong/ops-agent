from __future__ import annotations

from app.agent.models import Anomaly, Verification


class VerifierAgent:
    def verify(self, anomalies: list[Anomaly], post_metrics: dict[str, float]) -> Verification:
        if not anomalies:
            return Verification(
                resolved=True,
                summary="No anomaly detected in monitor stage.",
                checks={"overall": "healthy"},
            )

        checks: dict[str, str] = {}
        resolved = True
        for anomaly in anomalies:
            latest = post_metrics.get(anomaly.signal, anomaly.value)
            ok = latest <= anomaly.threshold
            checks[anomaly.signal] = (
                f"OK ({latest:.1f}% <= {anomaly.threshold:.1f}%)"
                if ok
                else f"NOT_OK ({latest:.1f}% > {anomaly.threshold:.1f}%)"
            )
            resolved = resolved and ok

        summary = "Incident resolved and metrics back to threshold." if resolved else "Incident still active."
        return Verification(resolved=resolved, summary=summary, checks=checks)
