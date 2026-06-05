param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [string]$Scenario = "ALL",
    [int]$Seed = 0,
    [int]$EpisodeTimeSteps = 8760,
    [int]$Episodes = 5,
    [int]$TorchThreads = 12,
    [int]$LiveProgressInterval = 250,
    [switch]$Cuda,
    [switch]$LiveOutput = $true,
    [switch]$NoMonitor
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "CityLearn MADRL full training"
$OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$OutputRootPath = Join-Path $ProjectRoot $OutputRoot
New-Item -ItemType Directory -Path $OutputRootPath -Force | Out-Null
$TranscriptPath = Join-Path $OutputRootPath "visible_launcher_transcript.log"
Start-Transcript -Path $TranscriptPath -Append | Out-Null

Write-Host "CityLearn V3 MADRL full training" -ForegroundColor Cyan
Write-Host ("Project: " + $ProjectRoot)
Write-Host ("OutputRoot: " + $OutputRoot)
Write-Host ("Transcript: " + $TranscriptPath)
Write-Host ""

& .\scripts\verify_project_context.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Project context verification failed. Training was not started." -ForegroundColor Red
    Stop-Transcript | Out-Null
    Read-Host "Press Enter to close"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Launching official training chain..." -ForegroundColor Green
Write-Host ("Command: CityLearn\scripts\launch_citylearn_v3_official_training.ps1 -Scenario {0} -Seed {1} -EpisodeTimeSteps {2} -Episodes {3} -SchemaPath CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json -OutputRoot {4} -TorchThreads {5} -LiveProgressInterval {6} -Cuda:{7} -LiveOutput:{8}" -f $Scenario, $Seed, $EpisodeTimeSteps, $Episodes, $OutputRoot, $TorchThreads, $LiveProgressInterval, [bool]$Cuda, [bool]$LiveOutput)
Write-Host ""

if (-not $NoMonitor) {
    $monitorArgs = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "CityLearn\scripts\monitor_citylearn_v3_official_training.ps1",
        "-OutputRoot",
        $OutputRoot,
        "-IntervalSeconds",
        "10",
        "-LogTail",
        "8"
    )
    $monitorProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $monitorArgs -WorkingDirectory $ProjectRoot -WindowStyle Normal -PassThru
    Write-Host ("Monitor visible PID: " + $monitorProcess.Id) -ForegroundColor Cyan
    Write-Host "El monitor muestra episodio, paso, recompensas, pesos multiobjetivo, KPIs y artefactos." -ForegroundColor Cyan
    Write-Host ""
}

& .\CityLearn\scripts\launch_citylearn_v3_official_training.ps1 `
    -Scenario $Scenario `
    -Seed $Seed `
    -EpisodeTimeSteps $EpisodeTimeSteps `
    -Episodes $Episodes `
    -SchemaPath "CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json" `
    -OutputRoot $OutputRoot `
    -TorchThreads $TorchThreads `
    -LiveProgressInterval $LiveProgressInterval `
    -Cuda:$Cuda `
    -LiveOutput:$LiveOutput
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host ("Training launcher finished with exit code: " + $exitCode) -ForegroundColor Yellow
Write-Host ("OutputRoot: " + $OutputRoot)
Stop-Transcript | Out-Null
Read-Host "Press Enter to close"
exit $exitCode
