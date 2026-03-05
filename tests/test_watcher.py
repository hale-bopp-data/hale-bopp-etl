"""Tests for the event watcher."""

import json

from hale_bopp_etl.watcher import _process_events


def test_process_trigger_event(tmp_path, monkeypatch):
    monkeypatch.setattr("hale_bopp_etl.watcher.EVENTS_DIR", tmp_path)

    event = {"event_id": "e1", "event_type": "db.schema.deploy.completed", "payload": {}}
    (tmp_path / "e1.json").write_text(json.dumps(event))

    runs = []
    monkeypatch.setattr("hale_bopp_etl.watcher.run_by_id", lambda pid, cfg=None: runs.append(pid))

    count = _process_events()
    assert count == 1
    assert len(runs) == 1
    assert not (tmp_path / "e1.json").exists()


def test_process_non_trigger_event(tmp_path, monkeypatch):
    monkeypatch.setattr("hale_bopp_etl.watcher.EVENTS_DIR", tmp_path)

    event = {"event_id": "e2", "event_type": "some.other.event", "payload": {}}
    (tmp_path / "e2.json").write_text(json.dumps(event))

    runs = []
    monkeypatch.setattr("hale_bopp_etl.watcher.run_by_id", lambda pid, cfg=None: runs.append(pid))

    count = _process_events()
    assert count == 0
    assert len(runs) == 0
    assert not (tmp_path / "e2.json").exists()


def test_process_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("hale_bopp_etl.watcher.EVENTS_DIR", tmp_path)
    count = _process_events()
    assert count == 0
