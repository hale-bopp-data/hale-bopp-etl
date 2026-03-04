"""Job factory — builds Dagster jobs from YAML pipeline config.

Replaces the Airflow DAG factory with the same config-driven philosophy.
"""

from __future__ import annotations

from typing import Any

from dagster import GraphDefinition, JobDefinition, NodeInvocation, OpDefinition, In, Out, op

from etl_hale_bopp.workflows.prebuilt import get_workflow_tasks


def build_jobs_from_config(config: dict[str, Any]) -> list[JobDefinition]:
    """Convert a validated pipeline config into a list of Dagster JobDefinitions."""
    jobs: list[JobDefinition] = []

    for pipeline in config.get("pipelines", []):
        job = _build_single_job(pipeline)
        if job:
            jobs.append(job)

    return jobs


def _build_single_job(pipeline: dict[str, Any]) -> JobDefinition | None:
    """Build a single Dagster job from a pipeline config entry."""
    pipeline_id = pipeline["id"]

    # Resolve tasks: inline or from workflow_ref
    if "workflow_ref" in pipeline:
        ref = pipeline["workflow_ref"]
        tasks = get_workflow_tasks(ref["id"], ref.get("context", {}))
    else:
        tasks = pipeline.get("tasks", [])

    if not tasks:
        return None

    # Create ops for each task
    ops = [_create_op_for_task(t) for t in tasks]

    # Build a linear graph: op_0 >> op_1 >> ... >> op_n
    graph = _build_linear_graph(pipeline_id, ops)

    return graph.to_job(
        name=pipeline_id,
        description=pipeline.get("description", f"Pipeline {pipeline_id}"),
        tags={
            "owner": pipeline.get("owner", "data-platform"),
            **{tag: "" for tag in pipeline.get("tags", [])},
        },
    )


def _create_op_for_task(task: dict[str, Any]) -> OpDefinition:
    """Create a Dagster op from a task config dict."""
    task_id = task["id"]
    task_type = task["type"]

    if task_type == "bash":
        command = task.get("bash_command", "echo 'no-op'")

        @op(name=task_id, ins={"upstream": In(Nothing)}, out=Out(str))
        def _bash(context):
            import subprocess
            context.log.info(f"Bash: {command}")
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=600)
            if r.returncode != 0:
                raise RuntimeError(f"Failed: {r.stderr}")
            return r.stdout

        return _bash

    elif task_type == "python":
        payload = task.get("payload", {})

        @op(name=task_id, ins={"upstream": In(Nothing)}, out=Out(dict))
        def _python(context):
            context.log.info(f"Python op: {payload}")
            return payload

        return _python

    elif task_type == "http":
        http_config = {
            "base_url": task.get("base_url", "http://localhost:5678"),
            "endpoint": task.get("endpoint", "/webhook/default"),
            "method": task.get("method", "POST"),
            "data": task.get("data", "{}"),
            "headers": task.get("headers", {"Content-Type": "application/json"}),
        }

        @op(name=task_id, ins={"upstream": In(Nothing)}, out=Out(dict))
        def _http(context):
            import httpx
            url = f"{http_config['base_url']}{http_config['endpoint']}"
            context.log.info(f"HTTP {http_config['method']} → {url}")
            with httpx.Client(timeout=30) as c:
                resp = c.request(http_config["method"], url, content=http_config["data"],
                                 headers=http_config["headers"])
            return {"status_code": resp.status_code}

        return _http

    else:
        raise ValueError(f"Unknown task type: {task_type}")


# Dagster's Nothing type for sequencing ops without data dependencies
from dagster import Nothing


def _build_linear_graph(name: str, ops: list[OpDefinition]) -> GraphDefinition:
    """Chain ops linearly: op_0 >> op_1 >> ... >> op_n."""
    if len(ops) == 1:
        return GraphDefinition(name=f"{name}_graph", node_defs=ops, dependencies={})

    deps = {}
    for i, current_op in enumerate(ops):
        if i == 0:
            deps[NodeInvocation(current_op.name)] = {}
        else:
            deps[NodeInvocation(current_op.name)] = {
                "upstream": ops[i - 1].outs["result"]
            }

    return GraphDefinition(name=f"{name}_graph", node_defs=ops, dependencies=deps)
