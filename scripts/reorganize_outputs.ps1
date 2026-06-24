# Reorganiza outputs/ segun outputs/README.md (idempotente).
# Ejecutar desde la raiz del repo tras verify_project_context.ps1.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "outputs"

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
}

function Move-IfExists([string]$Name, [string]$DestParent) {
    $Src = Join-Path $Out $Name
    if (-not (Test-Path $Src)) { return }
    $Dst = Join-Path $DestParent $Name
    if (Test-Path $Dst) {
        Write-Host "[skip] ya existe: $Dst"
        return
    }
    Ensure-Dir $DestParent
    Write-Host "[move] $Name -> $DestParent"
    Move-Item -LiteralPath $Src -Destination $DestParent
}

Ensure-Dir (Join-Path $Out "runs")
Ensure-Dir (Join-Path $Out "_archive/dryruns")
Ensure-Dir (Join-Path $Out "_archive/benchmarks")
Ensure-Dir (Join-Path $Out "_archive/reports")

$Runs = @(
    "citylearn_v3_madrl_full_20260615_074011_v4",
    "citylearn_v3_madrl_full_20260618_193234_visible",
    "citylearn_v3_madrl_full_20260618_193336_visible_direct",
    "citylearn_v3_madrl_full_20260618_193542_visible_pwsh",
    "citylearn_v3_madrl_full_20260618_193728_visible_pwsh",
    "colab_madrl_20260618_210509"
)

$Dryruns = @(
    "_dryrun_protocol_test",
    "_dryrun_test",
    "_validate_six_parallel_dryrun",
    "_validate_two_phase_dryrun",
    "codex_dryrun_endat_happo",
    "codex_supervision_dryrun_1ep4steps",
    "codex_supervision_dryrun_20260620",
    "notebook_verify_dryrun",
    "notebook_verify_two_phase_hm",
    "validate_a100_profile_dryrun",
    "validate_four_phase_dryrun",
    "validate_two_phase_dryrun",
    "validate_two_phase_fix",
    "validate_two_phase_parallel",
    "validate_two_phase_parallel2",
    "validation",
    "validation_colab_a100_dry_run",
    "hyperparam_dryrun_test",
    "test_notebook"
)

$Benchmarks = @(
    "benchmark_v2_baseline",
    "citylearn_v2_original_benchmark",
    "citylearn_v2_sb3_smoke",
    "citylearn_v2_sb3_smoke_buffer50k",
    "citylearn_v2_sb3_supervision_smoke",
    "comparison_citylearn_v2_vs_v3_madrl"
)

$Reports = @(
    "defensa_pdf",
    "plan_tesis",
    "thesis",
    "thesis_objective_evidence",
    "supervision_audit_20260620"
)

$RunsDir = Join-Path $Out "runs"
$DryDir = Join-Path $Out "_archive/dryruns"
$BenchDir = Join-Path $Out "_archive/benchmarks"
$RepDir = Join-Path $Out "_archive/reports"

foreach ($n in $Runs) { Move-IfExists $n $RunsDir }
foreach ($n in $Dryruns) { Move-IfExists $n $DryDir }
foreach ($n in $Benchmarks) { Move-IfExists $n $BenchDir }
foreach ($n in $Reports) { Move-IfExists $n $RepDir }

# Rescates HAPPO sueltos en raiz
Get-ChildItem -Path $Out -Directory -Filter "rescued_happo_*" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-IfExists $_.Name $RunsDir
}
Get-ChildItem -Path $Out -Directory -Filter "madrl_v3_*" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-IfExists $_.Name $RunsDir
}

# Informe suelto en raiz
$LooseReport = Join-Path $Out "informe_tecnico_supervision_20260620.json"
if (Test-Path $LooseReport) {
    $Dst = Join-Path $RepDir "informe_tecnico_supervision_20260620.json"
    if (-not (Test-Path $Dst)) {
        Write-Host "[move] informe_tecnico_supervision_20260620.json -> _archive/reports/"
        Move-Item -LiteralPath $LooseReport -Destination $Dst
    }
}

# dataset_cache -> data/cache (insumo, no resultado)
$CacheSrc = Join-Path $Out "dataset_cache"
$CacheDst = Join-Path $Root "data/cache"
if (Test-Path $CacheSrc) {
    Ensure-Dir (Join-Path $Root "data")
    if (-not (Test-Path $CacheDst)) {
        Write-Host "[move] dataset_cache -> data/cache"
        Move-Item -LiteralPath $CacheSrc -Destination $CacheDst
    } else {
        Write-Host "[skip] data/cache ya existe; dataset_cache no movido"
    }
}

# Puntero canonico: corrida v4 completa de referencia
$Canonical = "outputs/runs/citylearn_v3_madrl_full_20260615_074011_v4"
$CanonPath = Join-Path $Root $Canonical
if (Test-Path $CanonPath) {
    $Ptr = Join-Path $Out "latest_visible_training_output_root.txt"
    Set-Content -Path $Ptr -Value $Canonical -Encoding UTF8 -NoNewline
    Write-Host "[update] latest_visible_training_output_root.txt -> $Canonical"
}

Write-Host "[done] Reorganizacion outputs/ completada."
