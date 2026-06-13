"""Verify that the Iquitos dataset, training and evidence workflow is wired.

This check is static plus lightweight JSON/schema inspection. It does not start
training and it does not create training artifacts; it fails when a canonical
path in the root workflow is missing, stale or disconnected.
"""

from __future__ import annotations

import json
import sys
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
    dataset = manifest.get("dataset", {})
    require(dataset.get("schema_path") == rel(SCHEMA_PATH), "workflow_manifest schema_path is not the Iquitos schema", errors)
    require(dataset.get("buildings") == 17, "workflow_manifest buildings must be 17", errors)
    require(dataset.get("active_csv_files") == 222, "workflow_manifest active_csv_files must be 222", errors)
    require(dataset.get("ev_chargers") == 185, "workflow_manifest ev_chargers must be 185", errors)
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
    require(training.get("episodes") == 5, "Training episodes must be 5", errors)
    require(training.get("episode_time_steps") == 8760, "Training episode_time_steps must be 8760", errors)

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
    require(len(mode3_units) == 96, f"Schema has {len(mode3_units)} physical Mode 3 units, expected 96", errors)
    require(socket_counts == {2}, f"Mode 3 socket counts are {sorted(socket_counts)}, expected [2]", errors)

    return {
        "buildings": len(buildings),
        "chargers": len(chargers),
        "charger_csv": len(charger_files),
        "ev_definitions": len(ev_defs),
        "mode3_physical_units": len(mode3_units),
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

    require("tools\\check_training_dataset_ready.py" in text, "Launcher does not run dataset readiness gate", errors)
    require("local_8gb_safety_mode" in text, "Launcher does not record local 8GB VRAM safety mode", errors)
    require("$MaxConcurrentScenarioJobs = 1" in text, "Launcher does not force scenario concurrency 1 for local 8GB GPU", errors)
    require("LiveOutput requires sequential" in text, "Launcher does not explain LiveOutput sequential mode", errors)


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
