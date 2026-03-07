from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from app.agent.models import ExecutionRecord, PlanStep


class ExecutorAgent:
    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.allowed_scripts = {
            "app/scripts/cleanup_disk.sh",
            "app/scripts/reduce_cpu.sh",
        }

    def execute_plan(self, steps: list[PlanStep]) -> list[ExecutionRecord]:
        return [self._run_step(step) for step in steps]

    def _run_step(self, step: PlanStep) -> ExecutionRecord:
        if not step.command:
            return ExecutionRecord(
                step_id=step.id,
                status="skipped",
                command=step.command,
                output="No executable command.",
            )

        try:
            parts = shlex.split(step.command)
            if len(parts) < 2 or parts[0] != "bash":
                return ExecutionRecord(
                    step_id=step.id,
                    status="blocked",
                    command=step.command,
                    output="Only bash scripts are allowed in this simulation.",
                )

            script_path = parts[1]
            if script_path not in self.allowed_scripts:
                return ExecutionRecord(
                    step_id=step.id,
                    status="blocked",
                    command=step.command,
                    output=f"Command not allowlisted: {script_path}",
                )

            completed = subprocess.run(
                parts,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            output = "\n".join(
                segment for segment in [completed.stdout.strip(), completed.stderr.strip()] if segment
            )[:1200]
            status = "success" if completed.returncode == 0 else "failed"
            return ExecutionRecord(
                step_id=step.id,
                status=status,
                command=step.command,
                output=output or "No output.",
            )
        except Exception as exc:
            return ExecutionRecord(
                step_id=step.id,
                status="failed",
                command=step.command,
                output=str(exc),
            )
