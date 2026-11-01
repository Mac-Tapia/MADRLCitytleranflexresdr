"""Agrega los KPI de la campaña MADRL modular (Colab) y genera el resumen comparativo.

Las carpetas de cada tratamiento se localizan con el catálogo de resultados
(``uc3m.application.evaluation.results_catalog``): ``--results-root``, luego
``MADRL_RESULTS_ROOT`` y luego ``outputs/campaign``. Por tratamiento se leen
``<E*>/figures/tables/core_kpis.csv`` y ``<E*>/data/results.json``. Si falta un
tratamiento verificado o su ``core_kpis.csv``, el script termina con código 2 y
no escribe ranking: no rellena KPI ausentes.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from uc3m.application.evaluation.results_catalog import (  # noqa: E402
    AmbiguousCampaign,
    campaign_layout,
    discover_runs,
    resolve_results_root,
)

ALGOS = ("happo", "masac", "matd3", "maac")
SCENARIOS = ("E1", "E2", "E3")
TARGET_EPISODES = 50
SUMMARY_SUBDIR = Path("resumen_comparativo")

Layout = dict[tuple[str, str], Path]


class MissingTreatments(FileNotFoundError):
    """A required treatment has no verified run or lacks a KPI file."""


def locate_treatments(results_root: Path, seed: int = 0) -> Layout:
    layout = campaign_layout(results_root, seed=seed)
    statuses = {
        (run.algorithm, run.scenario): run.status
        for run in discover_runs(results_root, verified_only=False)
        if run.seed == seed
    }
    missing: list[str] = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            key = (algo.upper(), scen)
            if key not in layout:
                status = statuses.get(key)
                missing.append(f"{key[0]} {scen}" + (f" (status={status})" if status else ""))
            elif not (core_kpis_path(layout, algo, scen)).is_file():
                missing.append(f"{key[0]} {scen} (missing figures/tables/core_kpis.csv)")
            elif not (results_path(layout, algo, scen)).is_file():
                missing.append(f"{key[0]} {scen} (missing data/results.json)")
    if missing:
        raise MissingTreatments(
            f"{results_root}: no verified run for seed {seed}: " + ", ".join(missing)
        )
    return {key: layout[key] for key in ((a.upper(), s) for a in ALGOS for s in SCENARIOS)}


def core_kpis_path(layout: Layout, algo: str, scen: str) -> Path:
    return layout[(algo.upper(), scen)] / "figures" / "tables" / "core_kpis.csv"


def results_path(layout: Layout, algo: str, scen: str) -> Path:
    return layout[(algo.upper(), scen)] / "data" / "results.json"


def run_id_of(layout: Layout, algo: str, scen: str) -> str:
    return layout[(algo.upper(), scen)].parent.name


def read_core_kpis(layout: Layout, algo: str, scen: str) -> dict[str, float] | None:
    path = core_kpis_path(layout, algo, scen)
    if not path.exists():
        return None
    data: dict[str, float] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            val = (row.get("value") or "").strip()
            if not val:
                continue
            data[row["kpi"]] = float(val)
    return data


def read_episodes(layout: Layout, algo: str, scen: str) -> int | None:
    path = results_path(layout, algo, scen)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    recorded = payload.get("episodes_recorded")
    if recorded is not None:
        return int(recorded)
    hp = payload.get("hyperparameters") or {}
    jr = hp.get("job_resume") or {}
    if jr.get("completed_episodes") is not None:
        return int(jr["completed_episodes"])
    ep = payload.get("episodes")
    return int(ep) if ep else None


def flex_composite(kpis: dict[str, float]) -> float:
    return (
        kpis["peak_average"]
        + kpis["ramping_average"]
        + kpis["one_minus_load_factor_average"]
    ) / 3.0


def norm_lower_better(values: dict[str, float]) -> dict[str, float]:
    lo, hi = min(values.values()), max(values.values())
    if hi <= lo:
        return {k: 0.5 for k in values}
    return {k: 1.0 - (v - lo) / (hi - lo) for k, v in values.items()}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--results-root",
        type=Path,
        default=None,
        help="Campaign results root (default: MADRL_RESULTS_ROOT, then outputs/campaign)",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Default: <results-root>/{SUMMARY_SUBDIR.as_posix()}",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    results_root = resolve_results_root(args.results_root)
    out_run = args.output_dir or results_root / SUMMARY_SUBDIR
    try:
        layout = locate_treatments(results_root, seed=args.seed)
    except (MissingTreatments, AmbiguousCampaign) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    flex_raw: dict[str, float] = {}
    co2_raw: dict[str, float] = {}
    cost_raw: dict[str, float] = {}
    rows: list[dict] = []

    for algo in ALGOS:
        e1, e2, e3 = (read_core_kpis(layout, algo, s) for s in SCENARIOS)
        ep = {s: read_episodes(layout, algo, s) for s in SCENARIOS}
        if e1:
            flex_raw[algo.upper()] = flex_composite(e1)
        if e2 and "carbon_emissions_delta" in e2:
            co2_raw[algo.upper()] = e2["carbon_emissions_delta"]
        if e3 and "electricity_cost_delta" in e3:
            cost_raw[algo.upper()] = e3["electricity_cost_delta"]

        for scen, kpis in zip(SCENARIOS, (e1, e2, e3)):
            if not kpis:
                continue
            rows.append(
                {
                    "run_id": run_id_of(layout, algo, scen),
                    "algorithm": algo.upper(),
                    "scenario": scen,
                    "episodes": ep.get(scen),
                    **{k: kpis.get(k) for k in kpis},
                }
            )

    nf = norm_lower_better(flex_raw)
    nc = norm_lower_better(co2_raw)
    nt = norm_lower_better(cost_raw)

    ranking = []
    for algo in sorted(set(nf) | set(nc) | set(nt)):
        s1 = nf.get(algo, 0.0)
        s2 = nc.get(algo, 0.0)
        s3 = nt.get(algo, 0.0)
        mean = (s1 + s2 + s3) / 3.0
        ranking.append(
            {
                "algorithm": algo,
                "score_oe1_flex": round(s1, 4),
                "score_oe2_co2": round(s2, 4),
                "score_oe3_cost": round(s3, 4),
                "score_global": round(mean, 4),
                "episodes_e1": read_episodes(layout, algo.lower(), "E1"),
                "episodes_e2": read_episodes(layout, algo.lower(), "E2"),
                "episodes_e3": read_episodes(layout, algo.lower(), "E3"),
            }
        )
    ranking.sort(key=lambda x: -x["score_global"])
    for i, item in enumerate(ranking, 1):
        item["rank"] = i
        item["selected"] = i == 1

    episode_coverage = [
        {
            "algorithm": algo.upper(),
            "scenario": scen,
            "run_id": run_id_of(layout, algo, scen),
            "episodes_recorded": read_episodes(layout, algo, scen),
            "target_episodes": TARGET_EPISODES,
        }
        for algo in ALGOS
        for scen in SCENARIOS
    ]
    incomplete = [
        f"{item['algorithm']} {item['scenario']}"
        for item in episode_coverage
        if item["episodes_recorded"] != TARGET_EPISODES
    ]

    best = ranking[0]["algorithm"] if ranking else None

    report = {
        "mejor_madrl": best,
        "fuente": "modular_campaign_results_catalog",
        "results_root": str(results_root),
        "seed": args.seed,
        "run_ids": {
            f"{algo.upper()}/{scen}": run_id_of(layout, algo, scen)
            for algo in ALGOS
            for scen in SCENARIOS
        },
        "target_episodes": TARGET_EPISODES,
        "algorithms_in_study": ["HAPPO", "MASAC", "MATD3", "MAAC"],
        "episode_coverage": episode_coverage,
        "treatments_below_target_episodes": incomplete,
        "ranking_with_kpis": ranking,
        "ranking": ranking,
        "kpis_primarios": {
            "flex_composite_e1": flex_raw,
            "co2_delta_kg_e2": co2_raw,
            "cost_delta_eur_e3": cost_raw,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_run.mkdir(parents=True, exist_ok=True)
    (out_run / "best_madrl_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    csv_path = out_run / "comparison_metrics_colab.csv"
    if rows:
        fields = sorted({k for r in rows for k in r})
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    sel_path = out_run / "best_madrl_selection.csv"
    with sel_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "algorithm",
                "score_global",
                "score_oe1_flex",
                "score_oe2_co2",
                "score_oe3_cost",
                "selected",
            ],
        )
        writer.writeheader()
        for item in ranking:
            writer.writerow(
                {
                    "rank": item["rank"],
                    "algorithm": item["algorithm"],
                    "score_global": item["score_global"],
                    "score_oe1_flex": item["score_oe1_flex"],
                    "score_oe2_co2": item["score_oe2_co2"],
                    "score_oe3_cost": item["score_oe3_cost"],
                    "selected": item["selected"],
                }
            )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
