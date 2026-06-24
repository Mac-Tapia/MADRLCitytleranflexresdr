# Instala el MCP de NotebookLM para este repositorio
$ErrorActionPreference = "Stop"
$SkillDir = (Resolve-Path $PSScriptRoot).Path

Write-Host "Instalando NotebookLM MCP en: $SkillDir"

$env:PYTHONIOENCODING = "utf-8"
$venvPython = Join-Path $SkillDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $SkillDir ".venv")
    & (Join-Path $SkillDir ".venv\Scripts\pip.exe") install -r (Join-Path $SkillDir "requirements.txt")
    & $venvPython -m patchright install chrome
}

Write-Host ""
Write-Host "Listo. Reinicia Cursor o recarga MCP en Settings -> MCP."
Write-Host "Luego pide al agente: ejecuta setup_auth para login con Google."
