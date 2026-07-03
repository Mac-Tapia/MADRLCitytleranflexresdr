# Configura OAuth del conector Google Drive MCP (una vez por maquina).
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SkillDir = Join-Path $RepoRoot "tools\skills\google-drive-mcp"
$DataDir = Join-Path $SkillDir "data"
$CredentialsFile = Join-Path $DataDir "credentials.json"
$VenvPython = Join-Path $SkillDir ".venv\Scripts\python.exe"
$AuthScript = Join-Path $SkillDir "scripts\auth_manager.py"

Write-Host "[1/4] Verificando contexto del repositorio..."
& (Join-Path $RepoRoot "scripts\verify_project_context.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/4] Instalando dependencias del MCP..."
& (Join-Path $SkillDir "setup.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $CredentialsFile)) {
    Write-Host ""
    Write-Host "FALTA credentials.json" -ForegroundColor Yellow
    Write-Host "Copia aqui el JSON OAuth Desktop de Google Cloud:"
    Write-Host "  $CredentialsFile"
    Write-Host ""
    Write-Host "Google Cloud Console:"
    Write-Host "  1. APIs y servicios -> Biblioteca -> Google Drive API (habilitar)"
    Write-Host "  2. Pantalla de consentimiento OAuth -> modo Prueba -> anade tu cuenta"
    Write-Host "  3. Credenciales -> Crear credenciales -> ID de cliente OAuth -> Escritorio"
    Write-Host "  4. Descargar JSON -> renombrar a credentials.json en la ruta de arriba"
    Write-Host ""
    Write-Host "Luego vuelve a ejecutar:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\setup_google_drive_oauth.ps1"
    exit 2
}

Write-Host "[3/4] Validando credentials.json..."
& $VenvPython -c @"
import json, sys
from pathlib import Path
p = Path(r'$CredentialsFile')
data = json.loads(p.read_text(encoding='utf-8'))
installed = data.get('installed') or data.get('web')
if not installed or not installed.get('client_id'):
    print('ERROR: credentials.json invalido (falta installed.client_id)')
    sys.exit(1)
print('OK client_id:', installed['client_id'][:24] + '...')
"@ 
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/4] Abriendo navegador para autorizar Google Drive..."
Write-Host "      (Si falla, autoriza manualmente la URL que aparezca en consola)"
& $VenvPython $AuthScript setup
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $VenvPython $AuthScript check
Write-Host ""
Write-Host "Listo. Recarga MCP en Cursor (Settings -> MCP) y prueba:"
Write-Host "  python tools/analyze_drive_folder_sizes.py --scan-outputs"
