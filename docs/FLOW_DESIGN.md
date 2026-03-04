# Flow Design

Documento di disegno dei flow operativi e funzionali.

## 1) Bootstrapping e installazione
```mermaid
sequenceDiagram
  participant U as User
  participant PS as install.ps1
  participant BS as bootstrap.ps1
  participant DC as Docker Compose
  participant AF as Airflow Init

  U->>PS: pwsh ./scripts/install.ps1
  PS->>PS: verifica docker + compose
  PS->>PS: genera .env se assente

  U->>BS: pwsh ./scripts/bootstrap.ps1 -Mode init
  BS->>DC: up airflow-init
  DC->>AF: install requirements + db migrate + admin user

  U->>BS: pwsh ./scripts/bootstrap.ps1 -Mode up
  BS->>DC: up -d stack runtime
```

## 2) DAG generation flow (config-driven)
```mermaid
sequenceDiagram
  participant AF as Airflow Parser
  participant ED as dags/expose_dags.py
  participant CL as config_loader
  participant SC as schema.validate
  participant DF as dag_factory
  participant YAML as pipelines.yaml

  AF->>ED: load DAG module
  ED->>YAML: read config path
  ED->>CL: load_orchestration_config()
  CL-->>ED: config dict
  ED->>DF: build_dags_from_config(config)
  DF->>SC: validate_pipeline_config(config)
  SC-->>DF: valid/errors
  DF-->>ED: DAG objects
  ED-->>AF: globals().update(dags)
```

## 3) Runtime flow: daily pipeline
```mermaid
flowchart LR
  A[start] --> B[extract_step bash]
  B --> C[transform_step python]
  C --> D[notify_n8n http]
  D --> E[end]
```

## 4) Runtime flow: event pipeline
```mermaid
flowchart LR
  A[start] --> B[event_guard bash]
  B --> C[event_transform python]
  C --> D[callback_n8n http]
  D --> E[end]
```

## 5) Master orchestration flow
```mermaid
flowchart TB
  S[start] --> T1[Trigger etlb_daily_pipeline]
  S --> T2[Trigger etlb_event_pipeline]
  T1 --> E[end]
  T2 --> E
```

## 6) Integrazione n8n (target)
- Airflow -> n8n: callback via `SimpleHttpOperator` con connessione `n8n_default`.
- n8n -> Airflow: trigger DAG via Airflow REST API.
- Contratto payload consigliato:

```json
{
  "correlation_id": "uuid",
  "pipeline": "etlb_daily_pipeline",
  "status": "completed|failed",
  "run_id": "airflow_run_id",
  "timestamp": "ISO-8601"
}
```

## 7) Failure and recovery flow
```mermaid
flowchart LR
  F[Task failure] --> R{Retries available?}
  R -- Yes --> X[Automatic retry]
  R -- No --> N[Mark failed]
  N --> C[Callback n8n failure channel]
  N --> O[Operator triage in Airflow UI]
```
