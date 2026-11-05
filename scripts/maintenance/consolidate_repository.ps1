<#
.SYNOPSIS
  Plan or execute the T12 consolidation of duplicate files (one canonical per role).

.DESCRIPTION
  Plan (default) only writes canonicalization_plan.json (and the inventory next
  to it); nothing is removed.
  Execute -Plan <plan> asks tools.ops.audit_duplicate_files verify for a fresh
  go/no-go, then, right before each removal, re-checks the project context,
  containment inside the root, reparse points and the SHA-256 of the file.
  Only regular files listed in removed_paths with coverage_verified=true are
  removed, with Remove-Item -LiteralPath. No wildcard, basename match, git
  clean, reset or remote operation is used. Outcomes are written to
  consolidation_result.json next to the plan.

  -ProjectRoot defaults to this repository. Any other root must live under the
  system temp directory (disposable test trees).
#>
param(
    [ValidateSet('Plan', 'Execute')]
    [string]$Phase = 'Plan',
    [string]$Plan,
    [string]$Coverage,
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.TrimEnd('\')
Set-Location -LiteralPath $repo
$python = Join-Path $repo '.venv39-citylearn-v3/Scripts/python.exe'

function Assert-Context {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'scripts/verify_project_context.ps1') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Project context check failed; nothing removed.' }
}

if (-not $ProjectRoot) { $ProjectRoot = $repo }
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\')
if ($root -ne $repo) {
    $temp = (Resolve-Path -LiteralPath ([IO.Path]::GetTempPath())).Path.TrimEnd('\')
    if (-not $root.StartsWith($temp + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "ProjectRoot '$root' is neither this repository nor a disposable temp tree."
    }
}
$registry = Join-Path $root 'governance/repository_layout.yaml'

Assert-Context

if ($Phase -eq 'Plan') {
    if (-not $Plan) {
        if ($root -ne $repo) { throw 'Plan path is required for a non-repository root.' }
        $Plan = Join-Path $repo 'data/maintenance/repository_layout/canonicalization_plan.json'
    }
    $inventory = Join-Path (Split-Path -Parent $Plan) 'duplicate_inventory.json'
    $arguments = @('-B', '-m', 'tools.ops.audit_duplicate_files', 'plan', '--root', $root,
                   '--registry', $registry, '--out', $Plan, '--inventory-out', $inventory)
    if ($Coverage) { $arguments += @('--coverage', (Resolve-Path -LiteralPath $Coverage).Path) }
    & $python @arguments
    exit $LASTEXITCODE
}

if (-not $Plan) { throw 'Execute requires -Plan <canonicalization_plan.json>.' }
$planPath = (Resolve-Path -LiteralPath $Plan).Path
$verdictText = & $python -B -m tools.ops.audit_duplicate_files verify --plan $planPath --root $root --registry $registry
if ($LASTEXITCODE -ne 0) { Write-Output $verdictText; throw 'Plan refused by verification; nothing removed.' }
$decisions = @((($verdictText -join "`n") | ConvertFrom-Json).decisions)
$outcomes = @()

foreach ($decision in $decisions) {
    $now = (Get-Date).ToUniversalTime().ToString('o')
    $reasons = @($decision.reasons)
    if ($decision.decision -ne 'delete') {
        $outcomes += [pscustomobject]@{ path = $decision.path; status = 'blocked'; reasons = $reasons; at_utc = $now }
        continue
    }
    try {
        Assert-Context
        $item = Get-Item -LiteralPath $decision.absolute_path -Force
        $full = $item.FullName.TrimEnd('\')
        if (-not $full.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Target '$full' is outside '$root'."
        }
        if ($item.PSIsContainer) { throw "Target '$full' is a directory; only files are removed." }
        $cursor = $item
        while ($cursor -and $cursor.FullName.TrimEnd('\').Length -gt $root.Length) {
            if ($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Target '$full' is or lies under a reparse point."
            }
            $cursor = if ($cursor.PSIsContainer) { $cursor.Parent } else { $cursor.Directory }
        }
        # .NET SHA-256 also works when Windows PowerShell is launched by Python
        # with a PowerShell 7 PSModulePath where Get-FileHash is unavailable.
        $hashStream = [IO.File]::OpenRead($full)
        $hashAlgorithm = [Security.Cryptography.SHA256]::Create()
        try {
            $hash = ([BitConverter]::ToString($hashAlgorithm.ComputeHash($hashStream))).Replace('-', '').ToLowerInvariant()
        } finally {
            $hashStream.Dispose()
            $hashAlgorithm.Dispose()
        }
        if ($hash -ne $decision.sha256) { throw "Target '$full' changed since verification." }
        Remove-Item -LiteralPath $full -Force -ErrorAction Stop
        $outcomes += [pscustomobject]@{ path = $decision.path; status = 'deleted'; reasons = $reasons; sha256 = $hash; at_utc = $now }
    } catch {
        $outcomes += [pscustomobject]@{ path = $decision.path; status = 'failed'; reasons = @($reasons + $_.Exception.Message); at_utc = $now }
    }
}

$result = [pscustomobject]@{
    schema_version = 1
    plan = $planPath
    project_root = $root
    outcomes = @($outcomes)
}
$resultPath = Join-Path (Split-Path -Parent $planPath) 'consolidation_result.json'
ConvertTo-Json -InputObject $result -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
if (@($outcomes | Where-Object { $_.status -eq 'failed' }).Count -gt 0) { exit 1 }
exit 0
