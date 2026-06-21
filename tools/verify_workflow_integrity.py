"""Verify that the Iquitos dataset, training and evidence workflow is wired.

This check is static plus lightweight JSON/schema inspection. It does not start
training and it does not create training artifacts; it fails when a canonical
path in the root workflow is missing, stale or disconnected.
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_MANIFEST = ROOT / "docs" / "workflow_manifest.json"
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"
AUDIT_DIR = ROOT / "outputs" / "dataset_audit"
LATEST_OUTPUT_POINTER = ROOT / "outputs" / "latest_visible_training_output_root.txt"
DEFAULT_MANIFEST_OUT = AUDIT_DIR / "workflow_integrity_manifest.json"

ACTIVE_FILES_WITH_NO_STALE_DEFAULTS = [
    "pyproject.toml",
    "scripts/run_citylearn_v3_full_training_visible.ps1",
    "scripts/training_launcher_window.ps1",
    "scripts/training_resume_window.ps1",
    "CityLearn/configs/citylearn_v3_madrl_training.yaml",
    "CityLearn/configs/citylearn_v3_madrl_training.json",
    "CityLearn/scripts/launch_citylearn_v3_official_training.ps1",
    "CityLearn/scripts/monitor_citylearn_v3_official_training.ps1",
    "CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py",
    "CityLearn/scripts/generate_thesis_objective_evidence.py",
]

STALE_ROOTS_FOR_ACTIVE_DEFAULTS = [
    "outputs/citylearn_v3_madrl_oficial_v3",
    "outputs\\citylearn_v3_madrl_oficial_v3",
    "outputs/citylearn_v3_madrl_oficial_v4",
    "outputs\\citylearn_v3_madrl_oficial_v4",
    "outputs/citylearn_v3_madrl_oficial_v5",
    "outputs\\citylearn_v3_madrl_oficial_v5",
    "outputs/citylearn_v3_madrl_official_full_cuda_v2",
    "outputs\\citylearn_v3_madrl_official_full_cuda_v2",
    "outputs/citylearn_v3_madrl_iquitos_official_full_cuda_visible_relaunch_20260602_222217",
    "outputs\\citylearn_v3_madrl_iquitos_official_full_cuda_visible_relaunch_20260602_222217",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def project_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def validate_workflow_manifest(errors: list[str]) -> dict[str, Any]:
    require(WORKFLOW_MANIFEST.is_file(), f"Missing {rel(WORKFLOW_MANIFEST)}", errors)
    if not WORKFLOW_MANIFEST.is_file():
        return {}

    manifest = load_json(WORKFLOW_MANIFEST)
    technical_reports = manifest.get("technical_reports", [])
    require(
        "docs/audits/INFORME_OPTIMIZACION_CITYLEARN_MADRL_VRAM.md" in technical_reports,
        "workflow_manifest must reference the CityLearn MADRL VRAM optimization report",
        errors,
    )
    require(
        "docs/audits/INFORME_VALIDACION_RECOMPENSAS_MULTI_OBJETIVO_MADRL.md" in technical_reports,
        "workflow_manifest must reference the MADRL multi-objective reward validation report",
        errors,
    )
    for report_path in technical_reports:
        require(project_path(report_path).is_file(), f"Missing technical report referenced by workflow_manifest: {report_path}", errors)

    dataset = manifest.get("dataset", {})
    require(dataset.get("schema_path") == rel(SCHEMA_PATH), "workflow_manifest schema_path is not the Iquitos schema", errors)
    require(dataset.get("buildings") == 17, "workflow_manifest buildings must be 17", errors)
    require(dataset.get("active_csv_files") == 222, "workflow_manifest active_csv_files must be 222", errors)
    require(dataset.get("ev_chargers") == 185, "workflow_manifest ev_chargers must be 185", errors)
    require(dataset.get("ev_v2g_chargers") == 31, "workflow_manifest ev_v2g_chargers must be 31 camioneta V2G tomas", errors)
    require(dataset.get("ev_mode3_physical_units") == 96, "workflow_manifest Mode 3 physical units must be 96", errors)
    require(dataset.get("ev_definition_count") == 1850, "workflow_manifest EV definition count must be 1850", errors)

    required_audits = dataset.get("required_audits", [])
    for audit_name in required_audits:
        if audit_name == "workflow_integrity_manifest.json":
            continue
        require((AUDIT_DIR / audit_name).is_file(), f"Missing audit manifest: outputs/dataset_audit/{audit_name}", errors)

    workflow = manifest.get("workflow", [])
    for stage in workflow:
        for key in ("launcher", "wrapper", "primary_monitor", "legacy_monitor_wrapper", "v2_benchmark", "comparator", "generator"):
            if key in stage:
                require(project_path(stage[key]).exists(), f"Workflow stage {stage.get('stage')} references missing {key}: {stage[key]}", errors)

    training = next((stage for stage in workflow if stage.get("stage") == "training"), {})
    require(training.get("launcher") == "CityLearn/scripts/launch_citylearn_v3_official_training.ps1", "Training launcher is not canonical", errors)
    require(training.get("wrapper") == "scripts/run_citylearn_v3_full_training_visible.ps1", "Training wrapper is not canonical", errors)
    require(training.get("algorithms") == ["happo", "masac", "matd3", "maac"], "Training algorithms are not HAPPO/MASAC/MATD3/MAAC", errors)
    require(training.get("scenarios") == ["E1", "E2", "E3"], "Training scenarios are not E1/E2/E3", errors)
    require(training.get("episodes") == 50, "Training episodes must be 50", errors)
    require(training.get("episode_time_steps") == 8760, "Training episode_time_steps must be 8760", errors)
    require(training.get("num_env_steps") == 438000, "Training num_env_steps must be 438000", errors)
    baseline = training.get("baseline_comparison", {})
    require(baseline.get("mode") == "project_local_citylearn_v2", "Training baseline must use the project-local CityLearn v2 flow", errors)
    require(
        baseline.get("benchmark_script") == "CityLearn/scripts/benchmark_citylearn_v2_agents.py",
        "Training baseline benchmark script is not canonical",
        errors,
    )
    require(
        baseline.get("benchmark_agents_default") == ["baseline", "hour_rbc"],
        "Training baseline agents must be the local CityLearn v2 baseline/hour_rbc defaults",
        errors,
    )
    require(
        baseline.get("sb3_comparison_agents") == ["ppo", "sac", "a2c"],
        "Training must declare CityLearn v2 SB3 PPO/SAC/A2C comparison agents",
        errors,
    )
    sb3_scripts = baseline.get("sb3_comparison_scripts", {})
    for agent, expected_script in {
        "ppo": "CityLearn/scripts/benchmark_citylearn_v2_ppo.py",
        "sac": "CityLearn/scripts/benchmark_citylearn_v2_sac.py",
        "a2c": "CityLearn/scripts/benchmark_citylearn_v2_a2c.py",
    }.items():
        require(sb3_scripts.get(agent) == expected_script, f"Missing canonical SB3 {agent} comparison script in workflow_manifest", errors)
        require(project_path(expected_script).is_file(), f"Missing SB3 comparison script: {expected_script}", errors)
    require(
        "CityLearn v2 central-agent Stable-Baselines3" in str(baseline.get("rule", "")),
        "Training baseline rule must keep PPO/SAC/A2C in CityLearn v2 SB3 comparison flow",
        errors,
    )
    require(training.get("live_output") is False, "Training live_output must default to false for visible parallel monitoring", errors)
    require(training.get("parallel_scenarios") is True, "Training parallel_scenarios must default to true", errors)
    require(training.get("max_concurrent_scenario_jobs") == 2, "Training must request 2 concurrent scenario jobs", errors)
    require(training.get("max_concurrent_heavy_jobs") == 1, "Training must cap heavy MADRL jobs at 1", errors)

    return manifest


def validate_schema(errors: list[str]) -> dict[str, Any]:
    require(SCHEMA_PATH.is_file(), f"Missing {rel(SCHEMA_PATH)}", errors)
    if not SCHEMA_PATH.is_file():
        return {}

    schema = load_json(SCHEMA_PATH)
    buildings = {
        name: building
        for name, building in schema.get("buildings", {}).items()
        if building.get("include", True)
    }
    chargers = [
        charger
        for building in buildings.values()
        for charger in (building.get("chargers") or {}).values()
    ]
    ev_defs = schema.get("electric_vehicles_def", {})
    charger_files = sorted(DATASET_DIR.glob("charger_*.csv"))
    building_files = sorted(DATASET_DIR.glob("Building_*.csv"))
    washing_files = sorted(DATASET_DIR.glob("Washing_Machine_*.csv"))

    require(len(buildings) == 17, f"Schema has {len(buildings)} included buildings, expected 17", errors)
    require(len(chargers) == 185, f"Schema has {len(chargers)} chargers/tomas, expected 185", errors)
    require(len(charger_files) == 185, f"Dataset has {len(charger_files)} charger CSVs, expected 185", errors)
    require(len(ev_defs) == 1850, f"Schema has {len(ev_defs)} EV definitions, expected 1850", errors)
    require(len(building_files) == 17, f"Dataset has {len(building_files)} Building CSVs, expected 17", errors)
    require(len(washing_files) == 17, f"Dataset has {len(washing_files)} Washing_Machine CSVs, expected 17", errors)
    require((DATASET_DIR / "weather.csv").is_file(), "Dataset missing weather.csv", errors)
    require((DATASET_DIR / "pricing.csv").is_file(), "Dataset missing pricing.csv", errors)
    require((DATASET_DIR / "carbon_intensity.csv").is_file(), "Dataset missing carbon_intensity.csv", errors)

    mode3_units = {
        (charger.get("hardware") or {}).get("physical_charger_id")
        for charger in chargers
        if (charger.get("hardware") or {}).get("physical_charger_id")
    }
    socket_counts = {
        (charger.get("hardware") or {}).get("socket_count_per_physical_unit")
        for charger in chargers
    }
    camioneta_chargers = [
        charger
        for charger in chargers
        if ((charger.get("hardware") or {}).get("ev_type") or "").lower() == "camioneta"
    ]
    camioneta_v2g_chargers = [
        charger
        for charger in camioneta_chargers
        if float((charger.get("attributes") or {}).get("max_discharging_power", 0.0) or 0.0) > 0.0
        and (charger.get("hardware") or {}).get("v2g_capable") is True
        and (charger.get("hardware") or {}).get("power_flow_direction") == "bidirectional_v2g"
    ]
    non_camioneta_v2g_chargers = [
        charger
        for charger in chargers
        if ((charger.get("hardware") or {}).get("ev_type") or "").lower() != "camioneta"
        and float((charger.get("attributes") or {}).get("max_discharging_power", 0.0) or 0.0) > 0.0
    ]
    require(len(mode3_units) == 96, f"Schema has {len(mode3_units)} physical Mode 3 units, expected 96", errors)
    require(socket_counts == {2}, f"Mode 3 socket counts are {sorted(socket_counts)}, expected [2]", errors)
    require(len(camioneta_chargers) == 31, f"Schema has {len(camioneta_chargers)} camioneta chargers, expected 31", errors)
    require(len(camioneta_v2g_chargers) == 31, f"Schema has {len(camioneta_v2g_chargers)} V2G camioneta chargers, expected 31", errors)
    require(len(non_camioneta_v2g_chargers) == 0, f"Schema has {len(non_camioneta_v2g_chargers)} non-camioneta V2G chargers, expected 0", errors)

    return {
        "buildings": len(buildings),
        "chargers": len(chargers),
        "charger_csv": len(charger_files),
        "ev_definitions": len(ev_defs),
        "mode3_physical_units": len(mode3_units),
        "camioneta_v2g_chargers": len(camioneta_v2g_chargers),
    }


def validate_training_scripts(errors: list[str]) -> None:
    launch = ROOT / "CityLearn" / "scripts" / "launch_citylearn_v3_official_training.ps1"
    require(launch.is_file(), f"Missing {rel(launch)}", errors)
    if not launch.is_file():
        return

    text = launch.read_text(encoding="utf-8")
    for algorithm in ("happo", "masac", "matd3", "maac"):
        script = ROOT / "CityLearn" / "scripts" / f"train_citylearn_v3_{algorithm}.py"
        require(script.is_file(), f"Missing training script {rel(script)}", errors)
        require(f"train_citylearn_v3_{algorithm}.py" in text, f"Launcher does not reference train_citylearn_v3_{algorithm}.py", errors)

    for script_name in ("benchmark_citylearn_v2_ppo.py", "benchmark_citylearn_v2_sac.py", "benchmark_citylearn_v2_a2c.py"):
        script = ROOT / "CityLearn" / "scripts" / script_name
        require(script.is_file(), f"Missing CityLearn v2 SB3 comparison script {rel(script)}", errors)

    sb3_common = ROOT / "CityLearn" / "scripts" / "benchmark_citylearn_v2_sb3_common.py"
    require(sb3_common.is_file(), f"Missing {rel(sb3_common)}", errors)
    if sb3_common.is_file():
        sb3_text = sb3_common.read_text(encoding="utf-8")
        require("central_agent=True" in sb3_text, "SB3 comparison scripts must use CityLearn v2 central_agent=True", errors)
        require("CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json" in sb3_text, "SB3 comparison scripts must default to the local Iquitos schema", errors)
        require("StableBaselines3Wrapper" in sb3_text, "SB3 comparison scripts must use StableBaselines3Wrapper", errors)

    notebook_path = ROOT / "CityLearn" / "examples" / "madrl_citylearn_v3_tutorial.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook_text = "\n".join("".join(cell.get("source", [])) for cell in notebook.get("cells", []))
    require(
        'CITYLEARN_V2_BENCHMARKS = ["PPO", "SAC", "A2C"]' in notebook_text,
        "Notebook must declare PPO/SAC/A2C as the only CityLearn v2 SB3 benchmarks",
        errors,
    )
    require(
        "Nota MAPPO (baseline)" not in notebook_text and "baselines MADRL opcionales" not in notebook_text,
        "Notebook must not describe MAPPO/MADDPG as official baselines",
        errors,
    )

    colab_launcher = ROOT / "CityLearn" / "scripts" / "colab_a100_official_launcher.py"
    require(colab_launcher.is_file(), f"Missing {rel(colab_launcher)}", errors)
    if colab_launcher.is_file():
        colab_launcher_text = colab_launcher.read_text(encoding="utf-8")
        require("--include-baselines" not in colab_launcher_text, "Colab launcher must not expose MAPPO/MADDPG baseline flag", errors)
        require('"name": "mappo"' not in colab_launcher_text, "Colab launcher must not plan MAPPO v3 jobs", errors)
        require('"name": "maddpg"' not in colab_launcher_text, "Colab launcher must not plan MADDPG v3 jobs", errors)
        require(
            'CITYLEARN_V2_BENCHMARKS = ("PPO", "SAC", "A2C")' in colab_launcher_text,
            "Colab launcher must document PPO/SAC/A2C as the only comparison benchmarks",
            errors,
        )

    require("[string]$EndAtAlgorithm" in text, "Launcher must support EndAtAlgorithm for single-stage runs", errors)
    require("tools\\check_training_dataset_ready.py" in text, "Launcher does not run dataset readiness gate", errors)
    require("local_8gb_safety_mode" in text, "Launcher does not record local 8GB VRAM safety mode", errors)
    require("$MaxConcurrentScenarioJobs = 2" in text, "Launcher does not cap scenario concurrency at 2 for local 8GB GPU", errors)
    require("$MaxConcurrentHeavyJobs = 1" in text, "Launcher does not cap heavy algorithm concurrency at 1 for local 8GB GPU", errors)
    require("local_8gb_concurrency_note" in text, "Launcher does not record local 8GB concurrency policy", errors)
    require("LiveOutput requires sequential" in text, "Launcher does not explain LiveOutput sequential mode", errors)

    visible_wrapper = ROOT / "scripts" / "run_citylearn_v3_full_training_visible.ps1"
    quick_launcher = ROOT / "scripts" / "training_launcher_window.ps1"
    resume_launcher = ROOT / "scripts" / "training_resume_window.ps1"
    for wrapper in (visible_wrapper, quick_launcher, resume_launcher):
        require(wrapper.is_file(), f"Missing visible training wrapper {rel(wrapper)}", errors)
    if visible_wrapper.is_file():
        wrapper_text = visible_wrapper.read_text(encoding="utf-8")
        require("[bool]$LiveOutput = $false" in wrapper_text, "Visible wrapper must default LiveOutput to false for parallel scenario stages", errors)
    for wrapper in (quick_launcher, resume_launcher):
        if wrapper.is_file():
            wrapper_text = wrapper.read_text(encoding="utf-8")
            require("-LiveOutput" not in wrapper_text, f"{rel(wrapper)} must omit LiveOutput by default so the launcher switch remains false", errors)
            require("-MaxConcurrentScenarioJobs 2" in wrapper_text, f"{rel(wrapper)} must request 2 scenario jobs on local 8GB profile", errors)


def validate_active_defaults(errors: list[str]) -> None:
    for relative in ACTIVE_FILES_WITH_NO_STALE_DEFAULTS:
        path = ROOT / relative
        require(path.is_file(), f"Missing active workflow file: {relative}", errors)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for stale in STALE_ROOTS_FOR_ACTIVE_DEFAULTS:
            if stale in text:
                errors.append(f"Active workflow file still contains stale output default {stale}: {relative}")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    require('readme = "README.md"' in pyproject, "pyproject readme must point to README.md", errors)
    require('"numpy>=1.23.5,<2.0"' in pyproject, "pyproject numpy range must match CityLearn v3 environment", errors)


def validate_audits(errors: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    status_expectations = {
        "csv_integrity_manifest.json": ("status", "ok"),
        "training_dataset_ready_manifest.json": ("status", "ready"),
        "iquitos_citylearn_v3_dataset_evaluation.json": ("ok", True),
    }
    for filename, (key, expected) in status_expectations.items():
        path = AUDIT_DIR / filename
        require(path.is_file(), f"Missing audit file {rel(path)}", errors)
        if not path.is_file():
            continue
        payload = load_json(path)
        actual = payload.get(key)
        require(actual == expected, f"{filename} has {key}={actual!r}, expected {expected!r}", errors)
        summary[filename] = actual
    return summary


def validate_latest_pointer() -> dict[str, Any]:
    if not LATEST_OUTPUT_POINTER.is_file():
        return {"present": False, "note": "No active training pointer yet; launcher will create it."}

    value = LATEST_OUTPUT_POINTER.read_text(encoding="utf-8-sig").strip()
    target = project_path(value)
    return {
        "present": True,
        "value": value,
        "target_exists": target.exists(),
        "status_exists": (target / "official_full_status.json").is_file(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=DEFAULT_MANIFEST_OUT,
        help="Optional JSON report path. Defaults to outputs/dataset_audit/workflow_integrity_manifest.json.",
    )
    args = parser.parse_args()
    manifest_out = args.manifest_out if args.manifest_out.is_absolute() else ROOT / args.manifest_out

    errors: list[str] = []
    manifest = validate_workflow_manifest(errors)
    schema_summary = validate_schema(errors)
    validate_training_scripts(errors)
    validate_active_defaults(errors)
    audit_summary = validate_audits(errors)
    latest_pointer = validate_latest_pointer()

    report = {
        "ok": not errors,
        "project_root": str(ROOT),
        "workflow_manifest": manifest.get("purpose"),
        "schema_summary": schema_summary,
        "audit_summary": audit_summary,
        "latest_output_pointer": latest_pointer,
        "errors": errors,
    }
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
