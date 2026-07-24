#!/usr/bin/env python
"""Run the full non-parametric MADRL comparison battery (OE.1/OE.2/OE.3 + OG).

Implements the methodology sections 1–8 against **per-seed** KPIs (canonical
``n_seeds=12``) or illustrative synthetic seeds:

  OE (per scenario): Shapiro → Fligner → KW → ε² → Dunn-Holm → Cliff δ → winner rule
  OG (global): Friedman → Kendall W → Nemenyi → TOPSIS (+ Friedman validation)

The statistical unit of analysis is an independent training seed (not an
episode within a run). Prefer CSVs with a ``seed`` column, or a run root with
``{ALGO}/{E*}_seed_{k}/data/results.json``.

Usage (from repo root):

    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --complementary
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --illustrative-only
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --episodes-csv path\\to\\district_episode_kpis.csv
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --run-root outputs\\my_run
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --smoke
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from uc3m.multicriteria.scenarios import DEFAULT_PROTOCOL

# Canonical campaign: 12 independent seeds (0..11).
N_SEEDS = int(DEFAULT_PROTOCOL.n_seeds)

# Default OE metric mapping from district_episode_kpis.csv
# E1 flexibility → reward_mean (higher better)
# E2 CO2 → district_emission (lower better)
# E3 cost → district_cost (lower better)
DEFAULT_OE_SPECS: Dict[str, Dict[str, Any]] = {
    "OE.1": {
        "scenario": "E1",
        "metric": "reward_mean",
        "higher_is_better": True,
        "label": "flexibilidad energética",
    },
    "OE.2": {
        "scenario": "E2",
        "metric": "district_emission",
        "higher_is_better": False,
        "label": "emisiones de CO2",
    },
    "OE.3": {
        "scenario": "E3",
        "metric": "district_cost",
        "higher_is_better": False,
        "label": "costos energéticos",
    },
}

DEFAULT_EPISODES = (
    REPO
    / "outputs"
    / "_drive_madrl"
    / "full_data"
    / "analysis_real_drive"
    / "tables"
    / "district_episode_kpis.csv"
)

# Equal AHP-style weights for the three OE axes in OG TOPSIS (documented default).
DEFAULT_TOPSIS_WEIGHTS = {"OE.1": 1.0 / 3.0, "OE.2": 1.0 / 3.0, "OE.3": 1.0 / 3.0}

_SEED_DIR_RE = re.compile(r"^(?P<scenario>E[123])_seed_(?P<seed>\d+)$", re.IGNORECASE)


def _illustrative_oe_groups(
    n_per_algo: int = N_SEEDS,
    seed: int = 0,
) -> Dict[str, Dict[str, List[float]]]:
    """Synthetic seed spreads for smoke / offline demos (4 algorithms × 3 OE × n seeds)."""

    rng = np.random.default_rng(seed)
    # Means chosen so MAAC tends to win cost, HAPPO flex, MATD3 mid CO2.
    centers = {
        "OE.1": {"HAPPO": -0.55, "MAAC": -0.62, "MASAC": -0.70, "MATD3": -0.65},  # reward (higher better)
        "OE.2": {"HAPPO": 900.0, "MAAC": 850.0, "MASAC": 980.0, "MATD3": 820.0},  # emission (lower better)
        "OE.3": {"HAPPO": 400.0, "MAAC": 320.0, "MASAC": 480.0, "MATD3": 360.0},  # cost (lower better)
    }
    scales = {"OE.1": 0.04, "OE.2": 40.0, "OE.3": 25.0}
    out: Dict[str, Dict[str, List[float]]] = {}
    for oe, by_algo in centers.items():
        out[oe] = {
            algo: list(rng.normal(mu, scales[oe], size=n_per_algo))
            for algo, mu in by_algo.items()
        }
    return out


def _aggregate_seed_values(
    sub: pd.DataFrame,
    *,
    metric: str,
    seed_col: str = "seed",
    episode_col: str = "episode",
) -> List[float]:
    """One finite value per seed (last episode when available, else mean)."""

    if seed_col not in sub.columns:
        return []
    values: List[float] = []
    for _, g in sub.groupby(seed_col, sort=True):
        g = g.copy()
        if episode_col in g.columns:
            g = g.sort_values(episode_col)
            raw = g[metric].astype(float).to_numpy()
            finite = raw[np.isfinite(raw)]
            if finite.size:
                values.append(float(finite[-1]))
            continue
        raw = g[metric].astype(float).to_numpy()
        finite = raw[np.isfinite(raw)]
        if finite.size:
            values.append(float(np.mean(finite)))
    return values


def load_oe_groups_from_episodes(
    csv_path: Path,
    *,
    algorithms: Optional[Sequence[str]] = None,
    specs: Optional[Mapping[str, Mapping[str, object]]] = None,
    max_seeds: Optional[int] = None,
    expected_n_seeds: int = N_SEEDS,
    allow_episode_fallback: bool = False,
) -> Tuple[Dict[str, Dict[str, List[float]]], Dict[str, object]]:
    """Load per-algorithm **seed** samples for OE.1/OE.2/OE.3.

    Prefer a ``seed`` column (aggregate episodes → one score per seed). Without
    ``seed``, only ``allow_episode_fallback=True`` keeps episode-level samples
    (not the canonical design).
    """

    specs = specs or DEFAULT_OE_SPECS
    df = pd.read_csv(csv_path)
    required = {"algorithm", "scenario"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"episodes CSV missing columns: {sorted(missing)}")

    df["algorithm"] = df["algorithm"].astype(str).str.upper()
    df["scenario"] = df["scenario"].astype(str).str.upper()
    has_seed = "seed" in df.columns
    if algorithms is None:
        algorithms = sorted(df["algorithm"].unique().tolist())
    else:
        algorithms = [str(a).upper() for a in algorithms]

    if not has_seed and not allow_episode_fallback:
        raise ValueError(
            f"{csv_path} has no 'seed' column. Canonical tests require one value "
            f"per seed (expected_n_seeds={expected_n_seeds}). Re-export with seed, "
            "pass --run-root with *_seed_* jobs, use --illustrative-only, or set "
            "--allow-episode-fallback (not recommended)."
        )

    groups: Dict[str, Dict[str, List[float]]] = {}
    meta: Dict[str, Any] = {
        "source_csv": str(csv_path),
        "algorithms": list(algorithms),
        "unit": "seed" if has_seed else "episode",
        "expected_n_seeds": int(expected_n_seeds),
        "n": {},
        "coverage": {},
    }
    if not has_seed:
        meta["warning"] = (
            "No seed column; using episode samples. Canonical unit is "
            f"{expected_n_seeds} independent training seeds."
        )

    for oe_name, spec in specs.items():
        scen = str(spec["scenario"]).upper()
        metric = str(spec["metric"])
        if metric not in df.columns:
            raise ValueError(f"metric '{metric}' not in {csv_path}")
        sub = df[df["scenario"] == scen]
        by_algo: Dict[str, List[float]] = {}
        for algo in algorithms:
            algo_sub = sub.loc[sub["algorithm"] == algo]
            if has_seed:
                vals_list = _aggregate_seed_values(algo_sub, metric=metric)
            else:
                vals = algo_sub[metric].astype(float).to_numpy()
                vals = vals[np.isfinite(vals)]
                vals_list = [float(v) for v in vals]
            if max_seeds is not None and len(vals_list) > max_seeds:
                vals_list = vals_list[: int(max_seeds)]
            if vals_list:
                by_algo[algo] = vals_list
            n = len(vals_list)
            meta["n"][f"{oe_name}:{algo}"] = n
            meta["coverage"][f"{oe_name}:{algo}"] = {
                "n": n,
                "expected": int(expected_n_seeds),
                "complete": n >= int(expected_n_seeds),
            }
        groups[oe_name] = by_algo
    return groups, meta


def _metric_from_results_json(payload: Mapping[str, Any], metric: str) -> Optional[float]:
    """Best-effort extract of a district metric from results.json."""

    # Flat / summary fields
    for key in (metric, f"district_{metric}", metric.replace("district_", "")):
        if key in payload:
            try:
                v = float(payload[key])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                v = float("nan")
            if np.isfinite(v):
                return v

    report = payload.get("citylearn_v3_report")
    if isinstance(report, dict):
        for bag_name in ("all_values", "district_kpis", "summary"):
            bag = report.get(bag_name)
            if isinstance(bag, dict) and metric in bag:
                try:
                    v = float(bag[metric])  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    continue
                if np.isfinite(v):
                    return v
        # Map OE metrics from common KPI names when present
        aliases = {
            "reward_mean": ("reward_mean", "mean_reward", "district_reward_mean"),
            "district_emission": (
                "carbon_emissions",
                "district_emission",
                "district_carbon_emissions",
            ),
            "district_cost": ("electricity_cost", "district_cost", "cost"),
        }
        for bag_name in ("all_values", "district_kpis", "summary"):
            bag = report.get(bag_name)
            if not isinstance(bag, dict):
                continue
            for alias in aliases.get(metric, ()):
                if alias in bag:
                    try:
                        v = float(bag[alias])  # type: ignore[arg-type]
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        return v
    return None


def load_oe_groups_from_run_root(
    run_root: Path,
    *,
    algorithms: Optional[Sequence[str]] = None,
    specs: Optional[Mapping[str, Mapping[str, object]]] = None,
    expected_n_seeds: int = N_SEEDS,
    seeds: Optional[Sequence[int]] = None,
) -> Tuple[Dict[str, Dict[str, List[float]]], Dict[str, Any]]:
    """Load one KPI value per ``{algo}/{E*}_seed_{k}/data/results.json`` job."""

    specs = specs or DEFAULT_OE_SPECS
    seed_set = set(int(s) for s in (seeds if seeds is not None else range(expected_n_seeds)))
    if algorithms is None:
        algorithms = ["HAPPO", "MASAC", "MATD3", "MAAC"]
    else:
        algorithms = [str(a).upper() for a in algorithms]

    groups: Dict[str, Dict[str, List[float]]] = {name: {} for name in specs}
    meta: Dict[str, Any] = {
        "source_run_root": str(run_root),
        "unit": "seed",
        "expected_n_seeds": int(expected_n_seeds),
        "algorithms": list(algorithms),
        "n": {},
        "coverage": {},
        "missing": [],
    }

    for algo in algorithms:
        for oe_name, spec in specs.items():
            scen = str(spec["scenario"]).upper()
            metric = str(spec["metric"])
            values: List[float] = []
            for seed in sorted(seed_set):
                candidates = [
                    run_root / algo / f"{scen}_seed_{seed}" / "data" / "results.json",
                    run_root / algo.lower() / f"{scen}_seed_{seed}" / "data" / "results.json",
                    run_root / algo / scen / "data" / "results.json" if seed == 0 else None,
                ]
                path = next((p for p in candidates if p is not None and p.is_file()), None)
                if path is None:
                    meta["missing"].append(f"{algo}/{scen}/seed={seed}")
                    continue
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    meta["missing"].append(f"{algo}/{scen}/seed={seed}:unreadable")
                    continue
                val = _metric_from_results_json(payload, metric)
                if val is None:
                    meta["missing"].append(f"{algo}/{scen}/seed={seed}:no_{metric}")
                    continue
                values.append(float(val))
            groups[oe_name][algo] = values
            n = len(values)
            meta["n"][f"{oe_name}:{algo}"] = n
            meta["coverage"][f"{oe_name}:{algo}"] = {
                "n": n,
                "expected": int(expected_n_seeds),
                "complete": n >= int(expected_n_seeds),
            }
    return groups, meta


def _json_default(obj):
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="index")
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--episodes-csv",
        type=Path,
        default=None,
        help="district_episode_kpis.csv with a seed column (default Drive table if present)",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Training output root with {ALGO}/{E*}_seed_{k}/data/results.json (preferred)",
    )
    parser.add_argument(
        "--illustrative-only",
        action="store_true",
        help=f"Ignore CSVs and use synthetic OE spreads (4 algos × {N_SEEDS} seeds)",
    )
    parser.add_argument(
        "--n-seeds",
        type=int,
        default=N_SEEDS,
        help=f"Expected independent seeds per algorithm/scenario (default: {N_SEEDS})",
    )
    parser.add_argument(
        "--allow-episode-fallback",
        action="store_true",
        help="If CSV lacks seed, use episode samples (not canonical; discouraged)",
    )
    parser.add_argument(
        "--complementary",
        action="store_true",
        help="Also run Mood/Quade/SRH/Conover/MWU/Brunner-Munzel/Spearman/Kendall/Page",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO / "outputs" / "madrl_nonparametric_battery",
        help="Directory for JSON/Markdown reports",
    )
    parser.add_argument(
        "--max-seeds",
        type=int,
        default=None,
        help="Optional cap on seeds per algorithm/scenario (smoke / speed)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Fast path: illustrative data, complementary off, write reports",
    )
    parser.add_argument(
        "--page-order",
        nargs="+",
        default=None,
        help="Optional hypothesized increasing performance order for Page's trend",
    )
    parser.add_argument(
        "--topsis-weight-oe1",
        type=float,
        default=1.0 / 3.0,
        help="TOPSIS weight for OE.1 (default equal 1/3)",
    )
    parser.add_argument(
        "--topsis-weight-oe2",
        type=float,
        default=1.0 / 3.0,
        help="TOPSIS weight for OE.2 (default equal 1/3)",
    )
    parser.add_argument(
        "--topsis-weight-oe3",
        type=float,
        default=1.0 / 3.0,
        help="TOPSIS weight for OE.3 (default equal 1/3)",
    )
    args = parser.parse_args(argv)

    if args.smoke:
        args.illustrative_only = True
        args.complementary = False

    from uc3m.multicriteria.stats_tests import (
        format_full_report,
        run_full_methodology_battery,
    )

    n_seeds = int(args.n_seeds)
    meta: Dict[str, object] = {}
    if args.illustrative_only:
        oe_groups = _illustrative_oe_groups(n_per_algo=n_seeds)
        meta = {
            "source": "illustrative_synthetic",
            "unit": "seed",
            "n_per_algo": n_seeds,
            "expected_n_seeds": n_seeds,
        }
    elif args.run_root is not None:
        oe_groups, meta = load_oe_groups_from_run_root(
            Path(args.run_root),
            expected_n_seeds=n_seeds,
            seeds=range(n_seeds),
        )
        meta["source"] = "run_root_results_json"
    else:
        csv_path = args.episodes_csv or DEFAULT_EPISODES
        if not Path(csv_path).is_file():
            print(
                f"[warn] episodes CSV not found ({csv_path}); falling back to illustrative "
                f"({n_seeds} seeds).",
                file=sys.stderr,
            )
            oe_groups = _illustrative_oe_groups(n_per_algo=n_seeds)
            meta = {
                "source": "illustrative_fallback",
                "missing_csv": str(csv_path),
                "unit": "seed",
                "n_per_algo": n_seeds,
                "expected_n_seeds": n_seeds,
            }
        else:
            try:
                oe_groups, meta = load_oe_groups_from_episodes(
                    Path(csv_path),
                    max_seeds=args.max_seeds,
                    expected_n_seeds=n_seeds,
                    allow_episode_fallback=bool(args.allow_episode_fallback),
                )
                meta["source"] = "episodes_csv"
            except ValueError as exc:
                print(f"[warn] {exc}", file=sys.stderr)
                print(
                    f"[warn] Falling back to illustrative ({n_seeds} seeds).",
                    file=sys.stderr,
                )
                oe_groups = _illustrative_oe_groups(n_per_algo=n_seeds)
                meta = {
                    "source": "illustrative_fallback_no_seed_column",
                    "missing_csv_seed": str(csv_path),
                    "unit": "seed",
                    "n_per_algo": n_seeds,
                    "expected_n_seeds": n_seeds,
                }

    hib = {
        name: bool(DEFAULT_OE_SPECS[name]["higher_is_better"])
        for name in oe_groups
        if name in DEFAULT_OE_SPECS
    }
    w_sum = args.topsis_weight_oe1 + args.topsis_weight_oe2 + args.topsis_weight_oe3
    if w_sum <= 0:
        raise SystemExit("TOPSIS weights must sum to a positive value")
    topsis_weights = {
        "OE.1": args.topsis_weight_oe1 / w_sum,
        "OE.2": args.topsis_weight_oe2 / w_sum,
        "OE.3": args.topsis_weight_oe3 / w_sum,
    }

    battery = run_full_methodology_battery(
        oe_groups,
        oe_higher_is_better=hib,
        topsis_weights=topsis_weights,
        alpha=args.alpha,
        complementary=bool(args.complementary),
        page_order=args.page_order,
        expected_n_seeds=n_seeds,
    )
    battery["meta"] = meta
    battery["oe_specs"] = {
        k: {kk: vv for kk, vv in v.items() if kk != "label"}
        for k, v in DEFAULT_OE_SPECS.items()
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "nonparametric_battery.json"
    md_path = out_dir / "nonparametric_battery_report.md"
    json_path.write_text(
        json.dumps(battery, indent=2, default=_json_default),
        encoding="utf-8",
    )
    report = format_full_report(battery)
    md_path.write_text(report, encoding="utf-8")

    # Safe console print on Windows cp1252 terminals.
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode("ascii", errors="replace").decode("ascii"))
    print()
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")

    # Console summary of winners + seed coverage
    print("\n=== Winner summary ===")
    for oe_name, oe_res in (battery.get("oe") or {}).items():
        win = (oe_res or {}).get("winner") or {}
        cov = (oe_res or {}).get("sample_coverage") or {}
        print(
            f"  {oe_name}: {win.get('winners')} ({win.get('status')}) "
            f"n_seeds={cov.get('n_by_algorithm')}"
        )
    og = battery.get("og") or {}
    topsis = og.get("topsis") or {}
    ranking = topsis.get("ranking") or []
    if ranking:
        print(f"  OG TOPSIS official: {ranking[0].get('algorithm')} (C*={ranking[0].get('closeness')})")
    val = og.get("topsis_vs_friedman") or {}
    print(f"  TOPSIS vs Friedman agreement: {val.get('agreement')} discrepancy={val.get('discrepancy')}")
    print(f"  expected_n_seeds={n_seeds} unit={meta.get('unit', 'seed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
