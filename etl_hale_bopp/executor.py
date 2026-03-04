"""Task executor — runs bash, http, and python tasks."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

import httpx

log = logging.getLogger("hale-bopp-etl")


def execute_task(task: dict[str, Any]) -> dict[str, Any]:
    """Execute a single task and return the result."""
    task_type = task["type"]
    task_id = task["id"]

    if task_type == "bash":
        return _run_bash(task_id, task.get("bash_command", "echo 'no-op'"))
    elif task_type == "http":
        return _run_http(task_id, task)
    elif task_type == "python":
        return _run_python(task_id, task.get("payload", {}))
    else:
        raise ValueError(f"Unknown task type: {task_type}")


def _run_bash(task_id: str, command: str) -> dict[str, Any]:
    """Execute a bash command."""
    log.info("[%s] bash: %s", task_id, command)
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        log.error("[%s] stderr: %s", task_id, result.stderr)
        raise RuntimeError(f"Task {task_id} failed (exit {result.returncode}): {result.stderr}")
    log.info("[%s] stdout: %s", task_id, result.stdout.strip())
    return {"task_id": task_id, "type": "bash", "stdout": result.stdout, "returncode": 0}


def _run_http(task_id: str, task: dict[str, Any]) -> dict[str, Any]:
    """Execute an HTTP request."""
    base_url = task.get("base_url", "http://localhost:5678")
    endpoint = task.get("endpoint", "/webhook/default")
    method = task.get("method", "POST").upper()
    data = task.get("data", "{}")
    headers = task.get("headers", {"Content-Type": "application/json"})

    url = f"{base_url}{endpoint}"
    log.info("[%s] %s %s", task_id, method, url)

    with httpx.Client(timeout=30) as client:
        resp = client.request(method, url, content=data, headers=headers)
        resp.raise_for_status()

    log.info("[%s] HTTP %d", task_id, resp.status_code)
    return {"task_id": task_id, "type": "http", "status_code": resp.status_code}


def _run_python(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Execute a Python task with the given payload."""
    log.info("[%s] python: %s", task_id, payload)
    return {"task_id": task_id, "type": "python", "payload": payload}
