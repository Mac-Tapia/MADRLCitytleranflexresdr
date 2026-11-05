<#
.SYNOPSIS
Complete pytest gate with independent inventory, explicit scope and bound cut.
.DESCRIPTION
Fresh collects/runs tests/fresh_training. Repository collects/runs tests once,
including the fresh subset; it does not launch a second native micro fixture.
#>
param(
    [string]$CampaignManifest = '',
    [ValidateSet('Fresh', 'Repository')][string]$Scope = 'Fresh'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $root
$guard = Join-Path $root 'scripts/verify_project_context.ps1'
if (-not (Test-Path -LiteralPath $guard -PathType Leaf)) {
    throw 'Isolated gate copy has no canonical project guard. Integrate before launching this script.'
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $guard
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$python = Join-Path $root '.venv39-citylearn-v3/Scripts/python.exe'
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$gateDir = Join-Path $root 'data/maintenance/gates'
New-Item -ItemType Directory -Force -Path $gateDir | Out-Null
$junit = Join-Path $gateDir "${Scope}_profile_$stamp.xml"
$before = Join-Path $gateDir "${Scope}_profile_$stamp.sources.json"
$collection = Join-Path $gateDir "${Scope}_profile_$stamp.collection.json"
$execution = Join-Path $gateDir "${Scope}_profile_$stamp.execution.json"
$gateJson = Join-Path $gateDir "${Scope}_profile_$stamp.json"
$testScope = if ($Scope -eq 'Repository') { 'tests' } else { 'tests/fresh_training' }
$started = Get-Date
$previousAddopts = $env:PYTEST_ADDOPTS
$previousPlugins = $env:PYTEST_PLUGINS
$previousAutoload = $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
try {
    # Disable both environment and ini addopts, and plugins the cut does not name. Scope
    # is never accepted from a caller-supplied pytest argument list, -k, -m or test path.
    $env:PYTEST_ADDOPTS = ''
    $env:PYTEST_PLUGINS = ''
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
    & $python -B -m uc3m.application.training.gate_report --capture --project-root $root --output $before
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $common = @('-B', '-m', 'pytest', $testScope, '-q', '-p', 'no:cacheprovider', '-o', 'addopts=',
                '-p', 'uc3m.application.training.gate_pytest', "--rootdir=$root", "--confcutdir=$root",
                "--gate-scope=$testScope", "--gate-context=$before")
    $collectArgs = $common + @('--collect-only', '--gate-mode=collection', "--gate-evidence=$collection")
    & $python @collectArgs
    $code = $LASTEXITCODE
    if ($code -eq 0) {
        $runArgs = $common + @('-rfEs', '--gate-mode=execution', "--gate-inventory=$collection",
                               "--gate-evidence=$execution", "--junitxml=$junit")
        & $python @runArgs
        $code = $LASTEXITCODE
    }
    $gateArgs = @('-B', '-m', 'uc3m.application.training.gate_report', '--project-root', $root,
                  '--junit', $junit, '--exit-code', [string]$code, '--source-before', $before,
                  '--collection', $collection, '--output', $gateJson)
    if ($CampaignManifest) { $gateArgs += @('--manifest', $CampaignManifest) }
    & $python @gateArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $result = Get-Content -LiteralPath $gateJson -Raw | ConvertFrom-Json
    $result | Add-Member -NotePropertyName command -NotePropertyValue "python -B -m pytest $testScope (independent collect-only then exact scope run)"
    $result | Add-Member -NotePropertyName started_utc -NotePropertyValue $started.ToUniversalTime().ToString('o')
    $result | Add-Member -NotePropertyName duration_seconds -NotePropertyValue ((Get-Date) - $started).TotalSeconds
    $result | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $gateJson -Encoding UTF8
    if ($CampaignManifest) {
        $acceptance = Join-Path $gateDir "campaign_acceptance_$stamp.json"
        & $python -B -c "import json,sys; from pathlib import Path; from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance; r=verify_fresh_acceptance(Path(sys.argv[1]),gate_report=Path(sys.argv[2])); Path(sys.argv[3]).write_text(json.dumps(r.as_dict(),indent=2),encoding='utf-8'); print('campaign status:',r.status); sys.exit(0 if r.checks.get('gate_clean') else 1)" $CampaignManifest $gateJson $acceptance
        if ($LASTEXITCODE -ne 0) {
            Write-Output "Gate rejected on readback; see $acceptance"
            exit 1
        }
    }
    if (-not $result.software_acceptance) {
        Write-Output "Gate rejected: exit=$code; see $gateJson"
        exit 1
    }
    Write-Output "Complete $Scope software gate passed: $($result.counters.tests) tests; scientific acceptance remains separate."
    exit 0
}
finally {
    if ($null -eq $previousAddopts) { Remove-Item Env:PYTEST_ADDOPTS -ErrorAction SilentlyContinue }
    else { $env:PYTEST_ADDOPTS = $previousAddopts }
    if ($null -eq $previousPlugins) { Remove-Item Env:PYTEST_PLUGINS -ErrorAction SilentlyContinue }
    else { $env:PYTEST_PLUGINS = $previousPlugins }
    if ($null -eq $previousAutoload) { Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD -ErrorAction SilentlyContinue }
    else { $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = $previousAutoload }
}
