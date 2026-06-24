$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "CityLearn MADRL - Reanudacion"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

function Get-LastTrainingOutputRoot {
    if ($env:CITYLEARN_MADRL_OUTPUT_ROOT) {
        return $env:CITYLEARN_MADRL_OUTPUT_ROOT
    }
    $latestPath = "outputs\latest_visible_training_output_root.txt"
    if (Test-Path -LiteralPath $latestPath) {
        $value = (Get-Content -LiteralPath $latestPath -Raw).Trim()
        if ($value) { return $value }
    }
    $candidate = Get-ChildItem -LiteralPath "outputs" -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "official_full_status.json") } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($candidate) { return ("outputs\" + $candidate.Name) }
    return $null
}

$OutputRoot = Get-LastTrainingOutputRoot
if (-not $OutputRoot) {
    Write-Host "No se encontro OutputRoot para reanudar. Lanza primero training_launcher_window.ps1 o define CITYLEARN_MADRL_OUTPUT_ROOT." -ForegroundColor Red
    Read-Host "Presiona Enter"
    exit 1
}
New-Item -ItemType Directory -Path "outputs" -Force | Out-Null
Set-Content -Path "outputs\latest_visible_training_output_root.txt" -Value $OutputRoot -Encoding UTF8

Write-Host "=== CityLearn MADRL v3 - Reanudacion (SkipCompleted) ===" -ForegroundColor Cyan
Write-Host "Cadena: HAPPO/MASAC/MATD3/MAAC x E1,E2,E3 (12 runs)" -ForegroundColor White
Write-Host "Jobs con results.json existente seran saltados automaticamente." -ForegroundColor Yellow
Write-Host "Perfil: efficient | trace compact cada 10 pasos | monitor visible + paralelismo por escenario" -ForegroundColor DarkGray
Write-Host ("OutputRoot: " + $OutputRoot) -ForegroundColor Yellow
Write-Host ""

try {
    & ".\CityLearn\scripts\launch_citylearn_v3_official_training.ps1" `
        -Scenario ALL `
        -Cuda `
        -GpuProfile local4060_fast `
        -ParallelScenarios $true `
        -MaxConcurrentScenarioJobs 2 `
        -MaxConcurrentHeavyJobs 1 `
        -SkipCompleted `
        -ArtifactProfile efficient `
        -TraceRecordInterval 10 `
        -TraceDetail compact `
        -MaxGpuVramGib 8 `
        -GpuVramReserveGib 1.5 `
        -OutputRoot $OutputRoot `
        -SchemaPath "CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json"
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}

Write-Host ""
Write-Host "=== Cadena de entrenamiento finalizada ===" -ForegroundColor Green
Read-Host "Presiona Enter"
