from __future__ import annotations

from airflow.providers.http.operators.http import SimpleHttpOperator


def n8n_callback_task(
    task_id: str,
    endpoint: str,
    payload: str,
    http_conn_id: str = "n8n_default",
    method: str = "POST",
    dag=None,
) -> SimpleHttpOperator:
    return SimpleHttpOperator(
        task_id=task_id,
        http_conn_id=http_conn_id,
        endpoint=endpoint,
        method=method,
        data=payload,
        headers={"Content-Type": "application/json"},
        log_response=True,
        dag=dag,
    )
