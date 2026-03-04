from __future__ import annotations

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id="etlb_master_orchestrator",
    description="Master DAG for ETLBELVISO pipelines",
    schedule_interval=None,
    catchup=False,
    start_date=days_ago(1),
    tags=["etlbELVISO", "master"],
) as dag:
    start = EmptyOperator(task_id="start")

    run_daily = TriggerDagRunOperator(
        task_id="trigger_etlb_daily_pipeline",
        trigger_dag_id="etlb_daily_pipeline",
        wait_for_completion=False,
    )

    run_event = TriggerDagRunOperator(
        task_id="trigger_etlb_event_pipeline",
        trigger_dag_id="etlb_event_pipeline",
        wait_for_completion=False,
    )

    end = EmptyOperator(task_id="end")

    start >> [run_daily, run_event] >> end
