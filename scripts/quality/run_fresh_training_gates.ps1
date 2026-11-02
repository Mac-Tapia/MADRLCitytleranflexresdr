<#
.SYNOPSIS
  Strict acceptance gate of the fresh campaign (T10).

.DESCRIPTION
  Runs the fresh profile (tests/fresh_training) with no historical data. Any
  skip, xfail, xpass, error or failure rejects the gate. Records the command,
  duration, exit code, counters and the junit hash under
  data/maintenance/gates/. Passing this gate is software acceptance only; it
  is never scientific acceptance of the campaign.
#>
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $root
& powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$python = Join-Path $root '.venv39-citylearn-v3/Scripts/python.exe'
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$gateDir = Join-Path $root 'data/maintenance/gates'
New-Item -ItemType Directory -Force -Path $gateDir | Out-Null
$junit = Join-Path $gateDir "fresh_profile_$stamp.xml"
$started = Get-Date
& $python -B -m pytest tests/fresh_training -q -p no:cacheprovider -rfEs "--junitxml=$junit"
$code = $LASTEXITCODE
$seconds = [int]((Get-Date) - $started).TotalSeconds

[xml]$report = Get-Content -LiteralPath $junit -Raw
$totals = @{ tests = 0; failures = 0; errors = 0; skipped = 0 }
foreach ($suite in $report.testsuites.testsuite) {
    foreach ($key in @('tests', 'failures', 'errors', 'skipped')) { $totals[$key] += [int]$suite.$key }
}
$passed = ($code -eq 0) -and ($totals.failures -eq 0) -and ($totals.errors -eq 0) -and ($totals.skipped -eq 0)
$result = [ordered]@{
    schema_version = 1
    command = "python -B -m pytest tests/fresh_training -q -p no:cacheprovider -rfEs"
    started_utc = $started.ToUniversalTime().ToString('o')
    duration_seconds = $seconds
    exit_code = $code
    counters = $totals
    junit = "data/maintenance/gates/fresh_profile_$stamp.xml"
    junit_sha256 = (Get-FileHash -LiteralPath $junit -Algorithm SHA256).Hash.ToLower()
    software_acceptance = $passed
    scientific_acceptance = $false
}
$gateJson = Join-Path $gateDir "fresh_profile_$stamp.json"
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $gateJson -Encoding UTF8
# Campaign acceptance from its own artifacts; software and scientific answers stay separate.
$manifest = Join-Path $root 'outputs/campaigns/iquitos_v1/campaign_manifest.json'
if (Test-Path -LiteralPath $manifest) {
    $acceptance = Join-Path $gateDir "campaign_acceptance_$stamp.json"
    & $python -B -c "import json,sys; from pathlib import Path; from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance as v; r=v(Path(sys.argv[1]), gate_report=Path(sys.argv[2])); Path(sys.argv[3]).write_text(json.dumps(r.as_dict(), indent=2), encoding='utf-8'); print('campaign status:', r.status)" $manifest $gateJson $acceptance
}
if (-not $passed) { Write-Error "Fresh gate rejected: exit=$code counters=$($totals | ConvertTo-Json -Compress)"; exit 1 }
Write-Output "Fresh gate passed: $($totals.tests) tests, 0 skipped/failed."
exit 0
