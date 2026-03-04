"""Bash task operator for Dagster."""

from __future__ import annotations

import subprocess

from dagster import OpExecutionContext, op


@op
def bash_op(context: OpExecutionContext, command: str) -> str:
    """Execute a bash command and return stdout."""
    context.log.info(f"Executing bash: {command}")
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        context.log.error(f"stderr: {result.stderr}")
        raise RuntimeError(f"Bash command failed (exit {result.returncode}): {result.stderr}")
    context.log.info(f"stdout: {result.stdout}")
    return result.stdout
