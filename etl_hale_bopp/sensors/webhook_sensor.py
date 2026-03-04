"""Webhook sensor for receiving events from DB-HALE-BOPP and ARGOS-HALE-BOPP.

Exposes a simple Flask endpoint that Dagster's sensor polls for new events.
For MVP, events are written to a JSONL file that the sensor watches.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dagster import RunRequest, SensorEvaluationContext, sensor

EVENTS_DIR = Path(os.environ.get("HALEBOPP_EVENTS_DIR", "/tmp/hale-bopp-events"))


@sensor(minimum_interval_seconds=10)
def webhook_event_sensor(context: SensorEvaluationContext):
    """Watch for new event files dropped by the webhook endpoint."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    cursor = int(context.cursor) if context.cursor else 0
    new_cursor = cursor

    for event_file in sorted(EVENTS_DIR.glob("*.json")):
        file_ts = int(event_file.stat().st_mtime_ns)
        if file_ts <= cursor:
            continue

        with open(event_file, encoding="utf-8") as f:
            event = json.load(f)

        event_type = event.get("event_type", "")
        context.log.info(f"New event: {event_type} from {event_file.name}")

        # Trigger a run for events that need ETL processing
        if event_type in ("db.schema.deploy.completed", "argos.gate.pass"):
            yield RunRequest(
                run_key=event.get("event_id", event_file.stem),
                run_config={"ops": {"event_payload": {"config": event}}},
                tags={"event_type": event_type},
            )

        new_cursor = max(new_cursor, file_ts)
        event_file.unlink()  # Consume the event

    context.update_cursor(str(new_cursor))
