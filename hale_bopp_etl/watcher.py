"""Event watcher — polls events directory and triggers pipelines."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from hale_bopp_etl.runner import run_by_id

log = logging.getLogger("hale-bopp-etl")

EVENTS_DIR = Path(os.environ.get("HALEBOPP_EVENTS_DIR", "/tmp/hale-bopp-events"))
TRIGGER_TYPES = {"db.schema.deploy.completed", "argos.gate.pass"}
DEFAULT_PIPELINE = "etlb_event_pipeline"


def watch(interval: int = 10, config_path: str | None = None) -> None:
    """Poll events directory and trigger pipeline runs. Blocks forever."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Watching %s (interval=%ds)", EVENTS_DIR, interval)

    while True:
        _process_events(config_path)
        time.sleep(interval)


def _process_events(config_path: str | None = None) -> int:
    """Process all pending event files. Returns count of triggered runs."""
    if not EVENTS_DIR.exists():
        return 0

    triggered = 0
    for event_file in sorted(EVENTS_DIR.glob("*.json")):
        try:
            with open(event_file, encoding="utf-8") as f:
                event = json.load(f)

            event_type = event.get("event_type", "")
            log.info("Event: %s (%s)", event_type, event_file.name)

            if event_type in TRIGGER_TYPES:
                run_by_id(DEFAULT_PIPELINE, config_path)
                triggered += 1

            event_file.unlink()
        except Exception:
            log.exception("Error processing %s", event_file.name)

    return triggered
