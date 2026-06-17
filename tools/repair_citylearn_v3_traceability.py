"""Repair traceability metadata for existing CityLearn v3 MADRL outputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "CityLearn" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from citylearn_v3_training_common import (  # noqa: E402
    _artifact_consistency_audit,
    _as_int,
    _episode_summaries,
    write_json,
)


def _read_json(path: Path) -> Dict[str, object]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> List[Dict[str, object]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _run_dirs(root: Path) -> Iterable[Path]:
    if (root / "data" / "results.json").is_file() or (root / "results.json").is_file():
        yield root
        return

    for path in sorted(root.glob("*/*_seed_*")):
        if path.is_dir() and ((path / "data" / "results.json").is_file() or (path / "results.json").is_file()):
            yield path


def _json_mirrors(run_dir: Path, name: str) -> List[Path]:
    return [path for path in (run_dir / "data" / name, run_dir / name) if path.is_file()]


def _resolve_manifest_path(path_text: object) -> Optional[Path]:
    if not path_text:
        return None
    path = Path(str(path_text))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _repair_guard_payload(payload: Mapping[str, object], run_dir: Path, now: str) -> bool:
    hyperparameters = payload.get("hyperparameters")
    if not isinstance(hyperparameters, dict):
        return False

    guard = hyperparameters.get("finite_optimizer_step_guard")
    if not isinstance(guard, dict):
        return False

    audit_path = _resolve_manifest_path(guard.get("audit_path"))
    if audit_path is None:
        return False

    created = False
    if not audit_path.is_file():
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": now,
            "event": "finite_optimizer_step_guard_audit_file_repaired",
            "installed_optimizers": guard.get("installed_optimizers"),
            "run_dir": str(run_dir),
            "reason": "manifest_referenced_missing_audit_file",
        }
        with audit_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        created = True

    guard["audit_file_exists"] = audit_path.is_file()
    guard["audit_initialized"] = True
    if created:
        guard["audit_file_repaired"] = True
        guard["audit_file_repaired_at"] = now
    return created


def _repair_guard_manifests(run_dir: Path, now: str) -> int:
    created_count = 0
    for path in (
        *_json_mirrors(run_dir, "checkpoint_manifest.json"),
        *_json_mirrors(run_dir, "results.json"),
        *_json_mirrors(run_dir, "training_summary.json"),
    ):
        payload = _read_json(path)
        if not payload:
            continue
        if _repair_guard_payload(payload, run_dir, now):
            created_count += 1
        write_json(path, payload)
    return created_count


def repair_run(run_dir: Path) -> Dict[str, object]:
    data_dir = run_dir / "data"
    results_paths = _json_mirrors(run_dir, "results.json")
    results = _read_json(results_paths[0]) if results_paths else {}
    if not results:
        return {"run_dir": str(run_dir), "status": "skipped", "reason": "missing_results_json"}

    timeseries_rows = _read_csv(data_dir / "timeseries.csv") or _read_csv(run_dir / "timeseries.csv")
    trace_rows = _read_csv(data_dir / "trace.csv") or _read_csv(run_dir / "trace.csv")
    episode_summaries = _episode_summaries(timeseries_rows)
    report = results.get("citylearn_v3_report")
    if not isinstance(report, dict):
        report = results

    hyperparameters = results.get("hyperparameters") if isinstance(results.get("hyperparameters"), dict) else {}
    expected_episode_time_steps = _as_int(results.get("episode_time_steps"))
    expected_episodes = _as_int(results.get("episodes")) or _as_int(hyperparameters.get("episodes"))

    artifact_audit = _artifact_consistency_audit(
        report=report,
        timeseries_rows=timeseries_rows,
        trace_rows=trace_rows,
        episode_summaries=episode_summaries,
        expected_episode_time_steps=expected_episode_time_steps,
        expected_episodes=expected_episodes,
    )
    traceability = {
        "status": artifact_audit.get("status"),
        "planned_environment_steps": artifact_audit.get("expected_timeseries_rows"),
        "recorded_environment_steps": len(timeseries_rows),
        "environment_step_delta_vs_plan": artifact_audit.get("timeseries_row_delta_vs_expected"),
        "completed_episode_count": artifact_audit.get("completed_episode_count_from_timeseries"),
        "expected_episode_count": artifact_audit.get("expected_episodes"),
        "warnings": artifact_audit.get("warnings", []),
    }

    for path in results_paths:
        payload = _read_json(path)
        payload["artifact_audit"] = artifact_audit
        payload["traceability"] = traceability
        payload["episodes_recorded"] = len(episode_summaries)
        payload["timeseries_rows"] = len(timeseries_rows)
        payload["trace_rows"] = len(trace_rows)
        write_json(path, payload)

    for path in _json_mirrors(run_dir, "training_summary.json"):
        payload = _read_json(path)
        artifacts = payload.get("artifacts")
        if isinstance(artifacts, dict):
            artifacts["artifact_audit"] = artifact_audit
        payload["traceability"] = traceability
        write_json(path, payload)

    audit_paths = [data_dir / "artifact_audit.json"]
    root_audit_path = run_dir / "artifact_audit.json"
    if root_audit_path.is_file():
        audit_paths.append(root_audit_path)
    for path in audit_paths:
        write_json(path, artifact_audit)

    now = datetime.now(timezone.utc).isoformat()
    created_guard_files = _repair_guard_manifests(run_dir, now)
    return {
        "run_dir": str(run_dir),
        "status": artifact_audit.get("status"),
        "timeseries_rows": len(timeseries_rows),
        "expected_timeseries_rows": artifact_audit.get("expected_timeseries_rows"),
        "delta": artifact_audit.get("timeseries_row_delta_vs_expected"),
        "warning_count": len(artifact_audit.get("warnings", [])),
        "created_guard_files": created_guard_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", nargs="+", help="Output root or single run directory to repair.")
    args = parser.parse_args()

    results = []
    for root_text in args.output_root:
        root = Path(root_text)
        for run_dir in _run_dirs(root):
            results.append(repair_run(run_dir))

    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
