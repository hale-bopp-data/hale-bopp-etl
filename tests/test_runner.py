"""Tests for the pipeline runner."""

import pytest

from hale_bopp_etl.runner import load_pipelines, resolve_tasks, run_pipeline, list_pipelines


def test_load_pipelines():
    pipelines = load_pipelines()
    assert len(pipelines) == 3
    assert pipelines[0]["id"] == "etlb_daily_pipeline"


def test_resolve_tasks_workflow_ref():
    pipeline = {"id": "test", "workflow_ref": {"id": "daily_etl_n8n", "context": {}}}
    tasks = resolve_tasks(pipeline)
    assert len(tasks) == 3
    assert tasks[0]["type"] == "bash"


def test_resolve_tasks_inline():
    pipeline = {"id": "test", "tasks": [{"id": "s1", "type": "bash", "bash_command": "echo hi"}]}
    tasks = resolve_tasks(pipeline)
    assert len(tasks) == 1


def test_run_pipeline_bash_and_python():
    pipeline = {
        "id": "test_mixed",
        "tasks": [
            {"id": "step1", "type": "bash", "bash_command": "echo hello"},
            {"id": "step2", "type": "python", "payload": {"x": 1}},
        ],
    }
    results = run_pipeline(pipeline)
    assert len(results) == 2
    assert results[0]["type"] == "bash"
    assert "hello" in results[0]["stdout"]
    assert results[1]["type"] == "python"


def test_run_pipeline_empty():
    results = run_pipeline({"id": "empty", "tasks": []})
    assert results == []


def test_list_pipelines():
    pipelines = list_pipelines()
    assert len(pipelines) == 3
    ids = [p["id"] for p in pipelines]
    assert "etlb_daily_pipeline" in ids


def test_run_by_id_not_found():
    from hale_bopp_etl.runner import run_by_id
    with pytest.raises(ValueError, match="not found"):
        run_by_id("nonexistent_pipeline")
