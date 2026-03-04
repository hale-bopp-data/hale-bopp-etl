# hale-bopp-etl

Config-driven data orchestration engine — YAML pipelines, webhook integration, zero boilerplate.

## Features

- **Declarative Pipelines**: Define ETL workflows in YAML, not Python code
- **Dagster Integration**: Enterprise-grade scheduling and monitoring
- **Webhook Receiver**: FastAPI endpoint for event-driven pipeline triggers
- **Workflow Templates**: Reusable workflow primitives via `workflow_ref`
- **n8n Integration**: HTTP task type for webhook-based orchestration

## Quick Start

```bash
# Docker Compose (includes Dagster UI + PostgreSQL + Webhook receiver)
docker compose up

# Dagster UI: http://localhost:3000
# Webhook API: http://localhost:3001
```

## Pipeline Configuration

Pipelines are defined in `config/orchestration/pipelines.yaml`:

```yaml
pipelines:
  - id: daily_pipeline
    schedule: "0 4 * * *"
    owner: data-platform
    workflow_ref:
      id: daily_etl_n8n
      context:
        endpoint: /webhook/etlb-daily
```

## Testing

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Part of HALE-BOPP

HALE-BOPP is an open-source ecosystem of deterministic data governance engines:

- [hale-bopp-db](https://github.com/hale-bopp-data/hale-bopp-db) — Schema governance
- **hale-bopp-etl** (this repo) — Data orchestration
- [hale-bopp-argos](https://github.com/hale-bopp-data/hale-bopp-argos) — Policy gating

## License

Apache License 2.0 — see [LICENSE](LICENSE).
