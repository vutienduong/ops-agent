from __future__ import annotations

from app.agent.models import Anomaly, Diagnosis, PlanStep


class PlannerAgent:
    def create_plan(self, diagnosis: Diagnosis, anomalies: list[Anomaly]) -> list[PlanStep]:
        steps: list[PlanStep] = []
        next_id = 1

        has_disk = any("disk" in anomaly.signal for anomaly in anomalies)
        has_cpu = any("cpu" in anomaly.signal for anomaly in anomalies)

        if has_disk:
            steps.append(
                PlanStep(
                    id=f"step-{next_id}",
                    description="Inspect largest files to confirm disk pressure source.",
                    tool="shell",
                    command="bash app/scripts/cleanup_disk.sh --mode inspect",
                )
            )
            next_id += 1
            steps.append(
                PlanStep(
                    id=f"step-{next_id}",
                    description="Run cleanup automation for stale logs/tmp files.",
                    tool="shell",
                    command="bash app/scripts/cleanup_disk.sh --mode cleanup",
                )
            )
            next_id += 1

        if has_cpu:
            steps.append(
                PlanStep(
                    id=f"step-{next_id}",
                    description="Apply temporary CPU pressure relief automation.",
                    tool="shell",
                    command="bash app/scripts/reduce_cpu.sh",
                )
            )
            next_id += 1

        if not steps:
            steps.append(
                PlanStep(
                    id="step-1",
                    description=f"Collect additional diagnostics before action. RCA: {diagnosis.root_cause}",
                    tool="analysis",
                )
            )

        return steps
