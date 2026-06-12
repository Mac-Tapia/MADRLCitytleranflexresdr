param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [string]$Scenario = "ALL",
    [int]$Seed = 0,
    [int]$EpisodeTimeSteps = 8760,
    [int]$Episodes = 5,
    [int]$TorchThreads = 12,
    [int]$LiveProgressInterval = 250,
    [ValidateSet("full", "efficient", "minimal")]
    [string]$ArtifactProfile = "efficient",
    [int]$TraceRecordInterval = 10,
    [ValidateSet("full", "compact")]
    [string]$TraceDetail = "compact",
    [ValidateSet("local4060_fast", "local4060", "balanced", "conservative", "aws")]
    [string]$GpuProfile = "local4060_fast",
    [double]$MaxGpuVramGib = 0,
    [double]$GpuVramReserveGib = 1.5,
    [ValidateRange(0.0, 1.0)]
    [double]$CudaMemoryFraction = 0,
    [bool]$ParallelScenarios = $true,
    [ValidateRange(1, 16)]
    [int]$MaxConcurrentScenarioJobs = 2,
    [ValidateRange(1, 16)]
    [int]$MaxConcurrentHeavyJobs = 1,
    [switch]$Cuda,
    [bool]$LiveOutput = $true,
    [switch]$NoMonitor,
    [switch]$SelfLaunched   # uso interno: evita re-lanzamiento recursivo
)

$ErrorActionPreference = "Stop"
$PowerShellExe = "powershell.exe"
$PwshCommand = Get-Command pwsh.exe -ErrorAction SilentlyContinue
if ($PwshCommand) {
    $PowerShellExe = $PwshCommand.Source
}

# ── Auto-relanzamiento en ventana independiente ───────────────────────────────
# Si NO fue lanzado como ventana independiente, se re-lanza en una nueva
# ventana PowerShell con -WindowStyle Normal y luego sale.
# Esto asegura que el training corre en su propia ventana: si el usuario
# cierra la terminal original, el entrenamiento continua.
if (-not $SelfLaunched) {
    $selfScript = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { Join-Path $PSScriptRoot "run_citylearn_v3_full_training_visible.ps1" }
    $selfArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", $selfScript,
        "-OutputRoot", $OutputRoot,
        "-Scenario", $Scenario,
        "-Seed", "$Seed",
        "-EpisodeTimeSteps", "$EpisodeTimeSteps",
        "-Episodes", "$Episodes",
        "-TorchThreads", "$TorchThreads",
        "-LiveProgressInterval", "$LiveProgressInterval",
        "-ArtifactProfile", $ArtifactProfile,
        "-TraceRecordInterval", "$TraceRecordInterval",
        "-TraceDetail", $TraceDetail,
        "-GpuProfile", $GpuProfile,
        "-MaxGpuVramGib", "$MaxGpuVramGib",
        "-GpuVramReserveGib", "$GpuVramReserveGib",
        "-CudaMemoryFraction", "$CudaMemoryFraction",
        "-ParallelScenarios", "$ParallelScenarios",
        "-MaxConcurrentScenarioJobs", "$MaxConcurrentScenarioJobs",
        "-MaxConcurrentHeavyJobs", "$MaxConcurrentHeavyJobs",
        "-SelfLaunched"
    )
    if ($Cuda)      { $selfArgs += "-Cuda" }
    $selfArgs += @("-LiveOutput", "$LiveOutput")
    if ($NoMonitor) { $selfArgs += "-NoMonitor" }

    $projectRoot = Split-Path -Parent $PSScriptRoot
    $trainingWin = Start-Process $PowerShellExe `
        -ArgumentList $selfArgs `
        -WorkingDirectory $projectRoot `
        -WindowStyle Normal `
        -PassThru

    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  ENTRENAMIENTO INICIADO EN VENTANA INDEPENDIENTE" -ForegroundColor Green
    Write-Host "  PID ventana entrenamiento: $($trainingWin.Id)" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Puedes cerrar ESTA ventana." -ForegroundColor Yellow
    Write-Host "  NO cierres la ventana del entrenamiento hasta completar los 12 runs." -ForegroundColor Red
    Write-Host ""
    exit 0
}

$Host.UI.RawUI.WindowTitle = "CityLearn MADRL full training"
$OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$OutputRootPath = Join-Path $ProjectRoot $OutputRoot
New-Item -ItemType Directory -Path $OutputRootPath -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $ProjectRoot "outputs") -Force | Out-Null
Set-Content -Path (Join-Path $ProjectRoot "outputs\latest_visible_training_output_root.txt") -Value $OutputRoot -Encoding UTF8
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
Write-Host ("Command: CityLearn\scripts\launch_citylearn_v3_official_training.ps1 -Scenario {0} -Seed {1} -EpisodeTimeSteps {2} -Episodes {3} -SchemaPath CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json -OutputRoot {4} -TorchThreads {5} -LiveProgressInterval {6} -ArtifactProfile {7} -TraceRecordInterval {8} -TraceDetail {9} -GpuProfile {10} -MaxGpuVramGib {11} -GpuVramReserveGib {12} -CudaMemoryFraction {13} -ParallelScenarios:{14} -MaxConcurrentScenarioJobs {15} -MaxConcurrentHeavyJobs {16} -Cuda:{17} -LiveOutput:{18}" -f $Scenario, $Seed, $EpisodeTimeSteps, $Episodes, $OutputRoot, $TorchThreads, $LiveProgressInterval, $ArtifactProfile, $TraceRecordInterval, $TraceDetail, $GpuProfile, $MaxGpuVramGib, $GpuVramReserveGib, $CudaMemoryFraction, [bool]$ParallelScenarios, $MaxConcurrentScenarioJobs, $MaxConcurrentHeavyJobs, [bool]$Cuda, [bool]$LiveOutput)
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
    $monitorProcess = Start-Process -FilePath $PowerShellExe -ArgumentList $monitorArgs -WorkingDirectory $ProjectRoot -WindowStyle Normal -PassThru
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
    -ArtifactProfile $ArtifactProfile `
    -TraceRecordInterval $TraceRecordInterval `
    -TraceDetail $TraceDetail `
    -GpuProfile $GpuProfile `
    -MaxGpuVramGib $MaxGpuVramGib `
    -GpuVramReserveGib $GpuVramReserveGib `
    -CudaMemoryFraction $CudaMemoryFraction `
    -ParallelScenarios $ParallelScenarios `
    -MaxConcurrentScenarioJobs $MaxConcurrentScenarioJobs `
    -MaxConcurrentHeavyJobs $MaxConcurrentHeavyJobs `
    -Cuda:$Cuda `
    -LiveOutput:$LiveOutput
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host ("Training launcher finished with exit code: " + $exitCode) -ForegroundColor Yellow
Write-Host ("OutputRoot: " + $OutputRoot)
Stop-Transcript | Out-Null
Read-Host "Press Enter to close"
exit $exitCode
