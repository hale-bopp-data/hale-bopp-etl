from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _daily_etl_n8n(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    ctx = context or {}
    endpoint = ctx.get("endpoint", "/webhook/etlb-daily")

    return [
        {
            "id": "extract_step",
            "type": "bash",
            "bash_command": "echo '[extract] start daily extraction'",
        },
        {
            "id": "transform_step",
            "type": "python",
            "payload": {"stage": "transform", "mode": "daily"},
        },
        {
            "id": "notify_n8n",
            "type": "http",
            "http_conn_id": "n8n_default",
            "endpoint": endpoint,
            "method": "POST",
            "data": '{"pipeline":"etlb_daily_pipeline","status":"completed","source":"airflow"}',
            "headers": {"Content-Type": "application/json"},
        },
    ]


def _event_etl_n8n(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    ctx = context or {}
    endpoint = ctx.get("endpoint", "/webhook/etlb-event")

    return [
        {
            "id": "event_guard",
            "type": "bash",
            "bash_command": "echo '[event] validating payload and source'",
        },
        {
            "id": "event_transform",
            "type": "python",
            "payload": {"stage": "transform", "mode": "event"},
        },
        {
            "id": "callback_n8n",
            "type": "http",
            "http_conn_id": "n8n_default",
            "endpoint": endpoint,
            "method": "POST",
            "data": '{"pipeline":"etlb_event_pipeline","status":"completed","source":"airflow"}',
            "headers": {"Content-Type": "application/json"},
        },
    ]


def _quality_gate(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    ctx = context or {}
    check_cmd = ctx.get("check_cmd", "echo '[quality] basic checks passed'")

    return [
        {"id": "quality_precheck", "type": "bash", "bash_command": check_cmd},
        {
            "id": "quality_report",
            "type": "python",
            "payload": {"stage": "quality", "mode": "gate"},
        },
    ]


def _extract_and_unzip(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    ctx = context or {}
    source_url = ctx.get("source_url", "http://example.com/data.zip")
    dest_folder = ctx.get("dest_folder", "/opt/airflow/data/inbound")

    return [
        {
            "id": "download_data",
            "type": "bash",
            "bash_command": f"mkdir -p {dest_folder} && curl -sSL {source_url} -o {dest_folder}/download.zip",
        },
        {
            "id": "unzip_data",
            "type": "bash",
            "bash_command": f"unzip -o {dest_folder}/download.zip -d {dest_folder}/ && rm {dest_folder}/download.zip",
        },
    ]


def _load_to_db(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    ctx = context or {}
    file_path = ctx.get("file_path", "/opt/airflow/data/inbound/data.csv")
    table_name = ctx.get("table_name", "public.staging_table")

    return [
        {
            "id": "validate_file",
            "type": "bash",
            "bash_command": f"test -f {file_path} || (echo 'File missing' && exit 1)",
        },
        {
            "id": "execute_db_load",
            "type": "python",
            "payload": {"stage": "load", "file": file_path, "target_table": table_name},
        },
    ]


def _dynamic_file_router(context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    ctx = context or {}
    file_path = ctx.get("file_path", "/opt/airflow/data/inbound/data.csv")
    threshold_mb = ctx.get("threshold_mb", 100)

    # In a real Airflow DAG, this would be a BranchPythonOperator.
    # For our YAML-driven dynamic approach, we simulate the branching logic 
    # by chaining a Python evaluation task that pushes to XCom, 
    # followed by a ShortCircuitOperator or conditional downstream tasks.
    # To keep it simple in our current factory mapping, we use a single Python task
    # that internally decides whether to process locally (pandas) or via distant API (Spark).
    
    return [
        {
            "id": "check_file_size_and_route",
            "type": "python",
            "payload": {
                "stage": "route_and_execute",
                "file": file_path,
                "threshold_mb": threshold_mb,
                "action_local": "pandas_process",
                "action_remote": "trigger_spark_job"
            },
        }
    ]


WORKFLOW_REGISTRY = {
    "daily_etl_n8n": _daily_etl_n8n,
    "event_etl_n8n": _event_etl_n8n,
    "quality_gate": _quality_gate,
    "extract_and_unzip": _extract_and_unzip,
    "load_to_db": _load_to_db,
    "dynamic_file_router": _dynamic_file_router,
}


def list_workflows() -> List[str]:
    return sorted(WORKFLOW_REGISTRY.keys())


def get_workflow_tasks(workflow_id: str, context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    if workflow_id not in WORKFLOW_REGISTRY:
        available = ", ".join(list_workflows())
        raise ValueError(f"Unknown workflow_id '{workflow_id}'. Available: {available}")

    tasks = WORKFLOW_REGISTRY[workflow_id](context)
    return deepcopy(tasks)
