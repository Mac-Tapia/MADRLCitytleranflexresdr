"""Regenerate real Drive-backed training figures from Colab result JSON files.

The Drive mirror for this run contains objective reports, core KPIs, and real
episode summaries. It does not contain the original full timeseries/trace rows,
so this script intentionally skips figures that require those missing rows.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
CITYLEARN_SCRIPTS = REPO / "CityLearn" / "scripts"
if str(CITYLEARN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CITYLEARN_SCRIPTS))

from citylearn_v3_training_common import (  # noqa: E402
    _write_training_figures_and_tables,
    ensure_artifact_layout,
)


RUN_ID = "madrl_v3_20260627_164047"
KPIS_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
OUT_ROOT = REPO / "outputs" / RUN_ID
ALGOS = ("MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_core_kpis(algo: str, scenario: str) -> list[dict[str, Any]]:
    path = KPIS_DIR / f"{algo.lower()}_{scenario}_core_kpis.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def build_timeseries_rows(results: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summaries = list(results.get("episode_summaries") or [])

    for summary in summaries:
        episode = int(summary.get("episode", len(rows)))
        last_step = int(float(summary.get("last_global_step", episode)))
        reward_sum = float(summary.get("reward_sum_total", 0.0))
        reward_mean = float(summary.get("reward_mean_average", 0.0))
        rows.append(
            {
                "episode": episode,
                "episode_step": int(float(summary.get("last_episode_step", 8759))),
                "global_step": last_step,
                "reward_sum": reward_sum,
                "reward_mean": reward_mean,
            }
        )
    return rows


def build_trace_rows(_results: dict[str, Any]) -> list[dict[str, Any]]:
    return []


def remove_stale_non_drive_figures(figures_dir: Path) -> None:
    for name in (
        "citylearn_v2_district_timeseries.png",
        "exploration_action_l2.png",
        "agent_reward_contribution.png",
    ):
        path = figures_dir / name
        if path.exists():
            path.unlink()


def normalize_result_for_local_layout(results: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    local = dict(results)
    local["output_dir"] = str(run_dir)
    local["source_drive_output_dir"] = results.get("output_dir")
    local["drive_backed_figures"] = True
    local["drive_figure_note"] = (
        "Figures regenerated only from real Drive episode_summaries, citylearn_v3_report, "
        "and core KPI CSV files. Figures requiring unavailable full timeseries/trace rows "
        "are intentionally skipped."
    )
    return local


def regenerate_one(algo: str, scenario: str) -> dict[str, Any]:
    source = KPIS_DIR / f"{algo.lower()}_{scenario}_results.json"
    if not source.exists():
        return {
            "algorithm": algo,
            "scenario": scenario,
            "status": "missing_results_json",
            "source": str(source),
        }

    results = read_json(source)
    run_dir = OUT_ROOT / algo / scenario
    dirs = ensure_artifact_layout(run_dir)
    remove_stale_non_drive_figures(dirs["figures"])
    data_dir = dirs["data"]
    local_results = normalize_result_for_local_layout(results, run_dir)
    timeseries_rows = build_timeseries_rows(results)
    trace_rows = build_trace_rows(results)
    episode_summaries = list(results.get("episode_summaries") or [])
    report = results.get("citylearn_v3_report") or results

    write_json(data_dir / "results.json", local_results)
    write_json(data_dir / "training_summary.json", local_results)
    write_json(data_dir / "artifact_audit.json", results.get("artifact_audit") or {})
    write_csv(data_dir / "timeseries.csv", timeseries_rows)
    write_csv(data_dir / "trace.csv", trace_rows)

    extra_tables = {
        "drive_core_kpis": read_core_kpis(algo, scenario),
        "drive_episode_summary": episode_summaries,
    }
    manifest = _write_training_figures_and_tables(
        dirs=dirs,
        report=report,
        timeseries_rows=timeseries_rows,
        trace_rows=trace_rows,
        episode_summaries=episode_summaries,
        checkpoints=[],
        extra_tables=extra_tables,
    )
    return {
        "algorithm": algo,
        "scenario": scenario,
        "status": "ok",
        "run_dir": str(run_dir),
        "figure_count": manifest.get("figure_count"),
        "table_count": manifest.get("table_count"),
        "figure_errors": manifest.get("figure_errors"),
    }


def main() -> int:
    outputs = []
    for algo in ALGOS:
        for scenario in SCENARIOS:
            outputs.append(regenerate_one(algo, scenario))

    skipped_happo = {
        "algorithm": "HAPPO",
        "status": "skipped_completed_with_salvage_without_kpis",
        "reason": "HAPPO has 49/50 episodes and no objective KPI report in Drive results.",
    }
    summary = {
        "run_id": RUN_ID,
        "output_root": str(OUT_ROOT),
        "generated": outputs,
        "skipped": [skipped_happo],
    }
    write_json(OUT_ROOT / "resumen_comparativo" / "drive_training_figures_manifest.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
