# hale-bopp-etl

[![CI](https://github.com/hale-bopp-data/hale-bopp-etl/actions/workflows/ci.yml/badge.svg)](https://github.com/hale-bopp-data/hale-bopp-etl/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)

Config-driven data orchestration engine — YAML pipelines, webhook triggers, zero frameworks.

No Airflow, no Dagster, no Celery. Just Python, YAML, and deterministic execution.

## Architecture

```
                     ┌──────────────────────┐
  HTTP POST ────────►│  Webhook Receiver    │──── writes ───► /events/*.json
                     │  :3001               │
                     └──────────────────────┘
                                                    │
                     ┌──────────────────────┐       │ polls
  cron / manual ────►│  CLI Runner          │       │
                     │  hale-bopp-etl run   │       ▼
                     └──────────────────────┘  ┌──────────┐
                                               │ Watcher  │──► trigger pipeline
                                               └──────────┘
```

## Features

- **Declarative Pipelines**: Define workflows in YAML, not Python code
- **3 Task Primitives**: `bash`, `http`, `python` — compose anything
- **Webhook Receiver**: FastAPI endpoint for event-driven triggers
- **Event Watcher**: Polls a directory for JSON events, auto-triggers matching pipelines
- **Workflow Templates**: Reusable prebuilt workflows via `workflow_ref`
- **Config Validation**: Schema validation with clear error messages
- **Zero Dependencies**: No framework runtime, no external scheduler, no database required

## Quick Start

```bash
# Install
pip install -e .

# List available pipelines
python -m hale_bopp_etl list

# Run a pipeline
python -m hale_bopp_etl run <pipeline_id>

# Start webhook receiver
python -m hale_bopp_etl webhook --port 3001

# Start event watcher
python -m hale_bopp_etl watch --interval 10
```

## Pipeline Configuration

Pipelines are defined in `config/orchestration/pipelines.yaml`:

```yaml
pipelines:
  - id: daily_pipeline
    schedule: "0 4 * * *"
    description: "Daily data refresh"
    owner: data-platform
    tasks:
      - id: extract
        type: bash
        bash_command: "python scripts/extract.py"
      - id: notify
        type: http
        endpoint: /webhook/etl-done
        method: POST

  - id: quality_check
    schedule: null
    workflow_ref:
      id: quality_gate
      context:
        check_cmd: "python check.py"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/webhook` | Receive events (writes JSON to events dir) |
| `GET` | `/api/v1/health` | Service health check |

### Webhook Payload

```json
{
  "event_id": "evt-001",
  "timestamp": "2026-03-05T12:00:00Z",
  "source": "db",
  "event_type": "db.schema.deploy.completed",
  "payload": {"table": "users"}
}
```

## CLI

```
usage: hale-bopp-etl [-h] [-v] {run,list,watch,webhook} ...

Commands:
  run <pipeline_id>     Run a pipeline by ID
  list                  List available pipelines
  watch                 Watch events directory and trigger pipelines
  webhook               Start webhook receiver (FastAPI/Uvicorn)
```

## Testing

```bash
pip install -e .
pip install pytest
pytest tests/ -v
```

30 tests covering executor, runner, watcher, webhook, schema validation, and workflow templates.

## Part of HALE-BOPP

HALE-BOPP is an open-source ecosystem of deterministic data engines — the "muscles" that do the heavy lifting, no AI required.

```
  ┌──────────┐     event      ┌──────────┐     gate      ┌──────────┐
  │ DB :8100 │ ─────────────► │ETL :3001 │ ◄──────────── │ARGOS:8200│
  │ schema   │                │ pipeline │               │ policy   │
  │ govern.  │                │ runner   │               │ gating   │
  └──────────┘                └──────────┘               └──────────┘
```

- [hale-bopp-db](https://github.com/hale-bopp-data/hale-bopp-db) — Schema governance for PostgreSQL
- **hale-bopp-etl** (this repo) — Config-driven data orchestration
- [hale-bopp-argos](https://github.com/hale-bopp-data/hale-bopp-argos) — Policy gating and quality checks

## License

Apache License 2.0 — see [LICENSE](LICENSE).
