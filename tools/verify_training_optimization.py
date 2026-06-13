"""Verify CityLearn v3 MADRL training optimization wiring.

This script is intentionally static: it does not launch training and it does
not create output artifacts. It fails fast when one of the training bottleneck
mitigations is accidentally removed.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"Missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_all(text: str, relative_path: str, needles: list[str]) -> None:
    for needle in needles:
        require(needle in text, f"{relative_path} is missing: {needle}")


def verify_launcher(relative_path: str, expect_parallel: bool) -> None:
    text = read_text(relative_path)
    require_all(
        text,
        relative_path,
        [
            '[string]$ArtifactProfile = "efficient"',
            "[int]$TraceRecordInterval = 10",
            '[string]$TraceDetail = "compact"',
            '"--artifact-profile", "$ArtifactProfile"',
            '"--trace-record-interval", "$TraceRecordInterval"',
            '"--trace-detail", "$TraceDetail"',
            "artifact_optimization = [ordered]@",
            'root_trace_csv = ($ArtifactProfile -eq "full")',
            'statistical_trace_copy = ($ArtifactProfile -eq "full")',
            "Get-DedicatedCudaGpuInfo",
            "nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version",
            "source = \"nvidia-smi dedicated memory, not Windows shared GPU memory\"",
            "MaxGpuVramGib",
            "GpuVramReserveGib",
            "CudaMemoryFraction",
            "CudaMemoryArgs",
            "local_8gb_safety_mode",
            '"--cuda-memory-fraction"',
            "Wait-TrainingRam",
            "SkipCompleted",
        ],
    )
    if "official_training" in relative_path:
        require_all(
            text,
            relative_path,
            [
                "MasacCriticBatchSize",
                "MasacRnnHiddenDim",
                "MasacQmixHiddenDim",
                "MasacHyperHiddenDim",
                "MasacPreloadBatchDevice",
            ],
        )
        require("MasacCriticBatchSize = if ($IsLocal8GbGpu) { 1 } else { 64 }" in text, f"{relative_path} must use MASAC critic batch 1 on local 8GB GPUs")
        require("MasacMaxReplayBufferGib = if ($IsLocal8GbGpu) { 3.0 } else { 8 }" in text, f"{relative_path} must allow the validated 2.74 GiB MASAC replay estimate on local 8GB GPUs")
        require("MasacRnnHiddenDim = if ($IsLocal8GbGpu) { 64 } else { 256 }" in text, f"{relative_path} must use MASAC RNN hidden 64 on local 8GB GPUs")
        require("MasacQmixHiddenDim = if ($IsLocal8GbGpu) { 32 } else { 128 }" in text, f"{relative_path} must use MASAC QMIX hidden 32 on local 8GB GPUs")
        require('"--masac-preload-batch-device", "$MasacPreloadBatchDevice"' in text, f"{relative_path} must pass optimized MASAC batch preload mode")
    if "iquitos_training" in relative_path:
        require("$MasacMaxReplayBufferGib = if ($IsLocal8GbGpu) { 3.0 } else { 8 }" in text, f"{relative_path} must allow the validated 2.74 GiB MASAC replay estimate on local 8GB GPUs")
        require('$MasacPreloadBatchDevice = "auto"' in text, f"{relative_path} must default MASAC batch preload to auto")
        require('"--masac-preload-batch-device", "$MasacPreloadBatchDevice"' in text, f"{relative_path} must pass optimized MASAC batch preload mode")
        require('"--critic-batch-size", "1"' in text, f"{relative_path} must keep MASAC critic batch 1")
        require('"--actor-sample-times", "2"' in text, f"{relative_path} must keep MASAC actor samples at 2")
    if expect_parallel:
        require_all(
            text,
            relative_path,
            [
                '[bool]$ParallelScenarios = $true',
                "MaxConcurrentScenarioJobs",
                "MaxConcurrentHeavyJobs",
                "parallel_scenarios_by_algorithm",
                "Invoke-ParallelScenarioStage",
                "Start-ParallelTrainingJob",
                "Complete-ParallelTrainingJob",
            ],
        )


def verify_visible_wrappers() -> None:
    wrapper_text = read_text("scripts/run_citylearn_v3_full_training_visible.ps1")
    require('[bool]$LiveOutput = $false' in wrapper_text, "visible full-training wrapper must default LiveOutput to false")
    require("visible monitor + parallel scenario stages" in wrapper_text, "visible wrapper must describe parallel monitor mode")

    for relative_path in ("scripts/training_launcher_window.ps1", "scripts/training_resume_window.ps1"):
        text = read_text(relative_path)
        require("-LiveOutput" not in text, f"{relative_path} must omit LiveOutput so the launcher switch remains false")
        require("-MaxConcurrentScenarioJobs 2" in text, f"{relative_path} must request 2 concurrent scenario jobs")
        require("-MaxConcurrentHeavyJobs 1" in text, f"{relative_path} must keep heavy algorithms capped at 1")

    restart_text = read_text("scripts/restart_masac_matd3_maac.ps1")
    require('cd d:\\' not in restart_text.lower(), "MASAC restart helper must use repo-relative project resolution")
    require("-TorchThreads 12" not in restart_text, "MASAC restart helper must not override local4060_fast TorchThreads=8")
    require("-LiveProgressInterval 250" not in restart_text, "MASAC restart helper must not override local4060_fast LiveProgressInterval=1000")
    require("-SkipCompleted" in restart_text, "MASAC restart helper must skip completed runs on resume")
    require("-MasacMaxReplayBufferGib 3" in restart_text, "MASAC restart helper must keep the validated 3 GiB replay guard")
    require("-MasacPreloadBatchDevice auto" in restart_text, "MASAC restart helper must enable optimized batch preload auto mode")


def verify_reward_profiles() -> None:
    data = json.loads(read_text("CityLearn/configs/citylearn_v3_madrl_training.json"))
    expected_axis = {
        "E1": {"flex": 0.70, "carbon": 0.15, "cost": 0.15},
        "E2": {"flex": 0.15, "carbon": 0.70, "cost": 0.15},
        "E3": {"flex": 0.25, "carbon": 0.15, "cost": 0.60},
    }
    expected_profile = {
        "team_reward_ratio": 0.70,
        "ev_weight": 0.12,
        "reward_scale": 1.00,
        "ramp_weight": 0.35,
        "peak_weight": 0.45,
    }
    require(data["reward"]["axis_weights"] == expected_axis, "reward axis weights must match the validated multi-objective scenarios")
    require(float(data["algorithms"]["MASAC"]["cli"]["max_replay_buffer_gib"]) >= 3.0, "MASAC replay guard must cover the validated 2.74 GiB estimate")
    require(int(data["algorithms"]["MASAC"]["cli"]["buffer_size"]) == 2, "MASAC local buffer size must remain 2 for 8GB GPU safety")
    require(data["algorithms"]["MASAC"]["cli"]["masac_preload_batch_device"] == "auto", "MASAC optimized batch preload mode must default to auto")

    for algorithm in ("HAPPO", "MASAC", "MATD3", "MAAC"):
        profile = data["reward"]["profiles"][algorithm]
        require(profile["profile_name"] == f"{algorithm.lower()}_unified_comparable_v2", f"{algorithm} reward profile is not unified comparable v2")
        require(profile["axis_weight_multipliers"] == {"flex": 1.0, "carbon": 1.0, "cost": 1.0}, f"{algorithm} axis multipliers must be neutral")
        for key, expected in expected_profile.items():
            require(abs(float(profile[key]) - expected) < 1.0e-9, f"{algorithm} {key}={profile[key]}, expected {expected}")


def verify_training_common() -> None:
    relative_path = "CityLearn/scripts/citylearn_v3_training_common.py"
    text = read_text(relative_path)
    require_all(
        text,
        relative_path,
        [
            'choices=("full", "efficient", "minimal")',
            'artifact_profile not in {"full", "efficient", "minimal"}',
            'write_root_trace = artifact_profile == "full"',
            'include_statistical_trace = artifact_profile == "full"',
            "def _trace_sampling_payload",
            '"trace_is_sampled": sampled',
            "self.trace_record_interval = max(0, int(trace_record_interval))",
            "self.trace_detail not in",
            "self.global_step % self.trace_record_interval == 0 or all_done",
            "np.nan_to_num",
            "np.clip",
            "NormalizedObservationWrapper plus adapter clipping to [0, 1]",
            '"--cuda-memory-fraction"',
            "torch_module.cuda.set_per_process_memory_fraction",
            '"cuda_memory_fraction_applied": cuda_memory_fraction_applied',
        ],
    )


def verify_train_scripts() -> None:
    for name in ("happo", "masac", "matd3", "maac"):
        relative_path = f"CityLearn/scripts/train_citylearn_v3_{name}.py"
        text = read_text(relative_path)
        require_all(
            text,
            relative_path,
            [
                "trace_record_interval=args.trace_record_interval",
                "trace_detail=args.trace_detail",
                "cuda_memory_fraction=args.cuda_memory_fraction",
            ],
        )
    masac_text = read_text("CityLearn/scripts/train_citylearn_v3_masac.py")
    require("install_masac_runtime_optimizations" in masac_text, "MASAC train script must install runtime backend optimizations")
    require("--masac-preload-batch-device" in masac_text, "MASAC train script must expose optimized batch preload mode")

    masac_patch = read_text("CityLearn/scripts/masac_runtime_optimizations.py")
    require("PATCH_VERSION = \"citylearn_masac_runtime_v1\"" in masac_patch, "MASAC runtime optimization patch version missing")
    require("CUDA batch preload uses auto fallback to CPU after OOM" in masac_patch, "MASAC runtime patch must keep OOM fallback")
    require("per-timestep .cuda() calls are removed" in masac_patch, "MASAC runtime patch must document repeated CUDA-copy removal")


def verify_monitors() -> None:
    official_path = "CityLearn/scripts/monitor_citylearn_v3_official_training.ps1"
    official = read_text(official_path)
    require_all(
        official,
        official_path,
        [
            "function Clear-MonitorHost",
            'Join-Path $runDir "data\\results.json"',
            'Join-Path $runDir "data\\trace.csv"',
            "artifact_profile",
            "reward_signal",
            "trace_interval",
        ],
    )

    iquitos_path = "CityLearn/scripts/monitor_citylearn_v3_iquitos_training.ps1"
    iquitos = read_text(iquitos_path)
    require_all(
        iquitos,
        iquitos_path,
        [
            "function Clear-MonitorHost",
            "artifact_optimization",
            "trace_interval",
            "num_env_steps",
            "global_step",
        ],
    )


def verify_wrappers() -> None:
    launcher_path = "scripts/training_launcher_window.ps1"
    launcher = read_text(launcher_path)
    require_all(
        launcher,
        launcher_path,
        [
            '$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path',
            "CITYLEARN_MADRL_OUTPUT_ROOT",
            "latest_visible_training_output_root.txt",
            "citylearn_v3_madrl_full_",
            "-ArtifactProfile efficient",
            "-TraceRecordInterval 10",
            "-TraceDetail compact",
            "-GpuProfile local4060_fast",
            "-MaxGpuVramGib 8",
            "-GpuVramReserveGib 1.5",
        ],
    )
    require('set-location "d:\\' not in launcher.lower(), f"{launcher_path} still uses an absolute Set-Location")
    require("citylearn_v3_madrl_oficial_v4" not in launcher, f"{launcher_path} still points to v4 output")

    resume_path = "scripts/training_resume_window.ps1"
    resume = read_text(resume_path)
    require_all(
        resume,
        resume_path,
        [
            '$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path',
            "Get-LastTrainingOutputRoot",
            "CITYLEARN_MADRL_OUTPUT_ROOT",
            "latest_visible_training_output_root.txt",
            "-SkipCompleted",
            "-ArtifactProfile efficient",
            "-TraceRecordInterval 10",
            "-TraceDetail compact",
            "-GpuProfile local4060_fast",
            "-MaxGpuVramGib 8",
            "-GpuVramReserveGib 1.5",
        ],
    )
    require('set-location "d:\\' not in resume.lower(), f"{resume_path} still uses an absolute Set-Location")
    require("citylearn_v3_madrl_oficial_v4" not in resume, f"{resume_path} still points to v4 output")

    visible_path = "scripts/run_citylearn_v3_full_training_visible.ps1"
    visible = read_text(visible_path)
    require_all(
        visible,
        visible_path,
        [
            '[bool]$ParallelScenarios = $true',
            "MaxConcurrentScenarioJobs",
            "MaxConcurrentHeavyJobs",
            "MaxGpuVramGib",
            "GpuVramReserveGib",
            "CudaMemoryFraction",
            "-ParallelScenarios",
            "-MaxGpuVramGib",
            "-GpuVramReserveGib",
            "-CudaMemoryFraction",
            "-ArtifactProfile",
            "-TraceRecordInterval",
            "-TraceDetail",
        ],
    )


def verify_tests() -> None:
    relative_path = "CityLearn/tests/test_citylearn_v3_training_artifacts.py"
    text = read_text(relative_path)
    require_all(
        text,
        relative_path,
        [
            "test_efficient_artifact_profile_avoids_duplicate_heavy_trace_csv",
            "trace_happo_E3.csv",
            'policy["root_trace_csv"] is False',
            'policy["trace_is_sampled"] is True',
            'policy["trace_record_interval"] == 10',
        ],
    )


def main() -> int:
    verify_launcher("CityLearn/scripts/launch_citylearn_v3_official_training.ps1", expect_parallel=True)
    verify_launcher("CityLearn/scripts/launch_citylearn_v3_iquitos_training.ps1", expect_parallel=True)
    verify_visible_wrappers()
    verify_reward_profiles()
    verify_training_common()
    verify_train_scripts()
    verify_monitors()
    verify_wrappers()
    verify_tests()
    print("OK: training optimization wiring verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
