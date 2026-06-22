# Запуск test dashboard (localhost:8765)
# Использует тот же Python, что и pip (Python 3.12)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Pip = (Get-Command pip -ErrorAction SilentlyContinue).Source
if (-not $Pip) {
    Write-Error "pip not found. Install Python 3.10+ and run: pip install -e `".[web]`""
}
$Python = Join-Path (Split-Path (Split-Path $Pip -Parent) -Parent) "python.exe"

Write-Host "Python: $Python"
Write-Host "URL:    http://127.0.0.1:8765"
Write-Host ""
Write-Host "DB:     100.75.41.14 (Tailscale, default) / _llm_connector"
Write-Host "Env:    LLM_DB_USER, LLM_DB_PASSWORD (or .env in repo root)"
Write-Host ""

& $Python -m uvicorn scripts.test_dashboard.app:app --host 127.0.0.1 --port 8765 --reload --reload-include ".env" --reload-include ".env.local"
