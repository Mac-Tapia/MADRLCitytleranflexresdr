[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python = Join-Path $ProjectRoot '.venv39-citylearn-v3\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python 3.9 environment not found: $Python"
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot 'scripts\verify_project_context.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m pytest `
    (Join-Path $ProjectRoot 'tests\unit\governance\test_open_source_policy.py') `
    (Join-Path $ProjectRoot 'tests\ops\test_capture_modernization_baseline.py') `
    (Join-Path $ProjectRoot 'tests\ops\test_open_source_dependency_audit.py') `
    (Join-Path $ProjectRoot 'tests\ops\test_closed_services_and_secrets.py') `
    (Join-Path $ProjectRoot 'tests\ops\test_sbom.py') `
    (Join-Path $ProjectRoot 'tests\contract\test_dependency_roles.py') `
    (Join-Path $ProjectRoot 'tests\contract\test_spec_kit_consistency.py') `
    (Join-Path $ProjectRoot 'tests\contract\test_foundation_manifests.py') `
    -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python (Join-Path $ProjectRoot 'tools\ops\capture_modernization_baseline.py') `
    --output (Join-Path $ProjectRoot 'data\audits\modernization_baseline.json')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python (Join-Path $ProjectRoot 'tools\ops\audit_open_source_dependencies.py') `
    --output (Join-Path $ProjectRoot 'data\audits\open_source_dependency_manifest.json')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python (Join-Path $ProjectRoot 'tools\ops\generate_sbom.py') `
    --output (Join-Path $ProjectRoot 'data\audits\sbom.cdx.json')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python (Join-Path $ProjectRoot 'tools\ops\audit_closed_services_and_secrets.py') `
    --output (Join-Path $ProjectRoot 'data\audits\closed_services_and_secrets.json')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$GateJson = & $Python -c "import json; from pathlib import Path; from uc3m.governance.foundation import validate_foundation_manifests; print(json.dumps(validate_foundation_manifests(Path(r'$ProjectRoot')), sort_keys=True))"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$Gate = $GateJson | ConvertFrom-Json

Write-Host ("Foundation gate: status={0}; schemas={1}; closed_services={2}; dependencies={3}; blockers={4}" -f `
    $Gate.status, $Gate.schemas_valid, $Gate.closed_services_ok, $Gate.dependencies_ok, $Gate.dependency_blocker_count)

if (-not $Gate.ready) { exit 1 }
exit 0
