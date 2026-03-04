"""Python task operator for Dagster."""

from __future__ import annotations

from typing import Any

from dagster import OpExecutionContext, op


@op
def python_op(context: OpExecutionContext, payload: dict[str, Any]) -> dict[str, Any]:
    """Execute a Python task with the given payload. Returns the payload for downstream ops."""
    context.log.info(f"Python op executing with payload: {payload}")
    # MVP: log and pass through. Real implementations will import and call
    # domain-specific functions based on payload["stage"].
    return payload
