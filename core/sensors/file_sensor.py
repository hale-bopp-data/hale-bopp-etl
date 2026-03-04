from __future__ import annotations

from airflow.sensors.filesystem import FileSensor


def file_ready_sensor(
    task_id: str,
    fs_conn_id: str,
    filepath: str,
    poke_interval: int = 60,
    timeout: int = 1800,
    dag=None,
) -> FileSensor:
    return FileSensor(
        task_id=task_id,
        fs_conn_id=fs_conn_id,
        filepath=filepath,
        poke_interval=poke_interval,
        timeout=timeout,
        dag=dag,
    )
