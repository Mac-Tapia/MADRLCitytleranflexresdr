"""Build a reviewable sensitivity manifest; never launch training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

import yaml

from uc3m.application.sensitivity import ExperimentMatrix, generate_weight_grid
from uc3m.domain.objectives import HierarchyLevels


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT / "configs" / "experiments" / "objective_weight_sensitivity.yaml"
)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    payload = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported sensitivity schema_version")
    if payload.get("execution", {}).get("launch_authorized") is not False:
        raise ValueError("Sensitivity planning must remain launch_authorized=false")

    levels = HierarchyLevels(residual=float(payload["grid"]["minimum_weight"]))
    policies = generate_weight_grid(levels, step=float(payload["grid"]["step"]))
    matrix = ExperimentMatrix(
        algorithms=tuple(str(value) for value in payload["algorithms"]),
        policies=policies,
        seeds=tuple(int(value) for value in payload["seeds"]),
        timesteps_per_run=int(payload["timesteps_per_run"]),
        study_kind=str(payload["study_kind"]),  # type: ignore[arg-type]
    )
    manifest = matrix.as_manifest()
    manifest["config"] = args.config.as_posix()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
