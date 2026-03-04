"""Pipeline runner — loads config, resolves tasks, executes pipelines."""

from __future__ import annotations

import logging
from typing import Any

from hale_bopp_etl.config_loader import load_orchestration_config
from hale_bopp_etl.executor import execute_task
from hale_bopp_etl.schema import validate_pipeline_config
from hale_bopp_etl.workflows.prebuilt import get_workflow_tasks

log = logging.getLogger("hale-bopp-etl")


def load_pipelines(config_path: str | None = None) -> list[dict[str, Any]]:
    """Load and validate pipeline config, return pipeline list."""
    config = load_orchestration_config(config_path)
    result = validate_pipeline_config(config)
    if not result.valid:
        raise ValueError(f"Invalid pipeline config: {result.errors}")
    return config["pipelines"]


def resolve_tasks(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve a pipeline's tasks — inline or from workflow_ref."""
    if "workflow_ref" in pipeline:
        ref = pipeline["workflow_ref"]
        return get_workflow_tasks(ref["id"], ref.get("context", {}))
    return pipeline.get("tasks", [])


def run_pipeline(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute all tasks in a pipeline sequentially. Returns list of results."""
    pipeline_id = pipeline["id"]
    tasks = resolve_tasks(pipeline)

    if not tasks:
        log.warning("[%s] No tasks to run", pipeline_id)
        return []

    log.info("[%s] Starting pipeline (%d tasks)", pipeline_id, len(tasks))
    results = []

    for i, task in enumerate(tasks, 1):
        log.info("[%s] Task %d/%d: %s", pipeline_id, i, len(tasks), task["id"])
        result = execute_task(task)
        results.append(result)

    log.info("[%s] Pipeline completed (%d tasks)", pipeline_id, len(results))
    return results


def run_by_id(pipeline_id: str, config_path: str | None = None) -> list[dict[str, Any]]:
    """Find and run a pipeline by its ID."""
    pipelines = load_pipelines(config_path)
    pipeline = next((p for p in pipelines if p["id"] == pipeline_id), None)
    if pipeline is None:
        available = [p["id"] for p in pipelines]
        raise ValueError(f"Pipeline '{pipeline_id}' not found. Available: {available}")
    return run_pipeline(pipeline)


def list_pipelines(config_path: str | None = None) -> list[dict[str, str]]:
    """List all pipelines with their schedule info."""
    pipelines = load_pipelines(config_path)
    return [
        {
            "id": p["id"],
            "schedule": p.get("schedule") or "(manual)",
            "description": p.get("description", ""),
        }
        for p in pipelines
    ]
