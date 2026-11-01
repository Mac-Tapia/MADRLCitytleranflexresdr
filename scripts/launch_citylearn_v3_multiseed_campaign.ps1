# Launch CityLearn v3 MADRL multi-seed campaign (4 x 3 x 12)
# Dry-run (manifest only):
#   powershell -ExecutionPolicy Bypass -File scripts\launch_citylearn_v3_multiseed_campaign.ps1 -DryRun
# Execute on Colab/GPU host:
#   powershell -ExecutionPolicy Bypass -File scripts\launch_citylearn_v3_multiseed_campaign.ps1 -Execute -OutputRoot "D:\path\to\out"

param(
    [string]$OutputRoot = "",
    [string]$Seeds = "0-11",
    [int]$Episodes = 50,
    [switch]$DryRun,
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

powershell -ExecutionPolicy Bypass -File "$Repo\scripts\verify_project_context.ps1" | Out-Host

if (-not $OutputRoot) {
    $stamp = Get-Date -Format "yyyyMMdd"
    $OutputRoot = Join-Path $Repo "outputs\madrl_v3_multiseed_$stamp"
}

$pyArgs = @(
    "CityLearn\scripts\launch_citylearn_v3_multiseed_campaign.py",
    "--output-root", $OutputRoot,
    "--seeds", $Seeds,
    "--episodes", "$Episodes"
)

if ($Execute -and -not $DryRun) {
    $pyArgs += "--execute"
} else {
    $pyArgs += "--dry-run"
}

Write-Host "[multiseed] python $($pyArgs -join ' ')"
python @pyArgs
exit $LASTEXITCODE
