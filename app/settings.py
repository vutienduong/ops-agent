from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    sample_metrics_path: str = "app/data/sample_metrics.json"
    sample_logs_path: str = "app/data/sample_logs.txt"


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        sample_metrics_path=os.getenv("SAMPLE_METRICS_PATH", "app/data/sample_metrics.json"),
        sample_logs_path=os.getenv("SAMPLE_LOGS_PATH", "app/data/sample_logs.txt"),
    )
