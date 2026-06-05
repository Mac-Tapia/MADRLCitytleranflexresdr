param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [int]$RefreshSeconds = 30
)

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "CityLearn MADRL training monitor"
$OutputEncoding = [System.Text.Encoding]::UTF8

function Read-JsonFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

while ($true) {
    Clear-Host
    Write-Host "CITYLEARN V3 MADRL - TRAINING MONITOR" -ForegroundColor Cyan
    Write-Host ("Time: " + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
    Write-Host ("OutputRoot: " + $OutputRoot)
    Write-Host ""

    $statusPath = Join-Path $OutputRoot "official_full_status.json"
    $status = Read-JsonFile -Path $statusPath

    if ($null -ne $status) {
        Write-Host ("Chain status: {0} | dataset={1} | scenario={2}" -f $status.status, $status.dataset, $status.scenario) -ForegroundColor Green

        if ($status.jobs -and $status.jobs.Count -gt 0) {
            $job = $status.jobs[-1]
            Write-Host ("Current job: {0}/{1} | exit={2}" -f $job.scenario, $job.name, $job.exit_code)
            Write-Host ("Log: " + $job.log)
        }
    }
    else {
        Write-Host "Status file not found yet." -ForegroundColor Yellow
    }

    Write-Host ""
    $liveProgress = Get-ChildItem -LiteralPath $OutputRoot -Recurse -Filter live_progress.json -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($liveProgress) {
        Write-Host ("Live progress: " + $liveProgress.FullName) -ForegroundColor Yellow
        $progress = Read-JsonFile -Path $liveProgress.FullName

        if ($null -ne $progress) {
            $progress |
                Select-Object algorithm, scenario, episode, episode_step, global_step, time_step,
                    episode_return_cumulative, episode_reward_mean_cumulative,
                    total_reward_mean_cumulative, instant_reward_mean |
                Format-List
        }
    }
    else {
        Write-Host "No live_progress.json found yet." -ForegroundColor Yellow
    }

    Write-Host "GPU:" -ForegroundColor Cyan
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader

    Write-Host ""
    $activeLog = $null
    if ($null -ne $status -and $status.jobs -and $status.jobs.Count -gt 0) {
        $activeLog = $status.jobs[-1].log
    }

    if ($activeLog -and (Test-Path -LiteralPath $activeLog)) {
        Write-Host "Last log lines:" -ForegroundColor Cyan
        Get-Content -LiteralPath $activeLog -Tail 25
    }

    $activeErr = $null
    if ($null -ne $status -and $status.jobs -and $status.jobs.Count -gt 0) {
        $activeErr = $status.jobs[-1].stderr_log
    }

    if ($activeErr -and (Test-Path -LiteralPath $activeErr)) {
        Write-Host ""
        Write-Host "Stderr:" -ForegroundColor DarkYellow
        Get-Content -LiteralPath $activeErr -Tail 12
    }

    Write-Host ""
    Write-Host ("Refresh every {0} s. Closing this monitor does not stop training." -f $RefreshSeconds) -ForegroundColor Gray
    Start-Sleep -Seconds $RefreshSeconds
}
