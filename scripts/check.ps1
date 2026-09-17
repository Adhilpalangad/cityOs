# One command to lint + test everything that doesn't need Docker running:
# the web app and all three Python services (identity/city-core use an
# in-memory SQLite database for their unit tests, so no Postgres needed).
#
# Usage (from the repo root):
#   .\scripts\check.ps1

$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

$results = @()

function Run-Step {
    param([string]$Name, [scriptblock]$Block)
    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Block
    $passed = ($LASTEXITCODE -eq 0)
    $script:results += [PSCustomObject]@{ Step = $Name; Passed = $passed }
}

Run-Step "web: lint" { npm run lint:web }
Run-Step "web: typecheck" { npm run typecheck:web }
Run-Step "web: test" { npm run test:web }

foreach ($service in @("api-gateway", "identity", "city-core")) {
    $dir = "services/$service"
    Run-Step "$service`: install" { & ".\.venv\Scripts\python.exe" -m pip install -q -e "$dir[dev]" }
    Push-Location $dir
    Run-Step "$service`: lint" { & "..\..\.venv\Scripts\python.exe" -m ruff check . }
    Run-Step "$service`: test" { & "..\..\.venv\Scripts\python.exe" -m pytest -q }
    Pop-Location
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
foreach ($r in $results) {
    if ($r.Passed) {
        Write-Host ("{0,-25} PASS" -f $r.Step) -ForegroundColor Green
    } else {
        Write-Host ("{0,-25} FAIL" -f $r.Step) -ForegroundColor Red
    }
}

$failed = $results | Where-Object { -not $_.Passed }
if ($failed) {
    Write-Host ""
    Write-Host "$($failed.Count) step(s) failed." -ForegroundColor Red
    exit 1
} else {
    Write-Host ""
    Write-Host "All checks passed." -ForegroundColor Green
    exit 0
}
