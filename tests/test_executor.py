"""Tests for the task executor."""

import pytest

from etl_hale_bopp.executor import execute_task


def test_bash_task():
    result = execute_task({"id": "t1", "type": "bash", "bash_command": "echo hello"})
    assert result["type"] == "bash"
    assert "hello" in result["stdout"]
    assert result["returncode"] == 0


def test_bash_task_failure():
    with pytest.raises(RuntimeError, match="failed"):
        execute_task({"id": "t1", "type": "bash", "bash_command": "exit 1"})


def test_python_task():
    result = execute_task({"id": "t1", "type": "python", "payload": {"stage": "test"}})
    assert result["type"] == "python"
    assert result["payload"]["stage"] == "test"


def test_unknown_type():
    with pytest.raises(ValueError, match="Unknown task type"):
        execute_task({"id": "t1", "type": "spark"})
