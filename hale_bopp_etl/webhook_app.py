"""Webhook receiver — writes events to disk for the event watcher.

Receives Universal Events from hale-bopp-db and hale-bopp-argos
via POST /api/v1/webhook.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any

EVENTS_DIR = Path(os.environ.get("HALEBOPP_EVENTS_DIR", "/tmp/hale-bopp-events"))

app = FastAPI(title="ETL-HALE-BOPP Webhook Receiver", version="0.1.0")


class UniversalEvent(BaseModel):
    event_id: str = ""
    timestamp: str = ""
    source: str = ""
    event_type: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


@app.post("/api/v1/webhook", status_code=202)
def receive_webhook(event: UniversalEvent):
    """Receive a Universal Event and write it to disk for the sensor."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    event_id = event.event_id or str(uuid.uuid4())
    file_path = EVENTS_DIR / f"{event_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(event.model_dump(), f)

    return {"accepted": True, "event_id": event_id}


@app.get("/api/v1/health", response_model=HealthResponse)
def health():
    return HealthResponse()
