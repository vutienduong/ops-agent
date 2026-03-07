from __future__ import annotations

import json

from openai import OpenAI

from app.agent.models import Anomaly, Diagnosis


class Reasoner:
    def __init__(self, openai_api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.client = OpenAI(api_key=openai_api_key) if openai_api_key else None

    def diagnose(self, incident: str | None, anomalies: list[Anomaly], evidence: list[str]) -> Diagnosis:
        fallback = self._heuristic_diagnosis(incident=incident, anomalies=anomalies, evidence=evidence)
        if not self.client:
            return fallback

        prompt = {
            "incident": incident,
            "anomalies": [a.model_dump() for a in anomalies],
            "evidence": evidence,
            "output_format": {"root_cause": "string", "confidence": "0-1 float", "evidence": ["string"]},
        }
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": "You are an SRE diagnosing infrastructure incidents. Return strict JSON only.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                temperature=0,
            )
            text = response.output_text
            if not text:
                return fallback
            parsed = json.loads(text)
            return Diagnosis(
                root_cause=parsed["root_cause"],
                confidence=float(parsed["confidence"]),
                evidence=list(parsed["evidence"]),
            )
        except Exception:
            return fallback

    def _heuristic_diagnosis(
        self, incident: str | None, anomalies: list[Anomaly], evidence: list[str]
    ) -> Diagnosis:
        normalized = " ".join(evidence).lower()
        incident_text = (incident or "").lower()

        has_disk = any("disk" in a.signal for a in anomalies) or "disk" in incident_text
        has_cpu = any("cpu" in a.signal for a in anomalies) or "cpu" in incident_text

        if has_disk and ("no space left" in normalized or "log" in normalized):
            root_cause = "Disk usage exceeded threshold due to runaway log growth."
            confidence = 0.87
        elif has_disk:
            root_cause = "Disk usage exceeded threshold, likely from large transient files."
            confidence = 0.78
        elif has_cpu and ("throttle" in normalized or "spike" in normalized):
            root_cause = "CPU spike likely caused by burst traffic and worker saturation."
            confidence = 0.81
        elif has_cpu:
            root_cause = "CPU utilization is high, likely from overloaded application workers."
            confidence = 0.74
        else:
            root_cause = "Anomaly detected with insufficient context; collect more diagnostic logs."
            confidence = 0.55

        return Diagnosis(root_cause=root_cause, confidence=confidence, evidence=evidence[:8])
