<#
.SYNOPSIS
  Retire the closed list of historical outputs R-01..R-07 (T0).

.DESCRIPTION
  Inventory (default) and Plan only write a manifest; nothing is removed.
  Execute -Manifest <plan> asks tools.ops.historical_inventory for a fresh
  go/no-go, re-checks the project context, containment and reparse points
  right before each removal, removes with Remove-Item -LiteralPath only and
  records retirement_result.json next to the plan. No wildcard, git clean,
  reset, LFS purge or remote operation is ever used.

  -ProjectRoot defaults to this repository. Any other root must live under the
  system temp directory (disposable test trees).
#>
param(
    [ValidateSet('Inventory', 'Plan', 'Execute')]
    [string]$Phase = 'Inventory',
    [string]$Manifest,
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $repo
$python = Join-Path $repo '.venv39-citylearn-v3/Scripts/python.exe'
$evidence = Join-Path $repo 'data/maintenance/historicos'

function Assert-Context {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'scripts/verify_project_context.ps1') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Project context check failed; nothing removed.' }
}

function Assert-NoReparseAncestor([string]$Path, [string]$Boundary) {
    $current = [IO.Path]::GetDirectoryName($Path)
    while ($current) {
        if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Ancestor '$current' is a reparse point."
        }
        if ($current -ieq $Boundary) { return }
        $current = [IO.Path]::GetDirectoryName($current)
    }
    throw "Path '$Path' is outside '$Boundary'."
}

if (-not $ProjectRoot) { $ProjectRoot = $repo }
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\')
if ($root -ne $repo.TrimEnd('\')) {
    $temp = (Resolve-Path -LiteralPath ([IO.Path]::GetTempPath())).Path.TrimEnd('\')
    if (-not $root.StartsWith($temp + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "ProjectRoot '$root' is neither this repository nor a disposable temp tree."
    }
}

Assert-Context

if ($Phase -ne 'Execute') {
    if (-not $Manifest) {
        if ($root -ne $repo.TrimEnd('\')) { throw 'Manifest is required for a non-repository root.' }
        $name = if ($Phase -eq 'Plan') { 'retirement_plan.json' } else { 'historical_inventory.json' }
        $Manifest = Join-Path $evidence $name
    }
    & $python -B -m tools.ops.historical_inventory inventory --project-root $root --out $Manifest
    exit $LASTEXITCODE
}

if (-not $Manifest) { throw 'Execute requires -Manifest <retirement_plan.json>.' }
$plan = (Resolve-Path -LiteralPath $Manifest).Path
$verdictText = & $python -B -m tools.ops.historical_inventory verify --plan $plan --project-root $root
if ($LASTEXITCODE -ne 0) { Write-Output $verdictText; throw 'Plan refused by verification; nothing removed.' }
$verdict = $verdictText | ConvertFrom-Json
$outputsRoot = Join-Path $root 'outputs'
$outcomes = @()

foreach ($decision in $verdict.decisions) {
    $now = (Get-Date).ToUniversalTime().ToString('o')
    $reasons = @($decision.reasons)
    if ($decision.decision -ne 'delete') {
        $status = if ($decision.decision -eq 'already_absent') { 'already_absent' } else { 'blocked' }
        $outcomes += [pscustomobject]@{ target_id = $decision.target_id; status = $status; reasons = $reasons; exit_code = 0; at_utc = $now }
        continue
    }
    try {
        Assert-Context
        $target = $decision.absolute_path
        $item = Get-Item -LiteralPath $target -Force
        $full = $item.FullName.TrimEnd('\')
        if (-not $full.StartsWith($outputsRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Target '$full' is outside '$outputsRoot'."
        }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Target '$full' is a reparse point."
        }
        Assert-NoReparseAncestor -Path $full -Boundary $root
        if ($item.PSIsContainer) {
            Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction Stop
        } else {
            Remove-Item -LiteralPath $full -Force -ErrorAction Stop
        }
        $outcomes += [pscustomobject]@{ target_id = $decision.target_id; status = 'deleted'; reasons = $reasons; exit_code = 0; at_utc = $now }
    } catch {
        $outcomes += [pscustomobject]@{ target_id = $decision.target_id; status = 'failed'; reasons = @($reasons + $_.Exception.Message); exit_code = 1; at_utc = $now }
    }
}

$outcomesPath = Join-Path (Split-Path -Parent $plan) 'retirement_outcomes.json'
ConvertTo-Json -InputObject @($outcomes) -Depth 6 | Set-Content -LiteralPath $outcomesPath -Encoding UTF8
& $python -B -m tools.ops.historical_inventory record --plan $plan --project-root $root --outcomes $outcomesPath
exit $LASTEXITCODE
