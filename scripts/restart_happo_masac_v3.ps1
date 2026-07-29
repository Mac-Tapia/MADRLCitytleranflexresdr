$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

# Sesion definitiva v4 — nueva sesion con timestamp al momento de ejecucion.
# Entrena TODOS los algoritmos (HAPPO, MASAC, MATD3, MAAC) con perfil v4:
#   · bess_cycle_weight=0.10  (penalty ciclado BESS, Wan et al. 2022)
#   · ev_urgency_hours=8.0    (ventana urgencia EV 4h->8h, Pinto et al. 2022)
#   · ev_departure_deficit_weight=0.70
#   · ev_idle_deficit_weight=0.25
#   · ev_type_code fix activo (insertion order, commit 2ee72c72)
$SessionStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputRoot   = "outputs\citylearn_v3_madrl_full_${SessionStamp}_v4"

# ── Guardar referencia para el monitor ──────────────────────────────────────
New-Item -ItemType Directory -Path "outputs" -Force | Out-Null
Set-Content -Path "outputs\latest_visible_training_output_root.txt" -Value $OutputRoot -Encoding UTF8

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ENTRENAMIENTO DEFINITIVO v4 — TODOS LOS ALGORITMOS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Sesion  : $OutputRoot"
Write-Host "  Perfil  : *_unified_comparable_v4"
Write-Host "  Fix     : ev_type_code (insertion order) + BESS cycling penalty"
Write-Host "  EV      : urgency_hours=8h, departure_weight=0.70"
Write-Host ""

# ── Verificar que no haya training activo ──────────────────────────────────
$activePython = Get-Process python* -ErrorAction SilentlyContinue |
    Where-Object { $_.WorkingSet -gt 100MB }
if ($activePython) {
    Write-Host "ADVERTENCIA: Hay procesos Python con alto consumo de RAM:" -ForegroundColor Yellow
    $activePython | ForEach-Object {
        Write-Host "  PID $($_.Id)  RAM $([math]::Round($_.WorkingSet/1MB))MB  CPU $([math]::Round($_.CPU))s"
    }
    $resp = Read-Host "Espera a que el MAAC E3 actual termine. Continuar de todas formas? (s/N)"
    if ($resp -notmatch '^[sS]') {
        Write-Host "Cancelado." -ForegroundColor Red; exit 0
    }
}

Write-Host "Lanzando HAPPO -> MASAC -> MATD3 -> MAAC (3 escenarios cada uno)..." -ForegroundColor Green
Write-Host ""

& "CityLearn\scripts\launch_citylearn_v3_official_training.ps1" `
    -Scenario ALL `
    -Seed 0 `
    -EpisodeTimeSteps 8760 `
    -Episodes 50 `
    -SchemaPath "CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json" `
    -OutputRoot $OutputRoot `
    -ArtifactProfile efficient `
    -TraceRecordInterval 10 `
    -TraceDetail compact `
    -GpuProfile local4060_fast `
    -MaxGpuVramGib 0 `
    -GpuVramReserveGib 1.5 `
    -CudaMemoryFraction 0 `
    -ParallelScenarios:$true `
    -MaxConcurrentScenarioJobs 2 `
    -MaxConcurrentHeavyJobs 1 `
    -Cuda `
    -LiveOutput:$false `
    -StartFromAlgorithm happo `
    -MasacBufferSize 2 `
    -MasacMaxReplayBufferGib 3 `
    -MasacPreloadBatchDevice auto

$exitCode = $LASTEXITCODE
Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "Entrenamiento definitivo v4 COMPLETADO." -ForegroundColor Green
    Write-Host "Sesion: $OutputRoot" -ForegroundColor Green
} else {
    Write-Host "Entrenamiento finalizado con codigo: $exitCode" -ForegroundColor Red
}
Read-Host "Presiona Enter para cerrar"
exit $exitCode
