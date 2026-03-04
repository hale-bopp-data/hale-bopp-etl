"""Tests for the webhook receiver app."""

from fastapi.testclient import TestClient

from etl_hale_bopp.webhook_app import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_receive_event(tmp_path, monkeypatch):
    monkeypatch.setenv("HALEBOPP_EVENTS_DIR", str(tmp_path))
    # Reload EVENTS_DIR after monkeypatch
    import etl_hale_bopp.webhook_app as wa
    monkeypatch.setattr(wa, "EVENTS_DIR", tmp_path)

    resp = client.post("/api/v1/webhook", json={
        "event_id": "test-001",
        "timestamp": "2026-03-03T12:00:00Z",
        "source": "db",
        "event_type": "db.schema.deploy.completed",
        "payload": {"table": "users"},
    })
    assert resp.status_code == 202
    assert resp.json()["accepted"] is True

    # Verify file was written
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
