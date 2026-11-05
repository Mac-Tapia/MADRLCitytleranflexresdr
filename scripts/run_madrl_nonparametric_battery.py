#!/usr/bin/env python
"""Run the full non-parametric MADRL comparison battery (OE.1/OE.2/OE.3 + OG).

Implements the methodology sections 1–8 against **per-seed** KPIs (``--n-seeds``,
default the empirical protocol's value) or illustrative synthetic seeds:

  OE (per scenario): Shapiro → Fligner → KW → ε² → Dunn-Holm → Cliff δ → winner rule
  OG (global): Friedman → Kendall W → Nemenyi → TOPSIS (+ Friedman validation)

The statistical unit of analysis is an independent training seed (not an
episode within a run). The default source is the modular campaign catalog
(``uc3m.application.evaluation.results_catalog``): ``--results-root``, then
``MADRL_RESULTS_ROOT``, then ``outputs/campaign``; one verified run per
algorithm, scenario and seed. CSVs with a ``seed`` column or a legacy run root
with ``{ALGO}/{E*}_seed_{k}/data/results.json`` remain explicit alternatives.
Missing real data is reported and exits with code 2; illustrative values are
used only with ``--illustrative-only``/``--smoke``.

Usage (from repo root):

    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_nonparametric_battery.py --results-root outputs\\campaign
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

from uc3m.application.evaluation.results_catalog import (  # noqa: E402
    AmbiguousCampaign,
    campaign_layout,
    discover_runs,
    resolve_results_root,
)
from uc3m.multicriteria.scenarios import DEFAULT_PROTOCOL  # noqa: E402

# Default of the empirical protocol. A confirmatory reading declares its own n and ids.
N_SEEDS = int(DEFAULT_PROTOCOL.n_seeds)
CONFIRMATORY_ALGORITHMS = ("HAPPO", "MASAC", "MATD3", "MAAC")

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


class NoCampaignData(FileNotFoundError):
    """The results root has no verified run usable by the battery."""

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


def _declared_seed_ids(seeds: Sequence[int]) -> List[int]:
    """Sorted, unique, non-negative integer seed identities."""

    ids = []
    for seed in seeds:
        if isinstance(seed, bool) or int(seed) != seed or seed < 0:
            raise ValueError(f"invalid seed id: {seed!r}")
        ids.append(int(seed))
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate seed ids: {ids}")
    return sorted(ids)


def _pairing_eligible(
    seed_ids: Mapping[str, Mapping[str, Sequence[int]]],
    missing: Sequence[str],
    expected_n_seeds: int,
) -> bool:
    """Paired tests need every algorithm of an objective measured on the same seeds."""

    if missing or not seed_ids:
        return False
    return all(
        by_algo
        and len({tuple(sorted(ids)) for ids in by_algo.values()}) == 1
        and all(len(ids) == int(expected_n_seeds) for ids in by_algo.values())
        for by_algo in seed_ids.values()
    )


def _validated_episode_rows(df: pd.DataFrame, csv_path: Path) -> pd.DataFrame:
    """Seed and episode must identify exactly one row; nothing is averaged or filled."""

    seeds = pd.to_numeric(df["seed"], errors="coerce")
    if seeds.isna().any() or (seeds != seeds.round()).any() or (seeds < 0).any():
        raise ValueError(f"{csv_path}: seed must be a non-negative integer in every row")
    df = df.assign(seed=seeds.astype(int))
    key = ["algorithm", "scenario", "seed"]
    if "episode" in df.columns:
        episodes = pd.to_numeric(df["episode"], errors="coerce")
        if not np.isfinite(episodes.to_numpy(dtype=float)).all():
            raise ValueError(f"{csv_path}: episode must be finite in every row")
        df = df.assign(episode=episodes)
        key.append("episode")
    if df.duplicated(key).any():
        raise ValueError(f"{csv_path}: duplicate rows for the same {'/'.join(key[2:])}")
    return df


def load_oe_groups_from_episodes(
    csv_path: Path,
    *,
    algorithms: Optional[Sequence[str]] = None,
    specs: Optional[Mapping[str, Mapping[str, object]]] = None,
    max_seeds: Optional[int] = None,
    expected_n_seeds: int = N_SEEDS,
    allow_episode_fallback: bool = False,
    seeds: Optional[Sequence[int]] = None,
) -> Tuple[Dict[str, Dict[str, List[float]]], Dict[str, object]]:
    """Load per-algorithm **seed** samples for OE.1/OE.2/OE.3.

    Each seed contributes the metric of the final episode of its scenario. A seed
    without that value is reported in ``meta['missing']``, never filled from an
    earlier episode. Without ``seed``, only ``allow_episode_fallback=True`` keeps
    episode-level samples (not the canonical design, and not usable by the paired
    battery).
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

    if max_seeds is not None:
        expected_n_seeds = min(int(expected_n_seeds), int(max_seeds))
    groups: Dict[str, Dict[str, List[float]]] = {}
    meta: Dict[str, Any] = {
        "source_csv": str(csv_path),
        "algorithms": list(algorithms),
        "unit": "seed" if has_seed else "episode",
        "expected_n_seeds": int(expected_n_seeds),
        "n": {},
        "coverage": {},
        "missing": [],
        "seed_ids": {},
        "selection": {},
    }
    if has_seed:
        df = _validated_episode_rows(df, csv_path)
    else:
        meta["warning"] = (
            "No seed column; using episode samples. Canonical unit is "
            f"{expected_n_seeds} independent training seeds."
        )
    declared = None if seeds is None else _declared_seed_ids(seeds)
    if declared is not None and has_seed and not set(df["seed"]) <= set(declared):
        raise ValueError(f"{csv_path}: seeds outside the declared list {declared}")

    for oe_name, spec in specs.items():
        scen = str(spec["scenario"]).upper()
        metric = str(spec["metric"])
        if metric not in df.columns:
            raise ValueError(f"metric '{metric}' not in {csv_path}")
        sub = df[df["scenario"] == scen]
        by_algo: Dict[str, List[float]] = {}
        final = None
        if has_seed:
            meta["seed_ids"][oe_name] = {}
            if "episode" in sub.columns and not sub.empty:
                final = sub["episode"].max()
                final = int(final) if float(final).is_integer() else float(final)
                meta["selection"][oe_name] = {"final_episode": final, "rule": "same final episode for every seed"}
            universe = declared if declared is not None else sorted(int(s) for s in sub["seed"].unique())
            if max_seeds is not None:
                universe = universe[: int(max_seeds)]
        for algo in algorithms:
            algo_sub = sub.loc[sub["algorithm"] == algo]
            if has_seed:
                vals_list, ids = [], []
                for seed in universe:
                    rows = algo_sub.loc[algo_sub["seed"] == seed]
                    if final is not None:
                        rows = rows.loc[rows["episode"] == final]
                    value = float(rows[metric].iloc[0]) if len(rows) else float("nan")
                    if not np.isfinite(value):
                        meta["missing"].append(f"{algo}/{scen}/seed={seed}:no_{metric}")
                        continue
                    vals_list.append(value)
                    ids.append(int(seed))
                meta["seed_ids"][oe_name][algo] = ids
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
    meta["pairing_eligible"] = has_seed and _pairing_eligible(meta["seed_ids"], meta["missing"], expected_n_seeds)
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
    if algorithms is None:
        algorithms = ["HAPPO", "MASAC", "MATD3", "MAAC"]
    else:
        algorithms = [str(a).upper() for a in algorithms]
    if seeds is None:
        found = {int(match.group("seed")) for algo in algorithms
                 for folder in (run_root / algo, run_root / algo.lower()) if folder.is_dir()
                 for child in folder.iterdir() for match in [_SEED_DIR_RE.match(child.name)] if match}
        seeds = sorted(found) or range(expected_n_seeds)
    seed_list = _declared_seed_ids(seeds)

    groups: Dict[str, Dict[str, List[float]]] = {name: {} for name in specs}
    meta: Dict[str, Any] = {
        "source_run_root": str(run_root),
        "unit": "seed",
        "expected_n_seeds": int(expected_n_seeds),
        "algorithms": list(algorithms),
        "n": {},
        "coverage": {},
        "missing": [],
        "seed_ids": {name: {} for name in specs},
    }

    for algo in algorithms:
        for oe_name, spec in specs.items():
            scen = str(spec["scenario"]).upper()
            metric = str(spec["metric"])
            values: List[float] = []
            ids: List[int] = []
            for seed in seed_list:
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
                if "seed" in payload and payload["seed"] != seed:
                    meta["missing"].append(f"{algo}/{scen}/seed={seed}:declares_seed_{payload['seed']}")
                    continue
                values.append(float(val))
                ids.append(seed)
            groups[oe_name][algo] = values
            meta["seed_ids"][oe_name][algo] = ids
            n = len(values)
            meta["n"][f"{oe_name}:{algo}"] = n
            meta["coverage"][f"{oe_name}:{algo}"] = {
                "n": n,
                "expected": int(expected_n_seeds),
                "complete": n >= int(expected_n_seeds),
            }
    meta["pairing_eligible"] = _pairing_eligible(meta["seed_ids"], meta["missing"], expected_n_seeds)
    return groups, meta


def load_oe_groups_from_results_root(
    results_root: Path,
    *,
    algorithms: Optional[Sequence[str]] = None,
    specs: Optional[Mapping[str, Mapping[str, object]]] = None,
    expected_n_seeds: int = N_SEEDS,
    seeds: Optional[Sequence[int]] = None,
) -> Tuple[Dict[str, Dict[str, List[float]]], Dict[str, Any]]:
    """One KPI value per verified campaign run located through the results catalog."""

    specs = specs or DEFAULT_OE_SPECS
    if seeds is None:
        seeds = sorted({run.seed for run in discover_runs(results_root)})
        if not seeds:
            raise NoCampaignData(f"{results_root}: no verified campaign runs")
    seed_list = _declared_seed_ids(seeds)
    if algorithms is None:
        algorithms = ["HAPPO", "MASAC", "MATD3", "MAAC"]
    else:
        algorithms = [str(a).upper() for a in algorithms]

    layouts = {seed: campaign_layout(results_root, seed=seed) for seed in seed_list}
    if not any(layouts.values()):
        raise NoCampaignData(
            f"{results_root}: no verified campaign runs for seeds {seed_list}"
        )

    groups: Dict[str, Dict[str, List[float]]] = {name: {} for name in specs}
    meta: Dict[str, Any] = {
        "source_results_root": str(results_root),
        "unit": "seed",
        "expected_n_seeds": int(expected_n_seeds),
        "algorithms": list(algorithms),
        "n": {},
        "coverage": {},
        "missing": [],
        "run_ids": {},
        "seed_ids": {name: {} for name in specs},
    }

    for algo in algorithms:
        for oe_name, spec in specs.items():
            scen = str(spec["scenario"]).upper()
            metric = str(spec["metric"])
            values: List[float] = []
            ids: List[int] = []
            for seed in seed_list:
                scenario_dir = layouts[seed].get((algo, scen))
                path = scenario_dir / "data" / "results.json" if scenario_dir is not None else None
                if path is None or not path.is_file():
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
                ids.append(seed)
                meta["run_ids"][f"{algo}/{scen}/seed={seed}"] = scenario_dir.parent.name
            groups[oe_name][algo] = values
            meta["seed_ids"][oe_name][algo] = ids
            n = len(values)
            meta["n"][f"{oe_name}:{algo}"] = n
            meta["coverage"][f"{oe_name}:{algo}"] = {
                "n": n,
                "expected": int(expected_n_seeds),
                "complete": n >= int(expected_n_seeds),
            }
    meta["pairing_eligible"] = _pairing_eligible(meta["seed_ids"], meta["missing"], expected_n_seeds)
    return groups, meta


def run_nonparametric_battery(
    oe_groups: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    sampling: Optional[Mapping[str, Any]] = None,
    expected_n_seeds: int = N_SEEDS,
    oe_higher_is_better: Optional[Mapping[str, bool]] = None,
    topsis_weights: Optional[Mapping[str, float]] = None,
    alpha: float = 0.05,
    complementary: bool = False,
    page_order: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Battery on samples aligned by seed identity; lists are never paired by position."""

    from uc3m.multicriteria.stats_tests import run_full_methodology_battery

    seed_ids = (sampling or {}).get("seed_ids")
    if not seed_ids:
        raise ValueError("paired statistics need seed IDs; positional lists are not paired")
    if sampling.get("missing"):
        raise ValueError(f"missing seed measurements: {list(sampling['missing'])}")
    aligned_groups: Dict[str, Dict[str, List[float]]] = {}
    aligned_ids: Dict[str, List[int]] = {}
    for oe_name, by_algo in oe_groups.items():
        by_seed = {}
        for algo, values in by_algo.items():
            ids = _declared_seed_ids(seed_ids.get(oe_name, {}).get(algo, ()))
            stored = seed_ids[oe_name][algo]
            if len(stored) != len(values):
                raise ValueError(f"{oe_name}/{algo}: one value per seed id is required")
            by_seed[algo] = (ids, dict(zip(stored, values)))
        reference = next(iter(by_seed.values()))[0] if by_seed else []
        if any(ids != reference for ids, _ in by_seed.values()):
            raise ValueError(f"{oe_name}: algorithms were not measured on the same seed set")
        if len(reference) != int(expected_n_seeds):
            raise ValueError(f"{oe_name}: {len(reference)} seed ids, expected {expected_n_seeds}")
        aligned_groups[oe_name] = {algo: [float(row[s]) for s in reference] for algo, (_, row) in by_seed.items()}
        aligned_ids[oe_name] = reference
    if oe_higher_is_better is None:
        oe_higher_is_better = {
            name: bool(DEFAULT_OE_SPECS[name]["higher_is_better"])
            for name in aligned_groups
            if name in DEFAULT_OE_SPECS
        }
    battery = run_full_methodology_battery(
        aligned_groups,
        oe_higher_is_better=dict(oe_higher_is_better),
        topsis_weights=dict(topsis_weights or DEFAULT_TOPSIS_WEIGHTS),
        alpha=alpha,
        complementary=complementary,
        page_order=page_order,
        expected_n_seeds=int(expected_n_seeds),
    )
    battery["sampling"] = {"aligned_seed_ids": aligned_ids, "unit": sampling.get("unit", "seed")}
    battery["scientific_acceptance"] = False
    return battery


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
        help="Explicit district_episode_kpis.csv with a seed column",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=None,
        help="Modular campaign results root (default source: MADRL_RESULTS_ROOT, then outputs/campaign)",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Legacy training output root with {ALGO}/{E*}_seed_{k}/data/results.json",
    )
    parser.add_argument(
        "--illustrative-only",
        action="store_true",
        help=f"Ignore CSVs and use synthetic OE spreads (4 algos × {N_SEEDS} seeds)",
    )
    parser.add_argument(
        "--n-seeds",
        type=int,
        default=None,
        help=f"Expected independent seeds per algorithm/scenario (default: {N_SEEDS})",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        help="Declared seed ids; without it the ids found in the source are used and reported",
    )
    parser.add_argument(
        "--confirmatory-v1",
        action="store_true",
        help="Confirmatory reading: requires explicit --n-seeds and --seeds",
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

    from uc3m.multicriteria.stats_tests import format_full_report

    if args.confirmatory_v1:
        if args.n_seeds is None or args.seeds is None:
            parser.error("--confirmatory-v1 requires explicit --n-seeds and --seeds")
        if args.illustrative_only:
            parser.error("--confirmatory-v1 cannot use illustrative data")
        if len(args.seeds) != args.n_seeds:
            parser.error("--seeds must list exactly --n-seeds ids")
        if args.max_seeds is not None:
            parser.error("--confirmatory-v1 cannot be reduced with --max-seeds")
    n_seeds = N_SEEDS if args.n_seeds is None else int(args.n_seeds)
    meta: Dict[str, object] = {}
    try:
        declared_seeds = None if args.seeds is None else _declared_seed_ids(args.seeds)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    if args.illustrative_only:
        oe_groups = _illustrative_oe_groups(n_per_algo=n_seeds)
        meta = {
            "source": "illustrative_synthetic",
            "unit": "illustrative_draw",
            "n_per_algo": n_seeds,
            "expected_n_seeds": n_seeds,
            "seed_ids": {oe: {algo: list(range(n_seeds)) for algo in by_algo} for oe, by_algo in oe_groups.items()},
            "pairing_eligible": True,
        }
    elif args.run_root is not None:
        oe_groups, meta = load_oe_groups_from_run_root(
            Path(args.run_root),
            expected_n_seeds=n_seeds,
            seeds=declared_seeds,
        )
        meta["source"] = "run_root_results_json"
    elif args.episodes_csv is not None:
        csv_path = Path(args.episodes_csv)
        if not csv_path.is_file():
            print(f"[error] episodes CSV not found: {csv_path}", file=sys.stderr)
            return 2
        try:
            oe_groups, meta = load_oe_groups_from_episodes(
                csv_path,
                max_seeds=args.max_seeds,
                expected_n_seeds=n_seeds,
                allow_episode_fallback=bool(args.allow_episode_fallback),
                seeds=declared_seeds,
                algorithms=CONFIRMATORY_ALGORITHMS if args.confirmatory_v1 else None,
            )
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 2
        meta["source"] = "episodes_csv"
    else:
        results_root = resolve_results_root(args.results_root)
        try:
            oe_groups, meta = load_oe_groups_from_results_root(
                results_root,
                expected_n_seeds=n_seeds,
                seeds=declared_seeds,
            )
        except (NoCampaignData, AmbiguousCampaign) as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 2
        meta["source"] = "results_catalog_results_json"
        if meta["missing"]:
            print(
                "[warn] missing campaign treatments: " + ", ".join(meta["missing"]),
                file=sys.stderr,
            )

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

    expected = meta.get("expected_n_seeds", n_seeds)
    try:
        battery = run_nonparametric_battery(
            oe_groups,
            sampling=meta,
            oe_higher_is_better=hib,
            topsis_weights=topsis_weights,
            alpha=args.alpha,
            complementary=bool(args.complementary),
            page_order=args.page_order,
            expected_n_seeds=expected,
        )
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    battery["meta"] = meta
    battery["confirmatory_v1"] = bool(args.confirmatory_v1)
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
