"""Pipeline config validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_TASK_TYPES = {"python", "bash", "http"}


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)


def validate_pipeline_config(config: dict[str, Any]) -> ValidationResult:
    """Validate a pipeline configuration dict. Returns ValidationResult."""
    result = ValidationResult()

    pipelines = config.get("pipelines")
    if not pipelines or not isinstance(pipelines, list):
        result.valid = False
        result.errors.append("'pipelines' must be a non-empty list")
        return result

    for i, p in enumerate(pipelines):
        prefix = f"pipelines[{i}]"

        pid = p.get("id", "")
        if not isinstance(pid, str) or not pid.strip():
            result.valid = False
            result.errors.append(f"{prefix}: 'id' must be a non-empty string")

        if "schedule" not in p:
            result.valid = False
            result.errors.append(f"{prefix}: 'schedule' is required (use null for manual)")

        has_workflow = "workflow_ref" in p
        has_tasks = "tasks" in p

        if not has_workflow and not has_tasks:
            result.valid = False
            result.errors.append(f"{prefix}: must have 'workflow_ref' or 'tasks'")
        elif has_workflow and has_tasks:
            result.valid = False
            result.errors.append(f"{prefix}: cannot have both 'workflow_ref' and 'tasks'")

        if has_tasks:
            tasks = p["tasks"]
            if not isinstance(tasks, list) or len(tasks) == 0:
                result.valid = False
                result.errors.append(f"{prefix}: 'tasks' must be a non-empty list")
            else:
                for j, t in enumerate(tasks):
                    t_prefix = f"{prefix}.tasks[{j}]"
                    if not t.get("id", "").strip():
                        result.valid = False
                        result.errors.append(f"{t_prefix}: 'id' must be a non-empty string")
                    if t.get("type") not in VALID_TASK_TYPES:
                        result.valid = False
                        result.errors.append(f"{t_prefix}: 'type' must be one of {VALID_TASK_TYPES}")

    return result
