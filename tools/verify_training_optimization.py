"""Verify CityLearn v3 MADRL training optimization wiring.

This script is intentionally static: it does not launch training and it does
not create output artifacts. It fails fast when one of the training bottleneck
mitigations is accidentally removed.
"""

from __future__ import annotations

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
    verify_training_common()
    verify_train_scripts()
    verify_monitors()
    verify_wrappers()
    verify_tests()
    print("OK: training optimization wiring verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
