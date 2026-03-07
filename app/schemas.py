from __future__ import annotations

from pydantic import BaseModel, Field


class RunAgentRequest(BaseModel):
    incident: str | None = Field(default=None, description="Incident hint, e.g. 'Disk usage > 90%'")
    metrics: dict[str, float] | None = Field(default=None, description="Optional metrics override")
    logs: list[str] | None = Field(default=None, description="Optional logs override")
