param()

$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker non trovato nel PATH."
}

try {
  docker compose version | Out-Null
}
catch {
  throw "Docker Compose v2 non disponibile."
}

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example"
}

Write-Host "Installazione base completata. Ora esegui:"
Write-Host "  pwsh ./scripts/bootstrap.ps1 -Mode init"
Write-Host "  pwsh ./scripts/bootstrap.ps1 -Mode up"
