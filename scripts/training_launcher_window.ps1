$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "CityLearn MADRL Training"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot
$OutputRoot = if ($env:CITYLEARN_MADRL_OUTPUT_ROOT) {
    $env:CITYLEARN_MADRL_OUTPUT_ROOT
}
else {
    "outputs\citylearn_v3_madrl_full_" + (Get-Date -Format "yyyyMMdd_HHmmss")
}
New-Item -ItemType Directory -Path "outputs" -Force | Out-Null
Set-Content -Path "outputs\latest_visible_training_output_root.txt" -Value $OutputRoot -Encoding UTF8

Write-Host "=== CityLearn MADRL v3 - Training Visible ===" -ForegroundColor Cyan
Write-Host "Cadena: HAPPO/MASAC/MATD3/MAAC x E1,E2,E3 (12 runs)" -ForegroundColor White
Write-Host "Perfil: efficient | trace compact cada 10 pasos | modo visible secuencial" -ForegroundColor DarkGray
Write-Host ("OutputRoot: " + $OutputRoot) -ForegroundColor Yellow
Write-Host ""

try {
    & ".\CityLearn\scripts\launch_citylearn_v3_official_training.ps1" `
        -Scenario ALL `
        -Cuda `
        -GpuProfile local4060_fast `
        -LiveOutput `
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
Write-Host "=== Training finalizado ===" -ForegroundColor Green
Read-Host "Presiona Enter"
