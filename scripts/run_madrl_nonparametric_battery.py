#!/usr/bin/env python
"""Run the full non-parametric MADRL comparison battery (OE.1/OE.2/OE.3 + OG).

Implements the methodology sections 1–8 against episode KPIs or illustrative seeds:

  OE (per scenario): Shapiro → Fligner → KW → ε² → Dunn-Holm → Cliff δ → winner rule
  OG (global): Friedman → Kendall W → Nemenyi → TOPSIS (+ Friedman validation)

Usage (from repo root):

    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --complementary
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --illustrative-only
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --episodes-csv path\\to\\district_episode_kpis.csv
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --smoke
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Default OE metric mapping from district_episode_kpis.csv
# E1 flexibility → reward_mean (higher better)
# E2 CO2 → district_emission (lower better)
# E3 cost → district_cost (lower better)
DEFAULT_OE_SPECS: Dict[str, Dict[str, object]] = {
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


def _illustrative_oe_groups(
    n_per_algo: int = 8,
    seed: int = 0,
) -> Dict[str, Dict[str, List[float]]]:
    """Synthetic seed spreads for smoke / offline demos (4 algorithms × 3 OE)."""

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


def load_oe_groups_from_episodes(
    csv_path: Path,
    *,
    algorithms: Optional[Sequence[str]] = None,
    specs: Optional[Mapping[str, Mapping[str, object]]] = None,
    max_episodes: Optional[int] = None,
) -> Tuple[Dict[str, Dict[str, List[float]]], Dict[str, object]]:
    """Load per-algorithm episode samples for OE.1/OE.2/OE.3."""

    specs = specs or DEFAULT_OE_SPECS
    df = pd.read_csv(csv_path)
    required = {"algorithm", "scenario"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"episodes CSV missing columns: {sorted(missing)}")

    df["algorithm"] = df["algorithm"].astype(str).str.upper()
    df["scenario"] = df["scenario"].astype(str).str.upper()
    if algorithms is None:
        algorithms = sorted(df["algorithm"].unique().tolist())
    else:
        algorithms = [str(a).upper() for a in algorithms]

    groups: Dict[str, Dict[str, List[float]]] = {}
    meta: Dict[str, object] = {"source_csv": str(csv_path), "algorithms": list(algorithms), "n": {}}
    for oe_name, spec in specs.items():
        scen = str(spec["scenario"]).upper()
        metric = str(spec["metric"])
        if metric not in df.columns:
            raise ValueError(f"metric '{metric}' not in {csv_path}")
        sub = df[df["scenario"] == scen]
        by_algo: Dict[str, List[float]] = {}
        for algo in algorithms:
            vals = sub.loc[sub["algorithm"] == algo, metric].astype(float).to_numpy()
            vals = vals[np.isfinite(vals)]
            if max_episodes is not None and vals.size > max_episodes:
                vals = vals[: int(max_episodes)]
            if vals.size:
                by_algo[algo] = [float(v) for v in vals]
            meta["n"][f"{oe_name}:{algo}"] = int(vals.size)
        groups[oe_name] = by_algo
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
        help="district_episode_kpis.csv (default: Drive analysis table if present)",
    )
    parser.add_argument(
        "--illustrative-only",
        action="store_true",
        help="Ignore CSVs and use synthetic OE spreads (4 algos × 8 samples)",
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
        "--max-episodes",
        type=int,
        default=None,
        help="Optional cap on episodes per algorithm/scenario (smoke / speed)",
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

    meta: Dict[str, object] = {}
    if args.illustrative_only:
        oe_groups = _illustrative_oe_groups()
        meta = {"source": "illustrative_synthetic", "n_per_algo": 8}
    else:
        csv_path = args.episodes_csv or DEFAULT_EPISODES
        if not Path(csv_path).is_file():
            print(
                f"[warn] episodes CSV not found ({csv_path}); falling back to illustrative.",
                file=sys.stderr,
            )
            oe_groups = _illustrative_oe_groups()
            meta = {"source": "illustrative_fallback", "missing_csv": str(csv_path)}
        else:
            oe_groups, meta = load_oe_groups_from_episodes(
                Path(csv_path),
                max_episodes=args.max_episodes,
            )
            meta["source"] = "episodes_csv"

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

    # Console summary of winners
    print("\n=== Winner summary ===")
    for oe_name, oe_res in (battery.get("oe") or {}).items():
        win = (oe_res or {}).get("winner") or {}
        print(f"  {oe_name}: {win.get('winners')} ({win.get('status')})")
    og = battery.get("og") or {}
    topsis = og.get("topsis") or {}
    ranking = topsis.get("ranking") or []
    if ranking:
        print(f"  OG TOPSIS official: {ranking[0].get('algorithm')} (C*={ranking[0].get('closeness')})")
    val = og.get("topsis_vs_friedman") or {}
    print(f"  TOPSIS vs Friedman agreement: {val.get('agreement')} discrepancy={val.get('discrepancy')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
