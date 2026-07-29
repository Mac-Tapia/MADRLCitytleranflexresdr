#!/usr/bin/env python3
"""Validate 12 MADRL jobs under OUTPUT_ROOT using KPI-grounded completion rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "CityLearn" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from citylearn_v3_training_common import (  # noqa: E402
    build_jobs_resume_report,
    job_launcher_completion_blockers,
    job_meets_launcher_complete_requirements,
    preview_job_launcher_decision,
    resolve_existing_job_run_dir,
)

ALGOS = ("happo", "masac", "matd3", "maac")
SCENS = ("E1", "E2", "E3")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path, help="Run root, e.g. outputs/madrl_v3_...")
    parser.add_argument("--target-episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary")
    args = parser.parse_args()

    root = args.output_root.resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2

    rows = []
    complete = 0
    for algo in ALGOS:
        for scen in SCENS:
            run_dir = resolve_existing_job_run_dir(root, algo, scen, args.seed)
            if run_dir is None:
                rows.append(
                    {
                        "algorithm": algo.upper(),
                        "scenario": scen,
                        "ok": False,
                        "detail": "run_dir missing",
                    }
                )
                continue
            ok = job_meets_launcher_complete_requirements(
                run_dir,
                target_episodes=args.target_episodes,
                output_root=root,
            )
            preview = preview_job_launcher_decision(
                run_dir,
                algorithm=algo,
                target_episodes=args.target_episodes,
                output_root=root,
            )
            blockers = [] if ok else job_launcher_completion_blockers(
                run_dir,
                target_episodes=args.target_episodes,
                output_root=root,
            )
            if ok:
                complete += 1
            rows.append(
                {
                    "algorithm": algo.upper(),
                    "scenario": scen,
                    "ok": ok,
                    "action": preview.get("action"),
                    "status_line": preview.get("status_line"),
                    "blockers": blockers,
                    "run_dir": str(run_dir),
                }
            )

    summary = {
        "output_root": str(root),
        "target_episodes": args.target_episodes,
        "jobs_complete_kpi": complete,
        "jobs_total": len(rows),
        "all_complete": complete == len(rows),
        "jobs": rows,
    }
    report = build_jobs_resume_report(
        root,
        target_episodes=args.target_episodes,
        seed=args.seed,
    )
    summary["resume_report"] = {
        "completed": report.get("completed"),
        "resumable": report.get("resumable"),
        "pending": report.get("pending"),
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"OUTPUT_ROOT: {root}")
        print(f"KPI-complete: {complete}/{len(rows)} (target {args.target_episodes} ep/job)")
        print(f"Resume report: COMPLETOS={report.get('completed')} REANUDABLES={report.get('resumable')}")
        for row in rows:
            mark = "OK" if row["ok"] else "INCOMPLETE"
            print(f"  [{mark}] {row['algorithm']}/{row['scenario']}: {row.get('status_line')}")
            for b in row.get("blockers") or []:
                print(f"         blocker: {b}")

    return 0 if summary["all_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
