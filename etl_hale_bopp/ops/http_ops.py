"""HTTP task operator for Dagster."""

from __future__ import annotations

from typing import Any

import httpx
from dagster import OpExecutionContext, op


@op
def http_op(context: OpExecutionContext, http_config: dict[str, Any]) -> dict[str, Any]:
    """Execute an HTTP request. Returns the response body as dict."""
    base_url = http_config.get("base_url", "http://localhost:5678")
    endpoint = http_config.get("endpoint", "/webhook/default")
    method = http_config.get("method", "POST").upper()
    data = http_config.get("data", "{}")
    headers = http_config.get("headers", {"Content-Type": "application/json"})

    url = f"{base_url}{endpoint}"
    context.log.info(f"HTTP {method} → {url}")

    with httpx.Client(timeout=30) as client:
        resp = client.request(method, url, content=data, headers=headers)
        resp.raise_for_status()

    context.log.info(f"HTTP {resp.status_code}")
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "body": resp.text}
