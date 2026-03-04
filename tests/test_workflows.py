"""Tests for prebuilt workflow templates."""

import pytest

from hale_bopp_etl.workflows.prebuilt import WORKFLOW_REGISTRY, get_workflow_tasks


def test_all_workflows_registered():
    expected = {"daily_etl_n8n", "event_etl_n8n", "quality_gate",
                "extract_and_unzip", "load_to_db", "dynamic_file_router"}
    assert set(WORKFLOW_REGISTRY.keys()) == expected


def test_daily_etl_default():
    tasks = get_workflow_tasks("daily_etl_n8n")
    assert len(tasks) == 3
    assert tasks[0]["type"] == "bash"
    assert tasks[1]["type"] == "python"
    assert tasks[2]["type"] == "http"


def test_daily_etl_custom_endpoint():
    tasks = get_workflow_tasks("daily_etl_n8n", {"endpoint": "/custom"})
    assert tasks[2]["endpoint"] == "/custom"


def test_quality_gate_custom_cmd():
    tasks = get_workflow_tasks("quality_gate", {"check_cmd": "python check.py"})
    assert "python check.py" in tasks[0]["bash_command"]


def test_unknown_workflow_raises():
    with pytest.raises(ValueError, match="Unknown workflow_id"):
        get_workflow_tasks("nonexistent")


def test_get_workflow_returns_copy():
    t1 = get_workflow_tasks("daily_etl_n8n")
    t2 = get_workflow_tasks("daily_etl_n8n")
    t1[0]["id"] = "modified"
    assert t2[0]["id"] != "modified"
