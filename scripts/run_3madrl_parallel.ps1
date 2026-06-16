param(
    [string]$Scenario = "ALL",
    [int]$Seed = 0,
    [int]$EpisodeTimeSteps = 8760,
    [int]$Episodes = 50,
    [string]$SchemaPath = "CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json",
    [string]$OutputRoot,
    [ValidateSet("happo", "masac", "matd3", "maac")]
    [string[]]$Algorithms = @("happo", "matd3", "maac"),
    [ValidateSet("local4060_fast", "local4060", "balanced", "conservative", "aws")]
    [string]$GpuProfile = "aws",
    [ValidateRange(1, 16)]
    [int]$MaxConcurrentScenarioJobs = 3,
    [ValidateRange(1, 16)]
    [int]$MaxConcurrentHeavyJobs = 2,
    [switch]$AllowGpuOversubscription,
    [switch]$DryRun
)

# Entrena varios MADRL (HAPPO/MATD3/MAAC por defecto) en procesos paralelos
# independientes, y dentro de cada uno paraleliza tambien sus escenarios
# (E1/E2/E3) via -ParallelScenarios. Requiere el parametro -EndAtAlgorithm
# del launcher (CityLearn\scripts\launch_citylearn_v3_official_training.ps1)
# para que cada proceso entrene SOLO su algoritmo y no continue en cascada
# hacia el siguiente de la secuencia happo->masac->matd3->maac.
#
# MASAC no esta en la lista por defecto por su mayor consumo de VRAM/RAM;
# se puede agregar con -Algorithms happo,matd3,maac,masac si la GPU lo permite.
#
# Pensado para AWS (g5.2xlarge / A10G 24GB o superior). En GPU local de 8GB
# se bloquea por defecto: 3 algoritmos x N escenarios concurrentes satura la
# VRAM. Usar -AllowGpuOversubscription para forzarlo bajo su propio riesgo.

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

if (-not $OutputRoot) {
    $SessionStamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputRoot = "outputs\citylearn_v3_madrl_3parallel_${SessionStamp}"
}

function Get-DedicatedVramGib {
    try {
        $line = & nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null |
            Select-Object -First 1
        if ([string]::IsNullOrWhiteSpace($line)) { return $null }
        return [math]::Round(([double]$line.Trim()) / 1024.0, 2)
    }
    catch {
        return $null
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  3 MADRL EN PARALELO: $($Algorithms -join ', ')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Sesion       : $OutputRoot"
Write-Host "  Episodios    : $Episodes"
Write-Host "  Perfil GPU   : $GpuProfile"
Write-Host "  Escenarios/MADRL en paralelo: $MaxConcurrentScenarioJobs (heavy: $MaxConcurrentHeavyJobs)"
Write-Host ""

$detectedVramGib = Get-DedicatedVramGib
if ($null -ne $detectedVramGib -and $detectedVramGib -le 8.5 -and -not $AllowGpuOversubscription) {
    Write-Host "ERROR: GPU local detectada con $detectedVramGib GiB de VRAM dedicada." -ForegroundColor Red
    Write-Host "Lanzar $($Algorithms.Count) algoritmos en paralelo, cada uno con hasta" -ForegroundColor Red
    Write-Host "$MaxConcurrentScenarioJobs escenarios simultaneos, satura una GPU de 8GB (OOM esperado)." -ForegroundColor Red
    Write-Host "Este script esta pensado para AWS (g5.2xlarge / A10G 24GB o superior)." -ForegroundColor Red
    Write-Host "Si igual deseas intentarlo localmente, repite con -AllowGpuOversubscription." -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Path "outputs" -Force | Out-Null
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
Set-Content -Path "outputs\latest_3madrl_parallel_output_root.txt" -Value $OutputRoot -Encoding UTF8

$pwshExe = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwshExe -and $IsWindows) { $pwshExe = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source }
if (-not $pwshExe) { throw "pwsh (PowerShell 7) not found in PATH." }

$logDir = Join-Path $OutputRoot "parallel_launch_logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$processes = @()
foreach ($algo in $Algorithms) {
    $heavyForThisAlgo = if ($algo -in @("masac", "maac")) { $MaxConcurrentHeavyJobs } else { $MaxConcurrentScenarioJobs }

    $launcherArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $ProjectRoot "CityLearn\scripts\launch_citylearn_v3_official_training.ps1"),
        "-Scenario", $Scenario,
        "-Seed", $Seed,
        "-EpisodeTimeSteps", $EpisodeTimeSteps,
        "-Episodes", $Episodes,
        "-SchemaPath", $SchemaPath,
        "-OutputRoot", $OutputRoot,
        "-StartFromAlgorithm", $algo,
        "-EndAtAlgorithm", $algo,
        "-GpuProfile", $GpuProfile,
        "-ParallelScenarios", "true",
        "-MaxConcurrentScenarioJobs", $MaxConcurrentScenarioJobs,
        "-MaxConcurrentHeavyJobs", $heavyForThisAlgo,
        "-Cuda"
    )
    if ($AllowGpuOversubscription) { $launcherArgs += "-AllowGpuOversubscription" }

    Write-Host "  -> $($algo.ToUpper()): $pwshExe $($launcherArgs -join ' ')" -ForegroundColor DarkGray

    if ($DryRun) { continue }

    $stdOut = Join-Path $logDir "$algo.stdout.log"
    $stdErr = Join-Path $logDir "$algo.stderr.log"
    $startProcessArgs = @{
        FilePath = $pwshExe
        ArgumentList = $launcherArgs
        WorkingDirectory = $ProjectRoot
        RedirectStandardOutput = $stdOut
        RedirectStandardError = $stdErr
        PassThru = $true
    }
    if ($IsWindows) { $startProcessArgs["WindowStyle"] = "Normal" }
    $proc = Start-Process @startProcessArgs
    $processes += [pscustomobject]@{ Algorithm = $algo; ProcessId = $proc.Id; Process = $proc }
}

if ($DryRun) {
    Write-Host ""
    Write-Host "DryRun: no se lanzo ningun proceso." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Procesos lanzados:" -ForegroundColor Green
$processes | ForEach-Object { Write-Host "  $($_.Algorithm.ToUpper())  PID $($_.ProcessId)" }
Write-Host ""
Write-Host "Sesion: $OutputRoot" -ForegroundColor Green
Write-Host "Logs de lanzamiento: $logDir" -ForegroundColor Green
Write-Host "Monitorea con: nvidia-smi dmon  -o  Get-Process -Id $($processes.ProcessId -join ',')" -ForegroundColor DarkGray
