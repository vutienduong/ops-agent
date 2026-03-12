from __future__ import annotations

from fastapi import FastAPI

from app.agent.executor import ExecutorAgent
from app.agent.logs import LogService
from app.agent.monitoring import MonitoringService
from app.agent.planner import PlannerAgent
from app.agent.reasoner import Reasoner
from app.agent.verifier import VerifierAgent
from app.agent.workflow import InfraOpsWorkflow
from app.schemas import RunAgentRequest
from app.settings import get_settings

settings = get_settings()
workflow = InfraOpsWorkflow(
    monitoring=MonitoringService(
        sample_metrics_path=settings.sample_metrics_path,
        source=settings.metrics_source,
        prometheus_url=settings.prometheus_url,
    ),
    logs=LogService(
        sample_logs_path=settings.sample_logs_path,
        source=settings.logs_source,
        loki_url=settings.loki_url,
        loki_query=settings.loki_query,
    ),
    reasoner=Reasoner(openai_api_key=settings.openai_api_key, model=settings.openai_model),
    planner=PlannerAgent(),
    executor=ExecutorAgent(),
    verifier=VerifierAgent(),
)

app = FastAPI(
    title="Ops Agent Lab",
    description="AI agent simulation for infra monitoring, diagnosis and automation.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/incidents/examples")
def examples() -> dict[str, list[str]]:
    return {
        "incidents": [
            "Disk usage > 90%",
            "Server CPU spike",
            "Memory usage high",
        ]
    }


@app.post("/agent/run")
def run_agent(payload: RunAgentRequest) -> dict:
    return workflow.run(
        incident=payload.incident,
        metrics_override=payload.metrics,
        logs_override=payload.logs,
    )
