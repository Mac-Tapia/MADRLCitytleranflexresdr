# Descarga artefactos reales de Drive (OAuth) y genera figuras de tesis.
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path $PSScriptRoot "..").Path
Set-Location $RepoRoot

& (Join-Path $RepoRoot "scripts\verify_project_context.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$DrivePython = Join-Path $RepoRoot "tools\skills\google-drive-mcp\.venv\Scripts\python.exe"
$VenvPython = Join-Path $RepoRoot ".venv39-citylearn-v3\Scripts\python.exe"

Write-Host "[1/3] Comprobando OAuth Drive..."
& $DrivePython tools\fetch_drive_training_artifacts.py --check-auth
$authOk = ($LASTEXITCODE -eq 0)

if ($authOk) {
    Write-Host "[2/3] Descargando timeseries/trace/checkpoints desde Drive..."
    & $DrivePython tools\fetch_drive_training_artifacts.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "AVISO: OAuth no configurado. Usando mirror local outputs/_drive_madrl/full_data/" -ForegroundColor Yellow
    Write-Host "       Para sincronizar desde Drive ejecuta:" -ForegroundColor Yellow
    Write-Host "       powershell -ExecutionPolicy Bypass -File scripts\setup_google_drive_oauth.ps1" -ForegroundColor Yellow
}

Write-Host "[3/3] Generando figuras (solo datos reales)..."
& $VenvPython tools\generate_drive_thesis_figures.py
exit $LASTEXITCODE
