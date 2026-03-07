from __future__ import annotations

from pydantic import BaseModel, Field


class Anomaly(BaseModel):
    signal: str
    value: float
    threshold: float
    severity: str
    summary: str


class Diagnosis(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]


class PlanStep(BaseModel):
    id: str
    description: str
    tool: str
    command: str | None = None


class ExecutionRecord(BaseModel):
    step_id: str
    status: str
    command: str | None = None
    output: str


class Verification(BaseModel):
    resolved: bool
    summary: str
    checks: dict[str, str]
