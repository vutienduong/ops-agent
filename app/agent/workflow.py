from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agent.executor import ExecutorAgent
from app.agent.logs import LogService
from app.agent.models import Anomaly, Diagnosis, ExecutionRecord, PlanStep, Verification
from app.agent.monitoring import MonitoringService
from app.agent.planner import PlannerAgent
from app.agent.reasoner import Reasoner
from app.agent.verifier import VerifierAgent


class AgentState(TypedDict, total=False):
    incident: str | None
    input_metrics: dict[str, float] | None
    input_logs: list[str] | None
    metrics: dict[str, float]
    anomalies: list[Anomaly]
    logs: list[str]
    evidence: list[str]
    diagnosis: Diagnosis
    plan: list[PlanStep]
    execution: list[ExecutionRecord]
    post_metrics: dict[str, float]
    verification: Verification


class InfraOpsWorkflow:
    def __init__(
        self,
        monitoring: MonitoringService,
        logs: LogService,
        reasoner: Reasoner,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        verifier: VerifierAgent,
    ) -> None:
        self.monitoring = monitoring
        self.logs = logs
        self.reasoner = reasoner
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.graph = self._build_graph()

    def _build_graph(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("monitor", self._monitor_node)
        graph_builder.add_node("diagnose", self._diagnose_node)
        graph_builder.add_node("plan", self._plan_node)
        graph_builder.add_node("execute", self._execute_node)
        graph_builder.add_node("verify", self._verify_node)

        graph_builder.set_entry_point("monitor")
        graph_builder.add_edge("monitor", "diagnose")
        graph_builder.add_edge("diagnose", "plan")
        graph_builder.add_edge("plan", "execute")
        graph_builder.add_edge("execute", "verify")
        graph_builder.add_edge("verify", END)
        return graph_builder.compile()

    def run(
        self,
        incident: str | None = None,
        metrics_override: dict[str, float] | None = None,
        logs_override: list[str] | None = None,
    ) -> dict[str, Any]:
        state: AgentState = {
            "incident": incident,
            "input_metrics": metrics_override,
            "input_logs": logs_override,
        }
        output = self.graph.invoke(state)
        return self._serialize(output)

    def _monitor_node(self, state: AgentState) -> AgentState:
        metrics = state.get("input_metrics") or self.monitoring.fetch_metrics()
        anomalies = self.monitoring.detect_anomalies(metrics)
        logs = state.get("input_logs") or self.logs.read_logs()
        evidence = self.logs.select_evidence(anomalies=anomalies, logs=logs)
        return {"metrics": metrics, "anomalies": anomalies, "logs": logs, "evidence": evidence}

    def _diagnose_node(self, state: AgentState) -> AgentState:
        diagnosis = self.reasoner.diagnose(
            incident=state.get("incident"),
            anomalies=state.get("anomalies", []),
            evidence=state.get("evidence", []),
        )
        return {"diagnosis": diagnosis}

    def _plan_node(self, state: AgentState) -> AgentState:
        plan = self.planner.create_plan(
            diagnosis=state["diagnosis"],
            anomalies=state.get("anomalies", []),
        )
        return {"plan": plan}

    def _execute_node(self, state: AgentState) -> AgentState:
        execution = self.executor.execute_plan(state.get("plan", []))
        post_metrics = self._simulate_post_metrics(
            metrics=state.get("metrics", {}),
            execution=execution,
        )
        return {"execution": execution, "post_metrics": post_metrics}

    def _verify_node(self, state: AgentState) -> AgentState:
        verification = self.verifier.verify(
            anomalies=state.get("anomalies", []),
            post_metrics=state.get("post_metrics", state.get("metrics", {})),
        )
        return {"verification": verification}

    def _simulate_post_metrics(
        self, metrics: dict[str, float], execution: list[ExecutionRecord]
    ) -> dict[str, float]:
        updated = dict(metrics)
        for step in execution:
            if step.status != "success":
                continue
            command = step.command or ""
            if "cleanup_disk.sh" in command:
                if "disk_usage" in updated:
                    updated["disk_usage"] = max(58.0, updated["disk_usage"] - 28.0)
            if "reduce_cpu.sh" in command:
                if "cpu_usage" in updated:
                    updated["cpu_usage"] = max(45.0, updated["cpu_usage"] - 32.0)
        return updated

    def _serialize(self, state: AgentState) -> dict[str, Any]:
        return {
            "incident": state.get("incident"),
            "metrics": state.get("metrics", {}),
            "anomalies": [anomaly.model_dump() for anomaly in state.get("anomalies", [])],
            "evidence": state.get("evidence", []),
            "diagnosis": state["diagnosis"].model_dump() if state.get("diagnosis") else {},
            "plan": [step.model_dump() for step in state.get("plan", [])],
            "execution": [result.model_dump() for result in state.get("execution", [])],
            "post_metrics": state.get("post_metrics", {}),
            "verification": state["verification"].model_dump() if state.get("verification") else {},
        }
