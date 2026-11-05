"""Load real MADRL campaign artefacts or fall back to the illustrative matrix.

Real artefacts come from the modular campaign results root
(``<root>/<run_id>/<E*>/...``) resolved by
``uc3m.application.evaluation.results_catalog``; derived summaries live in
``<root>/resumen_comparativo/``. The illustrative matrix remains available for
tests and methodology demos (``prefer_real=False``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from uc3m.application.evaluation.results_catalog import (
    campaign_layout,
    discover_runs,
    resolve_results_root,
)
from uc3m.domain.pareto import (
    expected_utility,
    hypervolume_3d,
    non_dominated_indices,
    sparsity,
)
from uc3m.multicriteria.criteria import ALGORITHMS, CRITERION_IDS, CRITERION_SPECS

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


def pareto_quality_from_decision_matrix(
    decision_matrix: Mapping[str, Mapping[str, float]],
    *,
    criteria_kind: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Compute scale-independent Pareto metrics for cost, CO2, and flexibility."""

    algorithms = list(decision_matrix)
    if not algorithms:
        raise ValueError("Pareto quality requires at least one algorithm")
    raw = np.asarray(
        [
            [
                decision_matrix[algorithm]["C1"],
                decision_matrix[algorithm]["C2"],
                decision_matrix[algorithm]["C3"],
            ]
            for algorithm in algorithms
        ],
        dtype=float,
    )
    if not np.all(np.isfinite(raw)):
        raise ValueError("Pareto criteria must be finite")

    kinds = criteria_kind or {cid: CRITERION_SPECS[cid].kind for cid in ("C1", "C2", "C3")}
    normalized = np.empty_like(raw)
    for axis in range(3):
        values = raw[:, axis]
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        span = maximum - minimum
        if np.isclose(span, 0.0):
            normalized[:, axis] = 1.0
        elif kinds[f"C{axis + 1}"] == "cost":
            normalized[:, axis] = (maximum - values) / span
        else:
            normalized[:, axis] = (values - minimum) / span

    maximize = (True, True, True)
    front_indices = non_dominated_indices(normalized.tolist(), maximize=maximize)
    front_points = normalized[list(front_indices)]
    return {
        "objective_order": ["C1_cost", "C2_co2", "C3_flexibility"],
        "orientation": ["min" if kinds[cid] == "cost" else "max" for cid in ("C1", "C2", "C3")],
        "normalization": "benefit_minmax_with_constant_axis_equal_to_one",
        "reference_point": [0.0, 0.0, 0.0],
        "front": [algorithms[index] for index in front_indices],
        "hypervolume_3d": hypervolume_3d(
            normalized.tolist(), reference=[0.0, 0.0, 0.0], maximize=maximize
        ),
        "expected_utility_equal_weights": expected_utility(
            normalized.tolist(),
            weights=[1.0 / 3.0] * 3,
            maximize=maximize,
        ),
        "sparsity": sparsity(front_points.tolist()),
        "normalized_points": {
            algorithm: normalized[index].tolist()
            for index, algorithm in enumerate(algorithms)
        },
    }


def default_results_root(repo: Optional[Path] = None) -> Path:
    """``<repo>/outputs/campaign`` for an explicit repo, else the catalog default."""

    if repo is not None:
        return Path(repo) / "outputs" / "campaign"
    return resolve_results_root(None)


def resolve_run_dir(repo: Optional[Path] = None, run_dir: Optional[Path] = None) -> Optional[Path]:
    """Return the campaign results root to read, or None when no verified run exists.

    ``run_dir`` is an explicit results root; otherwise the default root is used
    only if the catalog finds at least one verified run in it.
    """

    if run_dir is not None and Path(run_dir).is_dir():
        return Path(run_dir)
    candidate = default_results_root(repo)
    if candidate.is_dir() and discover_runs(candidate):
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
        if cost is not None:
            matrix[algo]["C1"] = cost
            provenance[algo]["C1"] = "district_objectives.electricity_cost_delta_eur"
        if co2_delta is not None:
            matrix[algo]["C2"] = -co2_delta
            provenance[algo]["C2"] = "district_objectives.-carbon_emissions_delta_kg"
        if flex is not None:
            matrix[algo]["C3"] = flex
            provenance[algo]["C3"] = "district_objectives.flex_composite.ratio_to_baseline.lower_is_better"
        else:
            # A signed energy delta (kWh) is not the dimensionless flex ratio.
            provenance[algo]["C3"] = "unavailable:missing_comparable_flex_composite_ratio_to_baseline"
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
                if cid == "C3" and partial:
                    # Legacy demonstration C3 is activated energy (kWh), not the
                    # real composite ratio. Explicit fill cannot equate the units.
                    prov[algo][cid] = "unavailable:illustrative_kWh_not_comparable_to_real_ratio"
                    continue
                # Prefer same-algo illustrative fill; if algo missing there, skip.
                if algo not in base:
                    continue
                out[algo][cid] = float(base[algo][cid])
                prov[algo][cid] = "illustrative_methodology_section_3_2"
    return out, prov


def _summary_table(scenario_dir: Path) -> Path:
    return scenario_dir / "figures" / "tables" / "episode_summary.csv"


def episode_summary_path(
    run_dir: Path, algo: str, scenario: str, *, seed: int = 0
) -> Optional[Path]:
    """episode_summary.csv of the verified run for ``algo``/``scenario``/``seed``."""

    scenario_dir = campaign_layout(Path(run_dir), seed=seed).get(
        (str(algo).upper(), str(scenario).upper())
    )
    return None if scenario_dir is None else _summary_table(scenario_dir)


def load_episode_reward_series(
    run_dir: Path,
    *,
    scenario: str = "E1",
    algorithms: Optional[Sequence[str]] = None,
    seed: int = 0,
    episode_index_origin: int = 1,
    episode_metadata: Optional[Dict[str, object]] = None,
) -> Dict[str, list[float]]:
    """Load a complete indexed curve; legacy one-based origin defaults to 1.

    Native producers using zero-based IDs must explicitly pass origin=0. Never
    infer an origin from the minimum observed ID: that hides missing first rows.
    """

    if type(episode_index_origin) is not int or episode_index_origin not in (0, 1):
        raise ValueError("episode_index_origin must explicitly be zero or one")
    algos = list(algorithms or ALGORITHMS)
    layout = campaign_layout(Path(run_dir), seed=seed)
    out: Dict[str, list[float]] = {}
    for algo in algos:
        scenario_dir = layout.get((str(algo).upper(), str(scenario).upper()))
        if scenario_dir is None:
            continue
        path = _summary_table(scenario_dir)
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
        if "episode" not in frame.columns:
            raise ValueError(f"{path}: episode IDs are required; row position is not an episode ID")
        raw_ids = frame["episode"]
        ids = pd.to_numeric(raw_ids, errors="coerce").to_numpy(dtype=float)
        if (not ids.size or any(isinstance(v, (bool, np.bool_)) for v in raw_ids)
                or not np.all(np.isfinite(ids)) or np.any(ids != np.floor(ids))
                or np.any(ids < episode_index_origin) or len(np.unique(ids)) != len(ids)):
            raise ValueError(f"{path}: episode IDs must be unique finite integers from the declared origin")
        # A verified run's completed count, when recorded, also catches a missing
        # final row; continuity alone only detects initial/internal missing rows.
        evidence = json.loads((scenario_dir.parent / "evidence.json").read_text(encoding="utf-8"))
        expected = evidence.get("completed_episodes")
        if expected is not None and (type(expected) is not int or expected <= 0):
            raise ValueError(f"{path}: completed_episodes must be a positive integer when declared")
        count = expected if expected is not None else len(ids)
        ordered_ids = np.sort(ids).astype(int).tolist()
        if ordered_ids != list(range(episode_index_origin, episode_index_origin + count)):
            raise ValueError(f"{path}: episode coverage is not continuous and complete from the declared origin")
        frame = frame.assign(episode=ids).sort_values("episode")
        series = pd.to_numeric(frame[col], errors="coerce").tolist()
        if series and np.any(np.isfinite(series)):
            out[algo] = series
            if episode_metadata is not None:
                episode_metadata[algo] = {
                    "episode_ids": ordered_ids, "episode_index_origin": episode_index_origin,
                    "expected_completed_episodes": expected,
                }
    return out


def training_stability_from_episode_rewards(
    rewards: Sequence[float],
    *,
    steps_per_episode: float = 8760.0,
    early_late_fraction: float = 0.2,
) -> Dict[str, float]:
    """Derive C4/C5/C6 from a single real 50-ep training curve (no invention).

    - C4: sample variance of episodic reward (stability proxy; campaign is 1 seed).
    - C5: env-steps to 90% of initial-to-tail progress (episode_idx * steps/ep).
    - C6: |mean(last F) - mean(first F)| early–late gap (F≈20% of episodes).
    """

    from uc3m.multicriteria.criteria import steps_to_fraction_of_asymptotic

    arr = np.asarray(list(rewards), dtype=float)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        return {}

    ep_to_90 = steps_to_fraction_of_asymptotic(arr.tolist(), fraction=0.90)
    c5 = float(ep_to_90) * float(steps_per_episode)
    n_edge = max(1, int(round(arr.size * float(early_late_fraction))))
    early = float(np.mean(arr[:n_edge]))
    late = float(np.mean(arr[-n_edge:]))
    c6 = abs(late - early)
    metrics = {"C5": c5, "C6": c6}
    if arr.size > 1:
        metrics["C4"] = float(np.var(arr, ddof=1))
    return metrics


def load_real_c4c6_from_drive(
    run_dir: Path,
    *,
    scenario: str = "E1",
    algorithms: Optional[Sequence[str]] = None,
    episode_index_origin: int = 1,
    episode_metadata: Optional[Dict[str, object]] = None,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, str]], Dict[str, list[float]]]:
    """Fill C4–C6 + learning curves from real episode_summary tables."""

    series = load_episode_reward_series(
        run_dir, scenario=scenario, algorithms=algorithms,
        episode_index_origin=episode_index_origin, episode_metadata=episode_metadata,
    )
    partial: Dict[str, Dict[str, float]] = {}
    provenance: Dict[str, Dict[str, str]] = {}
    for algo, rewards in series.items():
        metrics = training_stability_from_episode_rewards(rewards)
        if not metrics:
            continue
        partial[algo] = metrics
        provenance[algo] = {
            "C4": "drive_episode_summary.episodic_reward_sample_variance_per_selected_seed",
            "C5": "drive_episode_summary.initial_to_tail_progress_90pct_index*8760",
            "C6": "drive_episode_summary.early_late_reward_gap_abs",
        }
    return partial, provenance, series


def load_decision_matrix(
    *,
    repo: Optional[Path] = None,
    run_dir: Optional[Path] = None,
    scenario: str = "E1",
    prefer_real: bool = True,
    allow_illustrative_fill: bool = False,
    episode_index_origin: int = 1,
) -> Dict[str, Any]:
    """Load real run artefacts; illustrative values require explicit opt-in.

    When ``prefer_real`` and campaign artefacts exist, C1–C3 come from district
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

            episode_metadata: Dict[str, object] = {}
            c456, prov456, learning_curves = load_real_c4c6_from_drive(
                resolved,
                scenario=scenario,
                algorithms=[a for a in partial if {"C1", "C2", "C3"}.issubset(partial[a])],
                episode_index_origin=episode_index_origin,
                episode_metadata=episode_metadata,
            )
            extras["episode_curve_index"] = episode_metadata
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
            # One criterion scalar per actual selected seed (currently seed=0).
            # Episodes remain in learning_curves; they never add seed replicas.
            seed_metric_samples = {
                cid: {a: [float(values[cid])] for a, values in c456.items() if cid in values}
                for cid in ("C4", "C5", "C6")
            }
            extras["seed_metric_replication"] = {
                "unit": "independent_training_seed",
                "selected_seed": 0,
                "max_n_seeds_per_algorithm": 1,
                "C4_definition": "sample_variance_of_episodic_rewards_within_selected_seed",
                "other_runs_are_not_inferred_replicas": True,
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
        if partial:
            matrix = {a: vals for a, vals in matrix.items() if set(CRITERION_IDS).issubset(vals)}
            provenance = {a: provenance[a] for a in matrix}
            if not matrix:
                raise FileNotFoundError("missing comparable real C3 ratio; illustrative kWh fill is prohibited")
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
                "real_only multicriteria: missing campaign C1–C6 "
                "(district_objectives + episode_summary)"
            )
        if any("illustrative" in str(v) for p in provenance.values() for v in p.values()):
            raise RuntimeError("real_only multicriteria: illustrative provenance leaked")
        source = "real_drive_50ep_c1c6"

    extras["algorithms_ranked"] = list(matrix.keys())
    extras["learning_curves"] = learning_curves
    criteria_kind = {cid: spec.kind for cid, spec in CRITERION_SPECS.items()}
    criterion_units = {cid: spec.unit for cid, spec in CRITERION_SPECS.items()}
    if source == "illustrative":
        # Preserve the historical demonstration without inventing a baseline
        # that could turn its kWh values into ratios.
        criteria_kind["C3"] = "benefit"
        criterion_units["C3"] = "kWh"
    return {
        "decision_matrix": matrix,
        "provenance": provenance,
        "source": source,
        "scenario": scenario,
        "criteria_kind": criteria_kind,
        "criterion_units": criterion_units,
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
