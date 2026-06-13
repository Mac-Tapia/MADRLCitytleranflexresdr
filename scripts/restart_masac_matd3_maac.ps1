$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

& "CityLearn\scripts\launch_citylearn_v3_official_training.ps1" `
    -Scenario ALL `
    -Seed 0 `
    -EpisodeTimeSteps 8760 `
    -Episodes 5 `
    -SchemaPath "CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json" `
    -OutputRoot "outputs\citylearn_v3_madrl_full_20260613_010234" `
    -ArtifactProfile efficient `
    -TraceRecordInterval 10 `
    -TraceDetail compact `
    -GpuProfile local4060_fast `
    -MaxGpuVramGib 0 `
    -GpuVramReserveGib 1.5 `
    -CudaMemoryFraction 0 `
    -ParallelScenarios:$true `
    -MaxConcurrentScenarioJobs 2 `
    -MaxConcurrentHeavyJobs 1 `
    -Cuda `
    -LiveOutput:$false `
    -StartFromAlgorithm masac `
    -SkipCompleted `
    -MasacBufferSize 2 `
    -MasacMaxReplayBufferGib 3
