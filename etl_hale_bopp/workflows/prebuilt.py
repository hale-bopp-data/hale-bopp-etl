"""Prebuilt workflow templates — config-driven task lists.

Each template is a factory function that receives a context dict
and returns a list of task definitions compatible with job_factory.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

WORKFLOW_REGISTRY: dict[str, Any] = {}


def _register(name: str):
    def decorator(fn):
        WORKFLOW_REGISTRY[name] = fn
        return fn
    return decorator


def get_workflow_tasks(workflow_id: str, context: dict[str, Any] | None = None) -> list[dict]:
    """Resolve a workflow_ref into a list of task dicts."""
    if workflow_id not in WORKFLOW_REGISTRY:
        raise ValueError(f"Unknown workflow_id: {workflow_id}. Available: {list(WORKFLOW_REGISTRY)}")
    return deepcopy(WORKFLOW_REGISTRY[workflow_id](context or {}))


@_register("daily_etl_n8n")
def _daily_etl_n8n(ctx: dict) -> list[dict]:
    endpoint = ctx.get("endpoint", "/webhook/etlb-daily")
    return [
        {"id": "extract_step", "type": "bash", "bash_command": "echo '[extract] daily extraction started'"},
        {"id": "transform_step", "type": "python", "payload": {"stage": "transform", "mode": "daily"}},
        {"id": "notify_n8n", "type": "http", "endpoint": endpoint, "method": "POST",
         "data": '{"pipeline": "daily_etl", "status": "completed"}'},
    ]


@_register("event_etl_n8n")
def _event_etl_n8n(ctx: dict) -> list[dict]:
    endpoint = ctx.get("endpoint", "/webhook/etlb-event")
    return [
        {"id": "event_guard", "type": "bash", "bash_command": "echo '[guard] validating event payload'"},
        {"id": "event_transform", "type": "python", "payload": {"stage": "transform", "mode": "event"}},
        {"id": "callback_n8n", "type": "http", "endpoint": endpoint, "method": "POST",
         "data": '{"pipeline": "event_etl", "status": "completed"}'},
    ]


@_register("quality_gate")
def _quality_gate(ctx: dict) -> list[dict]:
    check_cmd = ctx.get("check_cmd", "echo '[quality] basic checks passed'")
    return [
        {"id": "quality_precheck", "type": "bash", "bash_command": check_cmd},
        {"id": "quality_report", "type": "python", "payload": {"stage": "quality", "mode": "gate"}},
    ]


@_register("extract_and_unzip")
def _extract_and_unzip(ctx: dict) -> list[dict]:
    source_url = ctx.get("source_url", "http://example.com/data.zip")
    dest_folder = ctx.get("dest_folder", "/opt/data/inbound")
    return [
        {"id": "download_data", "type": "bash",
         "bash_command": f"mkdir -p {dest_folder} && curl -sL -o {dest_folder}/download.zip {source_url}"},
        {"id": "unzip_data", "type": "bash",
         "bash_command": f"cd {dest_folder} && unzip -o download.zip && rm download.zip"},
    ]


@_register("load_to_db")
def _load_to_db(ctx: dict) -> list[dict]:
    file_path = ctx.get("file_path", "/opt/data/inbound/data.csv")
    table_name = ctx.get("table_name", "public.staging_table")
    return [
        {"id": "validate_file", "type": "bash", "bash_command": f"test -f {file_path} && echo 'OK'"},
        {"id": "execute_db_load", "type": "python",
         "payload": {"stage": "load", "file": file_path, "target_table": table_name}},
    ]


@_register("dynamic_file_router")
def _dynamic_file_router(ctx: dict) -> list[dict]:
    file_path = ctx.get("file_path", "/opt/data/inbound/data.csv")
    threshold_mb = ctx.get("threshold_mb", 100)
    return [
        {"id": "check_and_route", "type": "python",
         "payload": {"stage": "route_and_execute", "file": file_path, "threshold_mb": threshold_mb,
                     "action_local": "pandas_process", "action_remote": "trigger_spark_job"}},
    ]
