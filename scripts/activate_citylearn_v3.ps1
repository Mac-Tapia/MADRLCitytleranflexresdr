Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ActivateScript = Join-Path $ProjectRoot '.venv39-citylearn-v3\Scripts\Activate.ps1'

if (-not (Test-Path -LiteralPath $ActivateScript)) {
    throw "No existe el entorno virtual esperado: $ActivateScript"
}

Set-Location -LiteralPath $ProjectRoot
. $ActivateScript

$env:PYTHONPATH = @(
    $ProjectRoot
    (Join-Path $ProjectRoot 'CityLearn')
) -join [System.IO.Path]::PathSeparator

Write-Host ''
Write-Host 'CityLearn v3 MADRL workspace activo' -ForegroundColor Cyan
Write-Host "Proyecto : $ProjectRoot"
Write-Host "Python   : $((Get-Command python).Source)"
Write-Host "Pwsh     : $($PSVersionTable.PSVersion)"
Write-Host ''
