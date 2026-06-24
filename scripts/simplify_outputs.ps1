# Aplana outputs/: un run canonico en raiz, _archive/ sin subcarpetas, dataset fuera.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "outputs"
$Archive = Join-Path $Out "_archive"
$Canonical = "citylearn_v3_madrl_full_20260615_074011_v4"

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
}

function Move-IfExists([string]$Src, [string]$Dst) {
    if (-not (Test-Path $Src)) { return }
    if (Test-Path $Dst) {
        Write-Host "[skip] existe: $Dst"
        return
    }
    Ensure-Dir (Split-Path $Dst -Parent)
    Write-Host "[move] $(Split-Path $Src -Leaf) -> $(Split-Path $Dst -Parent)"
    Move-Item -LiteralPath $Src -Destination $Dst
}

Ensure-Dir $Archive

# 1) Aplanar _archive/dryruns, benchmarks, reports -> _archive/
foreach ($sub in @("dryruns", "benchmarks", "reports")) {
    $subPath = Join-Path $Archive $sub
    if (-not (Test-Path $subPath)) { continue }
    Get-ChildItem -LiteralPath $subPath | ForEach-Object {
        Move-IfExists $_.FullName (Join-Path $Archive $_.Name)
    }
    if ((Get-ChildItem -LiteralPath $subPath -Force | Measure-Object).Count -eq 0) {
        Remove-Item -LiteralPath $subPath -Force -Recurse
        Write-Host "[rm] vacia: _archive/$sub"
    }
}

# 2) runs/ -> raiz (canonico) o _archive (resto)
$RunsDir = Join-Path $Out "runs"
if (Test-Path $RunsDir) {
    Get-ChildItem -LiteralPath $RunsDir -Directory | ForEach-Object {
        $name = $_.Name
        if ($name -eq $Canonical) {
            Move-IfExists $_.FullName (Join-Path $Out $name)
        } else {
            Move-IfExists $_.FullName (Join-Path $Archive $name)
        }
    }
    if ((Get-ChildItem -LiteralPath $RunsDir -Force | Measure-Object).Count -eq 0) {
        Remove-Item -LiteralPath $RunsDir -Force -Recurse
        Write-Host "[rm] vacia: runs/"
    }
}

# 3) dataset_audit -> data/dataset_audit
$AuditSrc = Join-Path $Out "dataset_audit"
$AuditDst = Join-Path $Root "data/dataset_audit"
if (Test-Path $AuditSrc) {
    if (-not (Test-Path $AuditDst)) {
        Ensure-Dir (Join-Path $Root "data")
        Write-Host "[move] dataset_audit -> data/dataset_audit"
        Move-Item -LiteralPath $AuditSrc -Destination $AuditDst
    } else {
        Write-Host "[skip] data/dataset_audit ya existe"
    }
}

# 4) dataset_cache fuera de outputs
$CacheSrc = Join-Path $Out "dataset_cache"
$CacheDst = Join-Path $Root "data/cache"
if (Test-Path $CacheSrc) {
    Ensure-Dir $CacheDst
    Get-ChildItem -LiteralPath $CacheSrc -File | ForEach-Object {
        $dstFile = Join-Path $CacheDst $_.Name
        if (-not (Test-Path $dstFile)) {
            Move-Item -LiteralPath $_.FullName -Destination $dstFile
        }
    }
    if ((Get-ChildItem -LiteralPath $CacheSrc -Force | Measure-Object).Count -eq 0) {
        Remove-Item -LiteralPath $CacheSrc -Force -Recurse
        Write-Host "[rm] dataset_cache/"
    }
}

# 5) Punteros
$CanonRel = "outputs/$Canonical"
if (Test-Path (Join-Path $Root $CanonRel)) {
    Set-Content -Path (Join-Path $Out "latest_visible_training_output_root.txt") -Value $CanonRel -Encoding UTF8 -NoNewline
    Set-Content -Path (Join-Path $Out "latest_colab_output_root.txt") -Value $CanonRel -Encoding UTF8 -NoNewline
    Write-Host "[update] punteros -> $CanonRel"
}

Write-Host "[done] outputs/ simplificado."
