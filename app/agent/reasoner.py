from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.agent.models import Anomaly, Diagnosis, IncidentHistoryEntry


class Reasoner:
    def __init__(
        self,
        openai_api_key: str | None = None,
        model: str = "gpt-4o-mini",
        context_window_size: int = 5,
    ) -> None:
        self.model = model
        self.client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.context_window_size = max(context_window_size, 1)

    def diagnose(
        self,
        incident: str | None,
        anomalies: list[Anomaly],
        evidence: list[str],
        history_context: list[IncidentHistoryEntry | dict[str, Any]] | None = None,
    ) -> Diagnosis:
        history_entries = self._normalize_history_entries(history_context or [])
        context_window = self._build_context_window(anomalies=anomalies, history_entries=history_entries)
        fallback = self._heuristic_diagnosis(
            incident=incident,
            anomalies=anomalies,
            evidence=evidence,
            context_window=context_window,
        )
        if not self.client:
            return fallback

        prompt = {
            "incident": incident,
            "anomalies": [a.model_dump() for a in anomalies],
            "evidence": evidence,
            "history_context": [entry.model_dump() for entry in context_window],
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
            parsed_evidence = parsed.get("evidence", [])
            if not isinstance(parsed_evidence, list):
                parsed_evidence = [str(parsed_evidence)]

            calibrated = self._calibrate_confidence(
                base_confidence=float(parsed["confidence"]),
                anomalies=anomalies,
                evidence=parsed_evidence,
                context_window=context_window,
            )
            final_evidence = parsed_evidence[:8] + self._build_history_evidence(context_window)
            return Diagnosis(
                root_cause=parsed["root_cause"],
                confidence=calibrated,
                evidence=final_evidence[:8],
            )
        except Exception:
            return fallback

    def _heuristic_diagnosis(
        self,
        incident: str | None,
        anomalies: list[Anomaly],
        evidence: list[str],
        context_window: list[IncidentHistoryEntry],
    ) -> Diagnosis:
        normalized = " ".join(evidence).lower()
        incident_text = (incident or "").lower()

        has_disk = any("disk" in a.signal for a in anomalies) or "disk" in incident_text
        has_cpu = any("cpu" in a.signal for a in anomalies) or "cpu" in incident_text
        has_memory = any("memory" in a.signal for a in anomalies) or "memory" in incident_text

        if has_disk and ("no space left" in normalized or "log" in normalized):
            root_cause = "Disk usage exceeded threshold due to runaway log growth."
            base_confidence = 0.78
        elif has_disk:
            root_cause = "Disk usage exceeded threshold, likely from large transient files."
            base_confidence = 0.67
        elif has_cpu and ("throttle" in normalized or "spike" in normalized):
            root_cause = "CPU spike likely caused by burst traffic and worker saturation."
            base_confidence = 0.71
        elif has_cpu:
            root_cause = "CPU utilization is high, likely from overloaded application workers."
            base_confidence = 0.62
        elif has_memory and ("oom" in normalized or "swap" in normalized):
            root_cause = "Memory pressure likely caused by allocation spikes or memory leak."
            base_confidence = 0.68
        elif has_memory:
            root_cause = "Memory usage is high and requires deeper process-level profiling."
            base_confidence = 0.58
        else:
            root_cause = "Anomaly detected with insufficient context; collect more diagnostic logs."
            base_confidence = 0.45

        repeated_root_cause = self._get_repeated_root_cause(context_window)
        if repeated_root_cause:
            root_cause = f"{root_cause} Similar to recent incidents: {repeated_root_cause}"

        confidence = self._calibrate_confidence(
            base_confidence=base_confidence,
            anomalies=anomalies,
            evidence=evidence,
            context_window=context_window,
        )
        final_evidence = evidence[:8] + self._build_history_evidence(context_window)
        return Diagnosis(root_cause=root_cause, confidence=confidence, evidence=final_evidence[:8])

    def _normalize_history_entries(
        self, history_entries: list[IncidentHistoryEntry | dict[str, Any]]
    ) -> list[IncidentHistoryEntry]:
        normalized: list[IncidentHistoryEntry] = []
        for entry in history_entries:
            if isinstance(entry, IncidentHistoryEntry):
                normalized.append(entry)
                continue
            try:
                normalized.append(IncidentHistoryEntry(**entry))
            except Exception:
                continue
        return normalized

    def _build_context_window(
        self,
        anomalies: list[Anomaly],
        history_entries: list[IncidentHistoryEntry],
    ) -> list[IncidentHistoryEntry]:
        if not history_entries:
            return []
        signals = {anomaly.signal for anomaly in anomalies}
        if not signals:
            return history_entries[-self.context_window_size :]
        filtered = [entry for entry in history_entries if signals.intersection(set(entry.anomaly_signals))]
        return filtered[-self.context_window_size :]

    def _get_repeated_root_cause(self, context_window: list[IncidentHistoryEntry]) -> str | None:
        if not context_window:
            return None
        counts: dict[str, int] = {}
        for entry in context_window:
            counts[entry.root_cause] = counts.get(entry.root_cause, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        if not ranked or ranked[0][1] < 2:
            return None
        return ranked[0][0]

    def _build_history_evidence(self, context_window: list[IncidentHistoryEntry]) -> list[str]:
        if not context_window:
            return []
        return [f"History context: {len(context_window)} related incidents were used for RCA."]

    def _calibrate_confidence(
        self,
        base_confidence: float,
        anomalies: list[Anomaly],
        evidence: list[str],
        context_window: list[IncidentHistoryEntry],
    ) -> float:
        score = base_confidence
        evidence_bonus = min(0.12, 0.02 * len(evidence))
        anomaly_bonus = min(0.08, 0.03 * len(anomalies))
        history_bonus = min(0.10, 0.04 * len(context_window))
        no_evidence_penalty = 0.12 if not evidence else 0.0
        calibrated = score + evidence_bonus + anomaly_bonus + history_bonus - no_evidence_penalty
        calibrated = max(0.30, min(0.97, calibrated))
        return round(calibrated, 2)
