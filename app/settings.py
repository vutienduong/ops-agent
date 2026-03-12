from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    sample_metrics_path: str = "app/data/sample_metrics.json"
    sample_logs_path: str = "app/data/sample_logs.txt"
    metrics_source: str = "sample"
    logs_source: str = "sample"
    prometheus_url: str | None = None
    loki_url: str | None = None
    loki_query: str = '{job="varlogs"}'


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        sample_metrics_path=os.getenv("SAMPLE_METRICS_PATH", "app/data/sample_metrics.json"),
        sample_logs_path=os.getenv("SAMPLE_LOGS_PATH", "app/data/sample_logs.txt"),
        metrics_source=os.getenv("METRICS_SOURCE", "sample"),
        logs_source=os.getenv("LOGS_SOURCE", "sample"),
        prometheus_url=os.getenv("PROMETHEUS_URL"),
        loki_url=os.getenv("LOKI_URL"),
        loki_query=os.getenv("LOKI_QUERY", '{job="varlogs"}'),
    )
