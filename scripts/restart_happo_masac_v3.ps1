$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

$OutputRoot = "outputs\citylearn_v3_madrl_full_20260613_010234"
$OutputRootFull = Join-Path $ProjectRoot $OutputRoot

# ── Guardar referencia para el monitor ──────────────────────────────────────
New-Item -ItemType Directory -Path "outputs" -Force | Out-Null
Set-Content -Path "outputs\latest_visible_training_output_root.txt" -Value $OutputRoot -Encoding UTF8

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  RE-RUN HAPPO + MASAC con perfil v3 (EV SOC reforzado + V2G)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  OutputRoot : $OutputRoot"
Write-Host "  Perfil     : *_unified_comparable_v3 (ev_weight=0.25, bug SOC corregido)"
Write-Host "  Schema     : V2G habilitado para camionetas (31 chargers bidireccionales)"
Write-Host ""

# ── Verificar que no haya training activo ──────────────────────────────────
$activePython = Get-Process python* -ErrorAction SilentlyContinue | Where-Object { $_.WorkingSet -gt 10MB }
if ($activePython) {
    Write-Host "ADVERTENCIA: Hay procesos Python activos con memoria significativa:" -ForegroundColor Yellow
    $activePython | ForEach-Object { Write-Host "  PID $($_.Id)  RAM $([math]::Round($_.WorkingSet/1MB))MB  CPU $([math]::Round($_.CPU))s" }
    $resp = Read-Host "¿Continuar de todas formas? (s/N)"
    if ($resp -notmatch '^[sS]') {
        Write-Host "Cancelado." -ForegroundColor Red; exit 0
    }
}

# ── Eliminar resultados v2 de HAPPO y MASAC ────────────────────────────────
Write-Host "Eliminando resultados v2 de HAPPO y MASAC..." -ForegroundColor Yellow
foreach ($alg in @("happo", "masac")) {
    $algDir = Join-Path $OutputRootFull $alg
    if (Test-Path $algDir) {
        Remove-Item -Recurse -Force $algDir
        Write-Host "  Eliminado: $alg\" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Lanzando HAPPO + MASAC v3 (MATD3 y MAAC seran saltados via SkipCompleted)..." -ForegroundColor Green
Write-Host ""

& "CityLearn\scripts\launch_citylearn_v3_official_training.ps1" `
    -Scenario ALL `
    -Seed 0 `
    -EpisodeTimeSteps 8760 `
    -Episodes 5 `
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
    -SkipCompleted `
    -MasacBufferSize 2 `
    -MasacMaxReplayBufferGib 3 `
    -MasacPreloadBatchDevice auto

$exitCode = $LASTEXITCODE
Write-Host ""
Write-Host "Re-run HAPPO+MASAC v3 finalizado con codigo: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { 'Green' } else { 'Red' })
Read-Host "Presiona Enter para cerrar"
exit $exitCode
