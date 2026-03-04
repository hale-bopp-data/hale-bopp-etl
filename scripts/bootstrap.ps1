param(
  [ValidateSet("init", "up", "down", "restart")]
  [string]$Mode = "up"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example"
}

if ($Mode -eq "init") {
  docker compose up airflow-init
  exit 0
}

if ($Mode -eq "up") {
  docker compose up -d
  exit 0
}

if ($Mode -eq "down") {
  docker compose down
  exit 0
}

if ($Mode -eq "restart") {
  docker compose down
  docker compose up -d
  exit 0
}
