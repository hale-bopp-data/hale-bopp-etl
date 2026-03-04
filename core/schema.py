from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]


def validate_pipeline_config(config: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []

    pipelines = config.get("pipelines")
    if not isinstance(pipelines, list) or not pipelines:
        errors.append("'pipelines' must be a non-empty list")
        return ValidationResult(valid=False, errors=errors)

    for idx, pipeline in enumerate(pipelines):
        if not isinstance(pipeline, dict):
            errors.append(f"pipeline[{idx}] must be an object")
            continue

        pipeline_id = pipeline.get("id")
        if not isinstance(pipeline_id, str) or not pipeline_id.strip():
            errors.append(f"pipeline[{idx}].id must be a non-empty string")

        if "schedule" not in pipeline:
            errors.append(f"pipeline[{idx}].schedule key is required (use null for manual DAG)")

        workflow_ref = pipeline.get("workflow_ref")
        tasks = pipeline.get("tasks")
        if workflow_ref is not None:
            if not isinstance(workflow_ref, dict):
                errors.append(f"pipeline[{idx}].workflow_ref must be an object")
                continue
            workflow_id = workflow_ref.get("id")
            if not isinstance(workflow_id, str) or not workflow_id.strip():
                errors.append(f"pipeline[{idx}].workflow_ref.id must be a non-empty string")
            continue

        if not isinstance(tasks, list) or not tasks:
            errors.append(
                f"pipeline[{idx}] must define either workflow_ref or a non-empty tasks list"
            )
            continue

        for t_idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                errors.append(f"pipeline[{idx}].tasks[{t_idx}] must be an object")
                continue

            task_id = task.get("id")
            task_type = task.get("type")
            if not isinstance(task_id, str) or not task_id.strip():
                errors.append(f"pipeline[{idx}].tasks[{t_idx}].id must be a non-empty string")
            if task_type not in {"python", "http", "bash"}:
                errors.append(f"pipeline[{idx}].tasks[{t_idx}].type unsupported: {task_type}")

    return ValidationResult(valid=(len(errors) == 0), errors=errors)
