"""Load real MADRL run artefacts or fall back to the illustrative matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from uc3m.multicriteria.criteria import ALGORITHMS, CRITERION_IDS

# Section 3.2 illustrative decision matrix (methodology text).
ILLUSTRATIVE_DECISION_MATRIX: Dict[str, Dict[str, float]] = {
    "HAPPO": {"C1": 1250.0, "C2": 3400.0, "C3": 820.0, "C4": 0.015, "C5": 480.0, "C6": 0.08},
    "MAAC": {"C1": 1180.0, "C2": 3550.0, "C3": 900.0, "C4": 0.032, "C5": 520.0, "C6": 0.12},
    "MASAC": {"C1": 1300.0, "C2": 3300.0, "C3": 780.0, "C4": 0.028, "C5": 390.0, "C6": 0.05},
    "MATD3": {"C1": 1210.0, "C2": 3480.0, "C3": 860.0, "C4": 0.021, "C5": 350.0, "C6": 0.10},
}

# Synthetic per-seed spreads around the illustrative means (for Wilcoxon demos).
ILLUSTRATIVE_SEED_SPREAD: Dict[str, Dict[str, Tuple[float, ...]]] = {
    "C1": {
        "HAPPO": (1240, 1255, 1248, 1260, 1245),
        "MAAC": (1170, 1185, 1178, 1190, 1175),
        "MASAC": (1290, 1310, 1295, 1305, 1300),
        "MATD3": (1200, 1215, 1208, 1220, 1205),
    },
    "C2": {
        "HAPPO": (3380, 3410, 3395, 3420, 3400),
        "MAAC": (3530, 3565, 3545, 3570, 3550),
        "MASAC": (3280, 3315, 3295, 3320, 3300),
        "MATD3": (3460, 3495, 3475, 3500, 3480),
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_run_candidates(repo: Optional[Path] = None) -> Tuple[Path, ...]:
    root = Path(repo) if repo is not None else _repo_root()
    return (
        root / "outputs" / "madrl_v3_20260627_164047",
        root / "outputs" / "citylearn_v3_madrl_full_20260615_074011_v4",
    )


def resolve_run_dir(repo: Optional[Path] = None, run_dir: Optional[Path] = None) -> Optional[Path]:
    if run_dir is not None and Path(run_dir).is_dir():
        return Path(run_dir)
    for candidate in default_run_candidates(repo):
        if candidate.is_dir():
            return candidate
    return None


def _safe_float(value) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(out):
        return None
    return out


def decision_matrix_from_district_objectives(
    csv_path: Path,
    *,
    scenario: str = "E1",
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, str]]]:
    """Map district OE KPIs into C1–C3; provenance flags for each cell."""

    frame = pd.read_csv(csv_path)
    if "scenario" in frame.columns:
        frame = frame[frame["scenario"].astype(str) == str(scenario)]
    matrix: Dict[str, Dict[str, float]] = {a: {} for a in ALGORITHMS}
    provenance: Dict[str, Dict[str, str]] = {a: {} for a in ALGORITHMS}

    for _, row in frame.iterrows():
        algo = str(row.get("algorithm", "")).upper()
        if algo not in matrix:
            continue
        # Cost criterion: lower delta (control - baseline) is better.
        cost = _safe_float(row.get("electricity_cost_delta_eur"))
        # CO2 avoided proxy: -(control - baseline) so reductions become positive.
        co2_delta = _safe_float(row.get("carbon_emissions_delta_kg"))
        flex = _safe_float(row.get("flex_composite"))
        if flex is None:
            flex = _safe_float(row.get("grid_import_delta"))
            if flex is not None:
                flex = abs(flex)
        if cost is not None:
            matrix[algo]["C1"] = cost
            provenance[algo]["C1"] = "district_objectives.electricity_cost_delta_eur"
        if co2_delta is not None:
            matrix[algo]["C2"] = -co2_delta
            provenance[algo]["C2"] = "district_objectives.-carbon_emissions_delta_kg"
        if flex is not None:
            matrix[algo]["C3"] = flex
            provenance[algo]["C3"] = "district_objectives.flex_composite_or_|grid_import_delta|"
    return matrix, provenance


def merge_with_illustrative(
    partial: Mapping[str, Mapping[str, float]],
    *,
    illustrative: Optional[Mapping[str, Mapping[str, float]]] = None,
    provenance: Optional[Mapping[str, Mapping[str, str]]] = None,
    algorithms: Optional[Sequence[str]] = None,
    require_real_technical: bool = False,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, str]]]:
    """Fill missing C1–C6 cells from the illustrative methodology matrix.

    When ``require_real_technical`` is True, only algorithms that already have
    real C1–C3 values are kept (avoids mixing tiny illustrative costs with
    large real district deltas).
    """

    base = illustrative or ILLUSTRATIVE_DECISION_MATRIX
    if require_real_technical:
        algos = [
            a
            for a in (algorithms or ALGORITHMS)
            if a in partial and {"C1", "C2", "C3"}.issubset(partial[a].keys())
        ]
        if len(algos) < 2:
            algos = list(algorithms or ALGORITHMS)
            require_real_technical = False
    else:
        algos = list(algorithms or ALGORITHMS)

    out: Dict[str, Dict[str, float]] = {}
    prov: Dict[str, Dict[str, str]] = {
        a: dict(provenance.get(a, {})) if provenance else {} for a in algos
    }
    for algo in algos:
        out[algo] = {}
        for cid in CRITERION_IDS:
            if algo in partial and cid in partial[algo]:
                out[algo][cid] = float(partial[algo][cid])
                prov[algo].setdefault(cid, "real_or_partial")
            else:
                # Prefer same-algo illustrative fill; if algo missing there, skip.
                if algo not in base:
                    continue
                out[algo][cid] = float(base[algo][cid])
                prov[algo][cid] = "illustrative_methodology_section_3_2"
    return out, prov


def episode_summary_path(run_dir: Path, algo: str, scenario: str) -> Path:
    return run_dir / algo / scenario / "figures" / "tables" / "episode_summary.csv"


def load_episode_reward_series(
    run_dir: Path,
    *,
    scenario: str = "E1",
    algorithms: Optional[Sequence[str]] = None,
) -> Dict[str, list[float]]:
    """Load per-episode reward_mean from Drive-derived episode_summary.csv."""

    algos = list(algorithms or ALGORITHMS)
    out: Dict[str, list[float]] = {}
    for algo in algos:
        path = episode_summary_path(run_dir, algo, scenario)
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        col = None
        for candidate in ("reward_mean_average", "reward_mean", "reward"):
            if candidate in frame.columns:
                col = candidate
                break
        if col is None:
            continue
        if "episode" in frame.columns:
            frame = frame.sort_values("episode")
        series = [float(x) for x in frame[col].tolist() if np.isfinite(float(x))]
        if series:
            out[algo] = series
    return out


def training_stability_from_episode_rewards(
    rewards: Sequence[float],
    *,
    steps_per_episode: float = 8760.0,
    early_late_fraction: float = 0.2,
) -> Dict[str, float]:
    """Derive C4/C5/C6 from a single real 50-ep training curve (no invention).

    - C4: sample variance of episodic reward (stability proxy; campaign is 1 seed).
    - C5: env-steps to 90% of asymptotic episodic reward (episode_idx * steps/ep).
    - C6: |mean(last F) - mean(first F)| early–late gap (F≈20% of episodes).
    """

    from uc3m.multicriteria.criteria import steps_to_fraction_of_asymptotic

    arr = np.asarray(list(rewards), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {}

    c4 = float(np.var(arr, ddof=1)) if arr.size > 1 else 0.0
    ep_to_90 = steps_to_fraction_of_asymptotic(arr.tolist(), fraction=0.90)
    c5 = float(ep_to_90) * float(steps_per_episode)
    n_edge = max(1, int(round(arr.size * float(early_late_fraction))))
    early = float(np.mean(arr[:n_edge]))
    late = float(np.mean(arr[-n_edge:]))
    c6 = abs(late - early)
    return {"C4": c4, "C5": c5, "C6": c6}


def load_real_c4c6_from_drive(
    run_dir: Path,
    *,
    scenario: str = "E1",
    algorithms: Optional[Sequence[str]] = None,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, str]], Dict[str, list[float]]]:
    """Fill C4–C6 + learning curves from real episode_summary tables."""

    series = load_episode_reward_series(run_dir, scenario=scenario, algorithms=algorithms)
    partial: Dict[str, Dict[str, float]] = {}
    provenance: Dict[str, Dict[str, str]] = {}
    for algo, rewards in series.items():
        metrics = training_stability_from_episode_rewards(rewards)
        if not metrics:
            continue
        partial[algo] = metrics
        provenance[algo] = {
            "C4": "drive_episode_summary.reward_mean_variance",
            "C5": "drive_episode_summary.episodes_to_90pct_asymptotic*8760",
            "C6": "drive_episode_summary.early_late_reward_gap_abs",
        }
    return partial, provenance, series


def load_decision_matrix(
    *,
    repo: Optional[Path] = None,
    run_dir: Optional[Path] = None,
    scenario: str = "E1",
    prefer_real: bool = True,
    allow_illustrative_fill: bool = True,
) -> Dict[str, Any]:
    """Load a decision matrix from run artefacts when present, else illustrative.

    When ``prefer_real`` and Drive artefacts exist, C1–C3 come from district
    objectives and C4–C6 from episode_summary (50 ep). Set
    ``allow_illustrative_fill=False`` for closure builds (no synthetic cells).
    """

    resolved = resolve_run_dir(repo=repo, run_dir=run_dir) if prefer_real else None
    source = "illustrative"
    partial: Dict[str, Dict[str, float]] = {}
    provenance: Dict[str, Dict[str, str]] = {}
    extras: Dict[str, object] = {}
    require_real_technical = False
    learning_curves: Dict[str, list[float]] = {}
    seed_metric_samples: Dict[str, Dict[str, Sequence[float]]] = {}

    if resolved is not None:
        district_csv = (
            resolved
            / "resumen_comparativo"
            / "multiobjetivo"
            / "district_objectives_by_algorithm.csv"
        )
        if district_csv.is_file():
            partial, provenance = decision_matrix_from_district_objectives(
                district_csv, scenario=scenario
            )
            require_real_technical = True
            source = "real_drive_50ep_c1c3"
            extras["district_csv"] = str(district_csv)
            extras["run_dir"] = str(resolved)
            missing = [a for a in ALGORITHMS if a not in partial or "C1" not in partial[a]]
            if missing:
                extras["algorithms_missing_real_c1c3"] = missing

            c456, prov456, learning_curves = load_real_c4c6_from_drive(
                resolved,
                scenario=scenario,
                algorithms=[a for a in partial if {"C1", "C2", "C3"}.issubset(partial[a])],
            )
            for algo, vals in c456.items():
                partial.setdefault(algo, {}).update(vals)
                provenance.setdefault(algo, {}).update(prov456.get(algo, {}))
            if c456 and all(
                {"C1", "C2", "C3", "C4", "C5", "C6"}.issubset(partial.get(a, {}))
                for a in partial
                if {"C1", "C2", "C3"}.issubset(partial.get(a, {}))
            ):
                source = "real_drive_50ep_c1c6"
            extras["learning_curve_episodes"] = {
                a: len(v) for a, v in learning_curves.items()
            }
            # Real seed samples = episodic rewards (single campaign seed).
            seed_metric_samples = {
                "C4": {a: list(learning_curves[a]) for a in learning_curves},
            }

        report = resolved / "resumen_comparativo" / "best_madrl_report.json"
        if report.is_file():
            extras["best_madrl_report"] = str(report)
            try:
                extras["best_madrl_report_payload"] = json.loads(
                    report.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                pass

    if allow_illustrative_fill:
        matrix, provenance = merge_with_illustrative(
            partial,
            provenance=provenance,
            require_real_technical=require_real_technical,
        )
        if not partial:
            source = "illustrative"
        elif source.startswith("real_drive") and any(
            "illustrative" in str(v)
            for algo_prov in provenance.values()
            for v in algo_prov.values()
        ):
            source = "hybrid_real_c1c3_plus_illustrative"
        if not seed_metric_samples:
            seed_metric_samples = {
                cid: {
                    algo: vals
                    for algo, vals in by_algo.items()
                    if algo in matrix
                }
                for cid, by_algo in ILLUSTRATIVE_SEED_SPREAD.items()
            }
    else:
        # Closure mode: keep only algorithms with full real C1–C6.
        matrix = {
            a: dict(vals)
            for a, vals in partial.items()
            if {"C1", "C2", "C3", "C4", "C5", "C6"}.issubset(vals.keys())
        }
        provenance = {a: dict(provenance.get(a, {})) for a in matrix}
        if not matrix:
            raise FileNotFoundError(
                "real_only multicriteria: missing Drive C1–C6 "
                "(district_objectives + episode_summary)"
            )
        if any("illustrative" in str(v) for p in provenance.values() for v in p.values()):
            raise RuntimeError("real_only multicriteria: illustrative provenance leaked")
        source = "real_drive_50ep_c1c6"

    extras["algorithms_ranked"] = list(matrix.keys())
    extras["learning_curves"] = learning_curves
    return {
        "decision_matrix": matrix,
        "provenance": provenance,
        "source": source,
        "scenario": scenario,
        "extras": extras,
        "seed_metric_samples": {
            cid: {
                algo: vals
                for algo, vals in by_algo.items()
                if algo in matrix
            }
            for cid, by_algo in seed_metric_samples.items()
        },
        "learning_curves": {
            a: [series] for a, series in learning_curves.items() if a in matrix
        },
    }
