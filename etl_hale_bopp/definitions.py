"""Dagster Definitions — entry point for the ETL-HALE-BOPP orchestrator.

Reads pipelines.yaml, validates, builds jobs, registers schedules and sensors.
"""

from __future__ import annotations

from dagster import Definitions, ScheduleDefinition

from etl_hale_bopp.config_loader import load_orchestration_config
from etl_hale_bopp.job_factory import build_jobs_from_config
from etl_hale_bopp.schema import validate_pipeline_config
from etl_hale_bopp.sensors.webhook_sensor import webhook_event_sensor


def _build_definitions() -> Definitions:
    config = load_orchestration_config()
    result = validate_pipeline_config(config)
    if not result.valid:
        raise ValueError(f"Invalid pipeline config: {result.errors}")

    jobs = build_jobs_from_config(config)

    # Create schedules for pipelines that have a cron schedule
    schedules = []
    for pipeline in config.get("pipelines", []):
        cron = pipeline.get("schedule")
        if cron:
            matching_job = next((j for j in jobs if j.name == pipeline["id"]), None)
            if matching_job:
                schedules.append(
                    ScheduleDefinition(
                        name=f"{pipeline['id']}_schedule",
                        job=matching_job,
                        cron_schedule=cron,
                    )
                )

    return Definitions(
        jobs=jobs,
        schedules=schedules,
        sensors=[webhook_event_sensor],
    )


defs = _build_definitions()
