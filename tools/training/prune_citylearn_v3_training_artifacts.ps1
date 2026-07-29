param(
    [string]$OutputRoot = "outputs\citylearn_v3_madrl_full_20260615_074011_v4",
    [int]$Seed = 0,
    [switch]$Apply,
    [switch]$KeepStatisticalComparison,
    [switch]$KeepRootMirrors
)

$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
# Script lives in tools/training/ — repo root is two levels up.
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $ScriptPath "..\..")).Path
$OutputsRoot = (Resolve-Path -LiteralPath (Join-Path $ProjectRoot "outputs")).Path
$OutputRootPath = if ([System.IO.Path]::IsPathRooted($OutputRoot)) {
    (Resolve-Path -LiteralPath $OutputRoot).Path
}
else {
    (Resolve-Path -LiteralPath (Join-Path $ProjectRoot $OutputRoot)).Path
}

function Assert-UnderPath {
    param(
        [string]$Path,
        [string]$Parent
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fullParent = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($fullParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe path outside expected parent: $fullPath"
    }
}

Assert-UnderPath -Path $OutputRootPath -Parent $OutputsRoot

$Algorithms = @("happo", "masac", "matd3", "maac")
$Scenarios = @("E1", "E2", "E3")
$CanonicalFiles = @(
    "data\results.json",
    "data\training_summary.json",
    "data\checkpoint_manifest.json",
    "data\artifact_audit.json",
    "data\timeseries.csv",
    "data\trace.csv",
    "figures\figures_manifest.json",
    "figures\tables\episode_summary.csv",
    "figures\tables\axis_baseline_comparison.csv",
    "figures\tables\agent_reward_summary.md"
)

$RunDirs = @()
foreach ($algorithm in $Algorithms) {
    foreach ($scenario in $Scenarios) {
        $runDir = Join-Path $OutputRootPath ("{0}\{1}_seed_{2}" -f $algorithm, $scenario, $Seed)
        if (-not (Test-Path -LiteralPath $runDir -PathType Container)) {
            throw "Missing expected run directory: $runDir"
        }

        foreach ($relativePath in $CanonicalFiles) {
            $candidate = Join-Path $runDir $relativePath
            if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
                throw "Missing canonical completed-training artifact: $candidate"
            }
        }

        $checkpointDir = Join-Path $runDir "checkpoints"
        if (-not (Test-Path -LiteralPath $checkpointDir -PathType Container)) {
            throw "Missing checkpoint directory: $checkpointDir"
        }

        $checkpointFiles = @(
            Get-ChildItem -Recurse -LiteralPath $checkpointDir -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Extension -in @(".pt", ".pth", ".pkl", ".ckpt") }
        )
        if ($checkpointFiles.Count -lt 1) {
            throw "No checkpoint model files found under: $checkpointDir"
        }

        if ($algorithm -eq "maac") {
            for ($episode = 1; $episode -le 5; $episode++) {
                $episodeCheckpoint = Join-Path $checkpointDir ("checkpoint_episode_{0}.pt" -f $episode)
                if (-not (Test-Path -LiteralPath $episodeCheckpoint -PathType Leaf)) {
                    throw "Missing MAAC episode checkpoint: $episodeCheckpoint"
                }
            }
        }

        $RunDirs += [pscustomobject]@{
            Algorithm = $algorithm
            Scenario = $scenario
            Path = $runDir
            CheckpointDir = $checkpointDir
        }
    }
}

$Candidates = New-Object System.Collections.Generic.List[object]

function Add-Candidate {
    param(
        [string]$Path,
        [string]$Reason
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $resolved = (Resolve-Path -LiteralPath $Path).Path
    Assert-UnderPath -Path $resolved -Parent $OutputRootPath
    $item = Get-Item -LiteralPath $resolved -Force
    $bytes = if ($item.PSIsContainer) {
        (Get-ChildItem -Recurse -LiteralPath $item.FullName -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    }
    else {
        $item.Length
    }
    if ($null -eq $bytes) { $bytes = 0 }
    $Candidates.Add([pscustomobject]@{
        Path = $item.FullName
        Type = if ($item.PSIsContainer) { "directory" } else { "file" }
        Reason = $Reason
        MB = [math]::Round([double]$bytes / 1MB, 3)
    }) | Out-Null
}

if (-not $KeepStatisticalComparison) {
    Add-Candidate -Path (Join-Path $OutputRootPath "statistical_comparison") -Reason "derived_duplicate_cross_run_comparison"
}
Add-Candidate -Path (Join-Path $OutputRootPath "visible_training_v4_transcript.log") -Reason "interactive_monitor_transcript"

foreach ($run in $RunDirs) {
    Add-Candidate -Path (Join-Path $run.Path "live_progress.json") -Reason "stale_live_monitor_state_after_completion"

    if (-not $KeepRootMirrors) {
        foreach ($mirrorName in @(
            "artifact_audit.json",
            "checkpoint_manifest.json",
            "results.json",
            "training_summary.json",
            "timeseries.csv",
            "trace.csv"
        )) {
            $rootMirror = Join-Path $run.Path $mirrorName
            $canonical = Join-Path $run.Path (Join-Path "data" $mirrorName)
            if ((Test-Path -LiteralPath $rootMirror -PathType Leaf) -and (Test-Path -LiteralPath $canonical -PathType Leaf)) {
                Add-Candidate -Path $rootMirror -Reason "duplicate_root_mirror_canonical_data_exists"
            }
        }
    }

    $checkpointLogDirs = @(
        Get-ChildItem -Recurse -LiteralPath $run.CheckpointDir -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq "logs" }
    )
    foreach ($dir in $checkpointLogDirs) {
        Add-Candidate -Path $dir.FullName -Reason "checkpoint_tensorboard_logs_not_model_state"
    }
}

$Candidates = @($Candidates | Sort-Object Path -Unique)

if ($Candidates.Count -eq 0) {
    Write-Host "No prune candidates found."
    exit 0
}

$totalMb = [math]::Round((($Candidates | Measure-Object MB -Sum).Sum), 3)
$Candidates |
    Select-Object Type, MB, Reason, Path |
    Format-Table -AutoSize | Out-String -Width 260 |
    Write-Host

Write-Host ("Candidates: {0} | Total: {1} MB | Mode: {2}" -f $Candidates.Count, $totalMb, $(if ($Apply) { "APPLY" } else { "DRY-RUN" }))

if (-not $Apply) {
    Write-Host "Dry-run only. Re-run with -Apply to delete these derived/obsolete artifacts."
    exit 0
}

foreach ($candidate in $Candidates) {
    Assert-UnderPath -Path $candidate.Path -Parent $OutputRootPath
    if ($candidate.Type -eq "directory") {
        Remove-Item -LiteralPath $candidate.Path -Recurse -Force
    }
    else {
        Remove-Item -LiteralPath $candidate.Path -Force
    }
}

if (-not $KeepStatisticalComparison) {
    foreach ($run in $RunDirs) {
        foreach ($relativeJson in @("data\results.json", "data\training_summary.json", "results.json", "training_summary.json")) {
            $jsonPath = Join-Path $run.Path $relativeJson
            if (-not (Test-Path -LiteralPath $jsonPath -PathType Leaf)) {
                continue
            }

            $payload = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
            if ($payload.PSObject.Properties.Name -contains "statistical_comparison_dir") {
                $payload.statistical_comparison_dir = $null
            }
            if ($payload.artifacts -and ($payload.artifacts.PSObject.Properties.Name -contains "statistical_comparison_dir")) {
                $payload.artifacts.statistical_comparison_dir = $null
            }
            $payload | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
        }
    }
}

if (-not $KeepRootMirrors) {
    foreach ($run in $RunDirs) {
        foreach ($relativeJson in @("data\results.json", "data\training_summary.json")) {
            $jsonPath = Join-Path $run.Path $relativeJson
            if (-not (Test-Path -LiteralPath $jsonPath -PathType Leaf)) {
                continue
            }

            $payload = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
            foreach ($propertyName in @(
                "artifact_audit_json_root",
                "checkpoint_manifest_root",
                "results_json_root",
                "training_summary_json_root",
                "timeseries_csv_root",
                "trace_csv_root"
            )) {
                if ($payload.PSObject.Properties.Name -contains $propertyName) {
                    $payload.$propertyName = $null
                }
                if ($payload.artifacts -and ($payload.artifacts.PSObject.Properties.Name -contains $propertyName)) {
                    $payload.artifacts.$propertyName = $null
                }
            }

            foreach ($policyName in @("artifact_write_policy")) {
                if ($payload.$policyName) {
                    if ($payload.$policyName.PSObject.Properties.Name -contains "root_timeseries_csv") {
                        $payload.$policyName.root_timeseries_csv = $false
                    }
                    if ($payload.$policyName.PSObject.Properties.Name -contains "root_trace_csv") {
                        $payload.$policyName.root_trace_csv = $false
                    }
                    if ($payload.$policyName.PSObject.Properties.Name -contains "root_building_detail_csv") {
                        $payload.$policyName.root_building_detail_csv = $false
                    }
                    if ($payload.$policyName.PSObject.Properties.Name -contains "legacy_root_artifacts") {
                        $payload.$policyName.legacy_root_artifacts = $false
                    }
                    if ($payload.$policyName.PSObject.Properties.Name -contains "statistical_comparison_artifacts") {
                        $payload.$policyName.statistical_comparison_artifacts = $false
                    }
                    if ($payload.$policyName.PSObject.Properties.Name -contains "statistical_comparison_trace_csv") {
                        $payload.$policyName.statistical_comparison_trace_csv = $false
                    }
                }
                if ($payload.artifacts -and $payload.artifacts.$policyName) {
                    if ($payload.artifacts.$policyName.PSObject.Properties.Name -contains "root_timeseries_csv") {
                        $payload.artifacts.$policyName.root_timeseries_csv = $false
                    }
                    if ($payload.artifacts.$policyName.PSObject.Properties.Name -contains "root_trace_csv") {
                        $payload.artifacts.$policyName.root_trace_csv = $false
                    }
                    if ($payload.artifacts.$policyName.PSObject.Properties.Name -contains "root_building_detail_csv") {
                        $payload.artifacts.$policyName.root_building_detail_csv = $false
                    }
                    if ($payload.artifacts.$policyName.PSObject.Properties.Name -contains "legacy_root_artifacts") {
                        $payload.artifacts.$policyName.legacy_root_artifacts = $false
                    }
                    if ($payload.artifacts.$policyName.PSObject.Properties.Name -contains "statistical_comparison_artifacts") {
                        $payload.artifacts.$policyName.statistical_comparison_artifacts = $false
                    }
                    if ($payload.artifacts.$policyName.PSObject.Properties.Name -contains "statistical_comparison_trace_csv") {
                        $payload.artifacts.$policyName.statistical_comparison_trace_csv = $false
                    }
                }
            }

            $payload | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
        }
    }
}

Write-Host ("Deleted {0} derived/obsolete artifact paths ({1} MB)." -f $Candidates.Count, $totalMb)
