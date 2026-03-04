"""Tests for pipeline config validation."""

from hale_bopp_etl.schema import validate_pipeline_config


def test_valid_config_with_tasks():
    config = {
        "pipelines": [
            {
                "id": "test_pipeline",
                "schedule": "0 4 * * *",
                "tasks": [
                    {"id": "step_1", "type": "bash", "bash_command": "echo hello"},
                    {"id": "step_2", "type": "python", "payload": {}},
                    {"id": "step_3", "type": "http", "endpoint": "/webhook/test"},
                ],
            }
        ]
    }
    result = validate_pipeline_config(config)
    assert result.valid
    assert result.errors == []


def test_valid_config_with_workflow_ref():
    config = {
        "pipelines": [
            {
                "id": "daily_pipeline",
                "schedule": None,
                "workflow_ref": {"id": "daily_etl_n8n", "context": {"endpoint": "/x"}},
            }
        ]
    }
    result = validate_pipeline_config(config)
    assert result.valid


def test_invalid_empty_id():
    config = {
        "pipelines": [
            {"id": "", "schedule": None, "tasks": [{"id": "s", "type": "bash"}]}
        ]
    }
    result = validate_pipeline_config(config)
    assert not result.valid
    assert any("id" in e for e in result.errors)


def test_invalid_missing_schedule():
    config = {
        "pipelines": [
            {"id": "test", "tasks": [{"id": "s", "type": "bash"}]}
        ]
    }
    result = validate_pipeline_config(config)
    assert not result.valid
    assert any("schedule" in e for e in result.errors)


def test_invalid_both_workflow_and_tasks():
    config = {
        "pipelines": [
            {
                "id": "test",
                "schedule": None,
                "workflow_ref": {"id": "daily_etl_n8n"},
                "tasks": [{"id": "s", "type": "bash"}],
            }
        ]
    }
    result = validate_pipeline_config(config)
    assert not result.valid


def test_invalid_no_workflow_no_tasks():
    config = {"pipelines": [{"id": "test", "schedule": None}]}
    result = validate_pipeline_config(config)
    assert not result.valid


def test_invalid_task_type():
    config = {
        "pipelines": [
            {"id": "test", "schedule": None, "tasks": [{"id": "s", "type": "spark"}]}
        ]
    }
    result = validate_pipeline_config(config)
    assert not result.valid
    assert any("type" in e for e in result.errors)


def test_empty_pipelines():
    config = {"pipelines": []}
    result = validate_pipeline_config(config)
    assert not result.valid
