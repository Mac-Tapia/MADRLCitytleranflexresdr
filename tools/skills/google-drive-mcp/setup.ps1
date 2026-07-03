# Instala el MCP de Google Drive para este repositorio
$ErrorActionPreference = "Stop"
$SkillDir = (Resolve-Path $PSScriptRoot).Path

Write-Host "Instalando Google Drive MCP en: $SkillDir"

$env:PYTHONIOENCODING = "utf-8"
$venvPython = Join-Path $SkillDir ".venv\Scripts\python.exe"
$dataDir = Join-Path $SkillDir "data"
$credentialsFile = Join-Path $dataDir "credentials.json"

if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $SkillDir ".venv")
    & (Join-Path $SkillDir ".venv\Scripts\pip.exe") install -r (Join-Path $SkillDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "pip install fallo. Reintenta: tools\skills\google-drive-mcp\.venv\Scripts\pip.exe install -r tools\skills\google-drive-mcp\requirements.txt"
    }
}

if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

Write-Host ""
if (-not (Test-Path $credentialsFile)) {
    Write-Host "ATENCION: Coloca credentials.json en:"
    Write-Host "  $credentialsFile"
    Write-Host ""
    Write-Host "Pasos en Google Cloud Console:"
    Write-Host "  1. Crear proyecto (o usar existente)"
    Write-Host "  2. APIs y servicios -> Biblioteca -> habilitar Google Drive API"
    Write-Host "  3. Credenciales -> Crear credenciales -> ID de cliente OAuth"
    Write-Host "  4. Tipo: Aplicacion de escritorio"
    Write-Host "  5. Descargar JSON y renombrar a credentials.json"
    Write-Host ""
}

Write-Host "Listo. Reinicia Cursor o recarga MCP en Settings -> MCP."
Write-Host "Luego pide al agente: ejecuta setup_auth para login con Google."
