# Common Utilities

Workflow riusabili per ETLBELVISO.

## Workflow disponibili
- `daily_etl_n8n`
- `event_etl_n8n`
- `quality_gate`

## Uso in `pipelines.yaml`
Esempio:

```yaml
pipelines:
  - id: my_daily_pipeline
    schedule: "0 6 * * *"
    workflow_ref:
      id: daily_etl_n8n
      context:
        endpoint: /webhook/custom-daily
```

`workflow_ref` sostituisce i task manuali della pipeline con i task predefiniti del workflow scelto.
