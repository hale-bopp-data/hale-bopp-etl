from __future__ import annotations

from typing import Any, Dict

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.utils.dates import days_ago

from common_utilities import get_workflow_tasks
from .schema import validate_pipeline_config


def _default_python_callable(task_payload: Dict[str, Any] | None = None, **context: Any) -> None:
    print("[ETLBELVISO] Python task executed")
    print(f"payload={task_payload or {}}")
    print(f"dag_run_id={context.get('run_id')}")


def _build_task(task_cfg: Dict[str, Any], dag: DAG):
    task_type = task_cfg["type"]
    task_id = task_cfg["id"]

    if task_type == "python":
        return PythonOperator(
            task_id=task_id,
            python_callable=_default_python_callable,
            op_kwargs={"task_payload": task_cfg.get("payload", {})},
            dag=dag,
        )

    if task_type == "bash":
        return BashOperator(
            task_id=task_id,
            bash_command=task_cfg.get("bash_command", "echo 'ETLBELVISO bash task'"),
            dag=dag,
        )

    if task_type == "http":
        return SimpleHttpOperator(
            task_id=task_id,
            http_conn_id=task_cfg.get("http_conn_id", "n8n_default"),
            endpoint=task_cfg.get("endpoint", "/webhook/airflow"),
            method=task_cfg.get("method", "POST"),
            data=task_cfg.get("data", "{}"),
            headers=task_cfg.get("headers", {"Content-Type": "application/json"}),
            log_response=True,
            dag=dag,
        )

    raise ValueError(f"Unsupported task type: {task_type}")


def build_dags_from_config(config: Dict[str, Any]) -> Dict[str, DAG]:
    validation = validate_pipeline_config(config)
    if not validation.valid:
        raise ValueError("Invalid orchestration config:\n- " + "\n- ".join(validation.errors))

    created: Dict[str, DAG] = {}

    for pipeline in config["pipelines"]:
        resolved_tasks = pipeline.get("tasks")
        if pipeline.get("workflow_ref") is not None:
            wf_ref = pipeline["workflow_ref"]
            resolved_tasks = get_workflow_tasks(
                workflow_id=wf_ref["id"],
                context=wf_ref.get("context", {}),
            )

        dag = DAG(
            dag_id=pipeline["id"],
            description=pipeline.get("description", "ETLBELVISO generated DAG"),
            schedule_interval=pipeline.get("schedule"),
            catchup=False,
            start_date=days_ago(1),
            tags=pipeline.get("tags", ["etlbELVISO"]),
            default_args={
                "owner": pipeline.get("owner", "data-platform"),
                "depends_on_past": False,
                "email_on_failure": False,
                "email_on_retry": False,
                "retries": pipeline.get("retries", 1),
            },
        )

        with dag:
            start = EmptyOperator(task_id="start")
            end = EmptyOperator(task_id="end")
            airflow_tasks = [_build_task(task_cfg, dag) for task_cfg in (resolved_tasks or [])]

            if airflow_tasks:
                start >> airflow_tasks[0]
                for i in range(len(airflow_tasks) - 1):
                    airflow_tasks[i] >> airflow_tasks[i + 1]
                airflow_tasks[-1] >> end
            else:
                start >> end

        created[pipeline["id"]] = dag

    return created
