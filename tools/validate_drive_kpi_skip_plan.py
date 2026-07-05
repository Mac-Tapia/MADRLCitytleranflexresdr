#!/usr/bin/env python3
"""Validate --skip-completed plan against real Drive KPI extracts (madrl_v3_20260627_164047)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "CityLearn" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from citylearn_v3_training_common import (  # noqa: E402
    build_jobs_resume_report,
    validate_canonical_colab_skip_plan,
)

KPI_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
EXPECTED = {
    ("happo", "E1"): "resume",
    ("happo", "E2"): "resume",
    ("happo", "E3"): "resume",
    ("masac", "E1"): "skip",
    ("masac", "E2"): "skip",
    ("masac", "E3"): "skip",
    ("matd3", "E1"): "skip",
    ("matd3", "E2"): "skip",
    ("matd3", "E3"): "skip",
    ("maac", "E1"): "skip",
    ("maac", "E2"): "skip",
    ("maac", "E3"): "skip",
}


def build_run_from_kpis(kpi_dir: Path, run_root: Path) -> int:
    copied = 0
    for algo in ("happo", "masac", "matd3", "maac"):
        for scen in ("E1", "E2", "E3"):
            src = kpi_dir / f"{algo}_{scen}_results.json"
            if not src.is_file():
                continue
            dest = run_root / algo.upper() / scen / "data"
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / "results.json")
            copied += 1
            if algo == "happo":
                ckpt = run_root / algo.upper() / scen / "checkpoints" / "models"
                ckpt.mkdir(parents=True, exist_ok=True)
                (ckpt / "actor_agent0.pt").write_bytes(b"stub")
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kpi-dir",
        type=Path,
        default=KPI_DIR,
        help="Directory with happo_E1_results.json etc.",
    )
    parser.add_argument("--target-episodes", type=int, default=50)
    args = parser.parse_args()

    if not args.kpi_dir.is_dir():
        print(f"ERROR: KPI dir missing: {args.kpi_dir}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        run_root = Path(tmp) / "madrl_v3_20260627_164047"
        n = build_run_from_kpis(args.kpi_dir, run_root)
        if n == 0:
            print("ERROR: no KPI files copied", file=sys.stderr)
            return 2

        report = build_jobs_resume_report(
            run_root,
            target_episodes=args.target_episodes,
            happo_rollout_threads=12,
            seed=0,
        )

    print("=" * 72)
    print("  SKIP PLAN (real Drive KPI copies -> canonical ALGO/Ex/data/results.json)")
    print("=" * 72)
    print(
        f"  omitir={report['completed']}  reanudar={report['resumable']}  "
        f"pendientes={report['pending']}  restart={report['restart_fresh']}"
    )
    print("-" * 72)

    validation = validate_canonical_colab_skip_plan(report)
    mismatches = list(validation.get("mismatches") or [])
    for row in report["jobs"]:
        algo = str(row["algorithm"]).lower()
        scen = str(row["scenario"]).upper()
        action = str(row["action"])
        exp = EXPECTED.get((algo, scen), "?")
        ok = action == exp
        mark = "OK" if ok else "MISMATCH"
        print(f"  [{mark}] {algo.upper()}/{scen}: {action} (expected {exp})")

    print("=" * 72)
    if not validation.get("ok"):
        print("FAIL: plan does not match Drive ground truth")
        for item in mismatches:
            print(
                f"  {item.get('job')}: expected {item.get('expected')}, "
                f"got {item.get('actual')} — {item.get('status_line')}"
            )
        return 1

    if report["completed"] != 9 or report["resumable"] != 3:
        print(
            f"FAIL: expected 9 skip + 3 resume, got "
            f"{report['completed']} skip + {report['resumable']} resume"
        )
        return 1

    print("PASS: only HAPPO×3 should run; MASAC/MATD3/MAAC×3 skip on relaunch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
