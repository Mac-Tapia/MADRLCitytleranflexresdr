$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $projectRoot
& powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$python = Join-Path $projectRoot '.venv39-citylearn-v3/Scripts/python.exe'
$report = Join-Path $projectRoot 'outputs/orchestration-tests.xml'
& $python -m pytest tests CityLearn/tests/test_incremental_resume_persistence.py CityLearn/tests/test_citylearn_v3_job_completion.py CityLearn/tests/test_internal_refactor_parity.py --junitxml=$report
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
[xml]$junit = Get-Content -LiteralPath $report -Raw
$skipped = 0
foreach ($suite in $junit.testsuites.testsuite) { $skipped += [int]$suite.skipped }
if ($skipped -gt 0) { Write-Error "Acceptance rejected: $skipped skipped tests"; exit 1 }
& $python -m tools.ops.audit_modular_training
exit $LASTEXITCODE
