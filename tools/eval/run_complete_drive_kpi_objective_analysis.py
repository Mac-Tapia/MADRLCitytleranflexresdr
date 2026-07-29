"""Análisis cuantitativo completo de la corrida canónica MADRL almacenada en Drive.

Fuente exclusiva:
    outputs/_drive_madrl/full_data/{ALGORITHM}/{SCENARIO}/data/*

La carpeta local es el espejo auditado de:
    https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX

El script:
1. valida 4 algoritmos x 3 escenarios x 50 episodios;
2. materializa todos los KPI distritales y los 75 KPI de 17 edificios;
3. reconstruye las 50 observaciones episódicas de HAPPO a partir de los
   49 episodios previos al resume y el episodio final 49 conservado después;
4. calcula los indicadores primarios alineados con OE.1/E1, OE.2/E2 y OE.3/E3;
5. ejecuta pruebas no paramétricas y decide las hipótesis compuestas;
6. calcula el ranking global TOPSIS con igual peso por dimensión.

No entrena modelos, no imputa KPI y no inventa episodios.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


REPO = Path(__file__).resolve().parents[2]
RUN_ID = "madrl_v3_20260627_164047"
DRIVE_URL = (
    "https://drive.google.com/drive/folders/"
    "1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX"
)
FULL_ROOT = REPO / "outputs" / "_drive_madrl" / "full_data"
RUN_ROOT = REPO / "outputs" / RUN_ID
OUT_DIR = (
    RUN_ROOT
    / "resumen_comparativo"
    / "estadistica"
    / "analisis_cuantitativo_completo_50_episodios"
)

ALGORITHMS = ["HAPPO", "MAAC", "MASAC", "MATD3"]
SCENARIOS = ["E1", "E2", "E3"]
ALPHA = 0.05

FLEX_KPIS = [
    "peak_average",
    "ramping_average",
    "one_minus_load_factor_average",
]

OBJECTIVES = {
    "OE1": {
        "scenario": "E1",
        "dimension": "Flexibilidad energética",
        "h0": "HE10",
        "h1": "HE11",
    },
    "OE2": {
        "scenario": "E2",
        "dimension": "Emisiones de CO₂",
        "h0": "HE20",
        "h1": "HE21",
    },
    "OE3": {
        "scenario": "E3",
        "dimension": "Costos energéticos",
        "h0": "HE30",
        "h1": "HE31",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def holm_adjust(p_values: Iterable[float]) -> list[float]:
    values = np.asarray(list(p_values), dtype=float)
    if values.size == 0:
        return []
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    m = len(values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def rank_biserial_signed(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values != 0.0)]
    if values.size == 0:
        return math.nan
    ranks = stats.rankdata(np.abs(values))
    positive = float(ranks[values > 0].sum())
    negative = float(ranks[values < 0].sum())
    total = positive + negative
    return (positive - negative) / total if total else math.nan


def descriptive(values: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "n": 0,
            "mean": math.nan,
            "median": math.nan,
            "std": math.nan,
            "min": math.nan,
            "p25": math.nan,
            "p75": math.nan,
            "iqr": math.nan,
            "max": math.nan,
            "cv_abs": math.nan,
        }
    p25, p75 = np.percentile(values, [25, 75])
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    return {
        "n": int(values.size),
        "mean": mean,
        "median": float(np.median(values)),
        "std": std,
        "min": float(np.min(values)),
        "p25": float(p25),
        "p75": float(p75),
        "iqr": float(p75 - p25),
        "max": float(np.max(values)),
        "cv_abs": float(std / abs(mean)) if abs(mean) > 1.0e-12 else math.nan,
    }


def objective_kpi_rows(
    algorithm: str, scenario: str, results: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    axes = results["citylearn_v3_report"]["objective_axis_kpis"]
    for axis, payload in axes.items():
        for kpi, item in payload["kpis"].items():
            comparison = item.get("comparison") or {}
            trace = item.get("trace") or {}
            value = finite_float(item.get("value"))
            baseline = finite_float(comparison.get("baseline"))
            lower = trace.get("lower_is_better")
            available = bool(comparison.get("available"))
            delta = (
                value - baseline
                if value is not None and baseline is not None
                else None
            )
            gain = None
            if (
                value is not None
                and baseline is not None
                and isinstance(lower, bool)
                and available
            ):
                signed = -delta if lower else delta
                denominator = abs(baseline)
                if denominator < 1.0e-12:
                    denominator = max(abs(value), 1.0)
                gain = signed / denominator
            rows.append(
                {
                    "run_id": RUN_ID,
                    "algorithm": algorithm,
                    "scenario": scenario,
                    "axis": axis,
                    "dimension": OBJECTIVES[axis]["dimension"],
                    "kpi": kpi,
                    "value": value,
                    "baseline": baseline,
                    "value_minus_baseline": delta,
                    "lower_is_better": lower,
                    "comparison_available": available,
                    "improved_vs_baseline": comparison.get(
                        "improved_vs_baseline"
                    ),
                    "signed_relative_gain": gain,
                    "source": trace.get("source"),
                    "note": trace.get("note"),
                }
            )
    return rows


def coverage_and_kpis() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[tuple[str, str], dict[str, Any]],
]:
    coverage_rows: list[dict[str, Any]] = []
    district_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    building_raw: list[pd.DataFrame] = []
    behavior_raw: list[pd.DataFrame] = []
    results_map: dict[tuple[str, str], dict[str, Any]] = {}

    for algorithm in ALGORITHMS:
        for scenario in SCENARIOS:
            data_dir = FULL_ROOT / algorithm / scenario / "data"
            results_path = data_dir / "results.json"
            building_path = data_dir / "building_kpis.csv"
            behavior_path = data_dir / "building_behavior_summary.csv"
            timeseries_path = data_dir / "timeseries.csv"
            trace_path = data_dir / "trace.csv"
            for path in (
                results_path,
                building_path,
                behavior_path,
                timeseries_path,
                trace_path,
            ):
                if not path.exists():
                    raise FileNotFoundError(path)

            results = read_json(results_path)
            results_map[(algorithm, scenario)] = results
            all_values = results["citylearn_v3_report"]["all_values"]
            building = pd.read_csv(building_path)
            behavior = pd.read_csv(behavior_path)
            expected_kpis = int(building["cost_function"].nunique())
            expected_buildings = int(building["name"].nunique())
            if int(results.get("episodes_recorded") or 0) != 50:
                raise ValueError(
                    f"{algorithm}/{scenario}: episodes_recorded != 50"
                )
            if len(building) != 1275:
                raise ValueError(f"{algorithm}/{scenario}: building rows != 1275")
            if expected_kpis != 75 or expected_buildings != 17:
                raise ValueError(
                    f"{algorithm}/{scenario}: expected 75 KPI x 17 buildings"
                )
            if len(behavior) != 17:
                raise ValueError(
                    f"{algorithm}/{scenario}: behavior rows != 17"
                )

            coverage_rows.append(
                {
                    "run_id": RUN_ID,
                    "algorithm": algorithm,
                    "scenario": scenario,
                    "episodes_recorded": int(results["episodes_recorded"]),
                    "episode_summaries_current_file": len(
                        results.get("episode_summaries") or []
                    ),
                    "timeseries_rows_current_file": int(
                        results.get("timeseries_rows") or 0
                    ),
                    "trace_rows_current_file": int(
                        results.get("trace_rows") or 0
                    ),
                    "district_kpis": len(all_values),
                    "buildings": expected_buildings,
                    "building_kpi_types": expected_kpis,
                    "building_kpi_rows": len(building),
                    "building_behavior_rows": len(behavior),
                    "results_bytes": results_path.stat().st_size,
                    "timeseries_bytes": timeseries_path.stat().st_size,
                    "trace_bytes": trace_path.stat().st_size,
                    "drive_source": DRIVE_URL,
                }
            )

            for kpi, value in all_values.items():
                district_rows.append(
                    {
                        "run_id": RUN_ID,
                        "algorithm": algorithm,
                        "scenario": scenario,
                        "kpi": kpi,
                        "value": finite_float(value),
                    }
                )

            objective_rows.extend(
                objective_kpi_rows(algorithm, scenario, results)
            )

            building.insert(0, "scenario", scenario)
            building.insert(0, "algorithm", algorithm)
            building_raw.append(building)

            behavior.insert(0, "scenario", scenario)
            behavior.insert(0, "algorithm", algorithm)
            behavior_raw.append(behavior)

    return (
        pd.DataFrame(coverage_rows),
        pd.DataFrame(district_rows),
        pd.DataFrame(objective_rows),
        pd.concat(building_raw, ignore_index=True),
        pd.concat(behavior_raw, ignore_index=True),
        results_map,
    )


def summarize_building_kpis(building: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (algorithm, scenario, kpi), group in building.groupby(
        ["algorithm", "scenario", "cost_function"], sort=True
    ):
        values = pd.to_numeric(group["value"], errors="coerce").dropna().to_numpy()
        rows.append(
            {
                "algorithm": algorithm,
                "scenario": scenario,
                "kpi": kpi,
                **descriptive(values),
            }
        )
    return pd.DataFrame(rows)


def summarize_behavior(behavior: pd.DataFrame) -> pd.DataFrame:
    id_columns = {"algorithm", "scenario", "agent", "grid_role_control"}
    numeric_columns = [
        column
        for column in behavior.columns
        if column not in id_columns
        and pd.to_numeric(behavior[column], errors="coerce").notna().any()
    ]
    rows: list[dict[str, Any]] = []
    for (algorithm, scenario), group in behavior.groupby(
        ["algorithm", "scenario"], sort=True
    ):
        for metric in numeric_columns:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy()
            rows.append(
                {
                    "algorithm": algorithm,
                    "scenario": scenario,
                    "metric": metric,
                    **descriptive(values),
                    "sum": float(np.sum(values)) if values.size else math.nan,
                }
            )
    return pd.DataFrame(rows)


def episode_rows(
    results_map: dict[tuple[str, str], dict[str, Any]]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for algorithm in ALGORITHMS:
        for scenario in SCENARIOS:
            results = results_map[(algorithm, scenario)]
            summaries = list(results.get("episode_summaries") or [])
            if algorithm == "HAPPO":
                previous = (
                    RUN_ROOT
                    / algorithm
                    / scenario
                    / "figures"
                    / "tables"
                    / "episode_summary.csv"
                )
                if not previous.exists():
                    raise FileNotFoundError(previous)
                old = pd.read_csv(previous).to_dict("records")
                summaries = old + summaries
            by_episode: dict[int, dict[str, Any]] = {}
            for item in summaries:
                episode = int(item["episode"])
                by_episode[episode] = item
            if sorted(by_episode) != list(range(50)):
                raise ValueError(
                    f"{algorithm}/{scenario}: no se reconstruyeron episodios 0..49"
                )
            for episode, item in sorted(by_episode.items()):
                rows.append(
                    {
                        "algorithm": algorithm,
                        "scenario": scenario,
                        "episode": episode,
                        "steps": int(float(item["steps"])),
                        "reward_mean_average": float(
                            item["reward_mean_average"]
                        ),
                        "reward_sum_total": float(item["reward_sum_total"]),
                        "source": (
                            "Drive pre-resume episode_summary + final results"
                            if algorithm == "HAPPO"
                            else "Drive results.json episode_summaries"
                        ),
                    }
                )
    return pd.DataFrame(rows)


def episode_descriptives(episodes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (algorithm, scenario), group in episodes.groupby(
        ["algorithm", "scenario"], sort=True
    ):
        values = group.sort_values("episode")["reward_mean_average"].to_numpy()
        x = np.arange(len(values), dtype=float)
        slope = float(np.polyfit(x, values, deg=1)[0])
        rows.append(
            {
                "algorithm": algorithm,
                "scenario": scenario,
                **descriptive(values),
                "first_episode": float(values[0]),
                "last_episode": float(values[-1]),
                "absolute_change_last_minus_first": float(
                    values[-1] - values[0]
                ),
                "relative_change_abs_denominator": float(
                    (values[-1] - values[0]) / max(abs(values[0]), 1.0e-12)
                ),
                "linear_slope_per_episode": slope,
                "best_episode": int(
                    group.iloc[int(np.argmax(values))]["episode"]
                ),
                "best_reward_mean": float(np.max(values)),
                "worst_episode": int(
                    group.iloc[int(np.argmin(values))]["episode"]
                ),
                "worst_reward_mean": float(np.min(values)),
            }
        )
    return pd.DataFrame(rows)


def audit_stored_deltas(district: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    families = [
        (
            "carbon_emissions",
            "carbon_emissions_baseline",
            "carbon_emissions_control",
            "carbon_emissions_delta",
            "kgCO2",
        ),
        (
            "electricity_cost",
            "electricity_cost_baseline",
            "electricity_cost_control",
            "electricity_cost_delta",
            "EUR",
        ),
    ]
    for (algorithm, scenario), group in district.groupby(
        ["algorithm", "scenario"], sort=True
    ):
        values = dict(zip(group["kpi"], group["value"]))
        for family, baseline_key, control_key, stored_key, unit in families:
            if not all(
                key in values for key in (baseline_key, control_key, stored_key)
            ):
                continue
            baseline = float(values[baseline_key])
            control = float(values[control_key])
            stored = float(values[stored_key])
            recomputed = control - baseline
            discrepancy = stored - recomputed
            rows.append(
                {
                    "algorithm": algorithm,
                    "scenario": scenario,
                    "family": family,
                    "unit": unit,
                    "baseline": baseline,
                    "control": control,
                    "stored_delta": stored,
                    "recomputed_control_minus_baseline": recomputed,
                    "stored_minus_recomputed": discrepancy,
                    "relative_discrepancy_pct": (
                        100.0 * discrepancy / abs(recomputed)
                        if abs(recomputed) > 1.0e-12
                        else math.nan
                    ),
                    "consistent_at_1e_6_relative": bool(
                        np.isclose(stored, recomputed, rtol=1.0e-6, atol=1.0e-9)
                    ),
                    "impact_rule": (
                        "Usar control-baseline recalculado para el impacto total; "
                        "conservar stored_delta solo para trazabilidad."
                    ),
                }
            )
    return pd.DataFrame(rows)


def building_metric_vectors(
    building: pd.DataFrame,
    scenario: str,
    baseline_metric: str,
    control_metric: str,
) -> dict[str, np.ndarray]:
    vectors: dict[str, np.ndarray] = {}
    for algorithm in ALGORITHMS:
        sub = building[
            (building["algorithm"] == algorithm)
            & (building["scenario"] == scenario)
            & building["cost_function"].isin(
                [baseline_metric, control_metric]
            )
        ].copy()
        pivot = sub.pivot(
            index="name", columns="cost_function", values="value"
        ).sort_index()
        baseline = pivot[baseline_metric].astype(float).to_numpy()
        control = pivot[control_metric].astype(float).to_numpy()
        vectors[algorithm] = 100.0 * (baseline - control) / np.abs(baseline)
    return vectors


def flex_vectors(
    results_map: dict[tuple[str, str], dict[str, Any]]
) -> dict[str, np.ndarray]:
    vectors: dict[str, np.ndarray] = {}
    for algorithm in ALGORITHMS:
        values = results_map[(algorithm, "E1")]["citylearn_v3_report"][
            "all_values"
        ]
        vectors[algorithm] = np.array(
            [100.0 * (1.0 - float(values[kpi])) for kpi in FLEX_KPIS],
            dtype=float,
        )
    return vectors


def analyze_objective_vectors(
    axis: str, vectors: dict[str, np.ndarray]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    descriptive_rows: list[dict[str, Any]] = []
    impact_rows: list[dict[str, Any]] = []
    for algorithm in ALGORITHMS:
        values = np.asarray(vectors[algorithm], dtype=float)
        desc = descriptive(values)
        descriptive_rows.append(
            {
                "axis": axis,
                "scenario": OBJECTIVES[axis]["scenario"],
                "dimension": OBJECTIVES[axis]["dimension"],
                "algorithm": algorithm,
                **desc,
                "favorable_units": int(np.sum(values > 0)),
                "unfavorable_units": int(np.sum(values < 0)),
                "zero_units": int(np.sum(values == 0)),
            }
        )
        try:
            test = stats.wilcoxon(
                values,
                zero_method="wilcox",
                alternative="two-sided",
                method="auto",
            )
            statistic = float(test.statistic)
            p_value = float(test.pvalue)
        except ValueError:
            statistic, p_value = 0.0, 1.0
        impact_rows.append(
            {
                "axis": axis,
                "scenario": OBJECTIVES[axis]["scenario"],
                "algorithm": algorithm,
                "n": len(values),
                "wilcoxon_statistic": statistic,
                "p_raw": p_value,
                "rank_biserial": rank_biserial_signed(values),
                "median_effect_percent": float(np.median(values)),
            }
        )
    adjusted = holm_adjust([row["p_raw"] for row in impact_rows])
    for row, p_adjusted in zip(impact_rows, adjusted):
        row["p_holm"] = p_adjusted
        row["significant_holm"] = bool(p_adjusted < ALPHA)
        row["effect_direction"] = (
            "favorable"
            if row["median_effect_percent"] > 0
            else "desfavorable"
            if row["median_effect_percent"] < 0
            else "nulo"
        )

    groups = [np.asarray(vectors[a], dtype=float) for a in ALGORITHMS]
    friedman = stats.friedmanchisquare(*groups)
    n_blocks = len(groups[0])
    kendall_w = float(friedman.statistic) / (
        n_blocks * (len(ALGORITHMS) - 1)
    )
    omnibus_rows = [
        {
            "axis": axis,
            "scenario": OBJECTIVES[axis]["scenario"],
            "test": "Friedman",
            "n_blocks": n_blocks,
            "algorithms": len(ALGORITHMS),
            "statistic": float(friedman.statistic),
            "p_value": float(friedman.pvalue),
            "kendall_w": kendall_w,
            "significant": bool(friedman.pvalue < ALPHA),
        }
    ]

    posthoc_rows: list[dict[str, Any]] = []
    for first, second in combinations(ALGORITHMS, 2):
        test = stats.wilcoxon(
            vectors[first],
            vectors[second],
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        differences = vectors[first] - vectors[second]
        posthoc_rows.append(
            {
                "axis": axis,
                "scenario": OBJECTIVES[axis]["scenario"],
                "algorithm_1": first,
                "algorithm_2": second,
                "n_pairs": len(differences),
                "wilcoxon_statistic": float(test.statistic),
                "p_raw": float(test.pvalue),
                "median_difference_effect_pct": float(
                    np.median(differences)
                ),
                "rank_biserial": rank_biserial_signed(differences),
            }
        )
    adjusted = holm_adjust([row["p_raw"] for row in posthoc_rows])
    for row, p_adjusted in zip(posthoc_rows, adjusted):
        row["p_holm"] = p_adjusted
        row["significant_holm"] = bool(p_adjusted < ALPHA)

    return (
        pd.DataFrame(descriptive_rows),
        pd.DataFrame(impact_rows),
        pd.concat(
            [pd.DataFrame(omnibus_rows), pd.DataFrame(posthoc_rows)],
            ignore_index=True,
            sort=False,
        ),
    )


def primary_objective_values(
    district: pd.DataFrame,
    results_map: dict[tuple[str, str], dict[str, Any]],
) -> pd.DataFrame:
    lookup = {
        (row.algorithm, row.scenario, row.kpi): float(row.value)
        for row in district.itertuples()
        if pd.notna(row.value)
    }
    rows: list[dict[str, Any]] = []
    for algorithm in ALGORITHMS:
        e1 = results_map[(algorithm, "E1")]["citylearn_v3_report"][
            "all_values"
        ]
        flex_values = [float(e1[kpi]) for kpi in FLEX_KPIS]
        flex_composite = float(np.mean(flex_values))
        rows.append(
            {
                "axis": "OE1",
                "scenario": "E1",
                "dimension": OBJECTIVES["OE1"]["dimension"],
                "algorithm": algorithm,
                "primary_metric": "flex_composite",
                "baseline": 1.0,
                "control": flex_composite,
                "control_minus_baseline": flex_composite - 1.0,
                "favorable_effect_percent": 100.0 * (1.0 - flex_composite),
                "peak_average": flex_values[0],
                "ramping_average": flex_values[1],
                "one_minus_load_factor_average": flex_values[2],
                "unit": "ratio CityLearn; baseline=1",
            }
        )
        for axis, scenario, prefix, unit in (
            ("OE2", "E2", "carbon_emissions", "kgCO2"),
            ("OE3", "E3", "electricity_cost", "EUR"),
        ):
            baseline = lookup[(algorithm, scenario, f"{prefix}_baseline")]
            control = lookup[(algorithm, scenario, f"{prefix}_control")]
            rows.append(
                {
                    "axis": axis,
                    "scenario": scenario,
                    "dimension": OBJECTIVES[axis]["dimension"],
                    "algorithm": algorithm,
                    "primary_metric": f"{prefix}_total",
                    "baseline": baseline,
                    "control": control,
                    "control_minus_baseline": control - baseline,
                    "favorable_effect_percent": (
                        100.0 * (baseline - control) / abs(baseline)
                    ),
                    "peak_average": math.nan,
                    "ramping_average": math.nan,
                    "one_minus_load_factor_average": math.nan,
                    "unit": unit,
                }
            )
    frame = pd.DataFrame(rows)
    frame["rank_within_objective"] = frame.groupby("axis")[
        "favorable_effect_percent"
    ].rank(method="min", ascending=False).astype(int)
    return frame


def global_ranking(primary: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    pivot = primary.pivot(
        index="algorithm",
        columns="axis",
        values="favorable_effect_percent",
    ).loc[ALGORITHMS, ["OE1", "OE2", "OE3"]]
    matrix = pivot.to_numpy(dtype=float)

    shifted = matrix - np.min(matrix, axis=0)
    denominators = np.sqrt(np.sum(shifted**2, axis=0))
    normalized = np.divide(
        shifted,
        denominators,
        out=np.zeros_like(shifted),
        where=denominators > 0,
    )
    weighted = normalized * (1.0 / 3.0)
    ideal = np.max(weighted, axis=0)
    anti_ideal = np.min(weighted, axis=0)
    distance_ideal = np.sqrt(np.sum((weighted - ideal) ** 2, axis=1))
    distance_anti = np.sqrt(
        np.sum((weighted - anti_ideal) ** 2, axis=1)
    )
    topsis = np.divide(
        distance_anti,
        distance_ideal + distance_anti,
        out=np.zeros_like(distance_anti),
        where=(distance_ideal + distance_anti) > 0,
    )

    minmax = np.divide(
        matrix - np.min(matrix, axis=0),
        np.max(matrix, axis=0) - np.min(matrix, axis=0),
        out=np.full_like(matrix, 0.5),
        where=(np.max(matrix, axis=0) - np.min(matrix, axis=0)) > 0,
    )
    ranks = np.vstack(
        [
            stats.rankdata(-matrix[:, column], method="average")
            for column in range(matrix.shape[1])
        ]
    ).T

    rows = []
    for index, algorithm in enumerate(ALGORITHMS):
        rows.append(
            {
                "algorithm": algorithm,
                "effect_flexibility_percent": matrix[index, 0],
                "effect_co2_percent": matrix[index, 1],
                "effect_cost_percent": matrix[index, 2],
                "mean_raw_effect_percent": float(np.mean(matrix[index])),
                "mean_minmax_score": float(np.mean(minmax[index])),
                "topsis_equal_weight": float(topsis[index]),
                "mean_objective_rank": float(np.mean(ranks[index])),
            }
        )
    frame = pd.DataFrame(rows)
    frame["rank_topsis"] = (
        frame["topsis_equal_weight"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    frame = frame.sort_values(
        ["rank_topsis", "algorithm"], ignore_index=True
    )

    friedman = stats.friedmanchisquare(
        *[
            matrix[ALGORITHMS.index(algorithm), :]
            for algorithm in ALGORITHMS
        ]
    )
    global_test = {
        "test": "Friedman sobre tres efectos primarios (OE1, OE2, OE3)",
        "n_dimensions": 3,
        "algorithms": 4,
        "statistic": float(friedman.statistic),
        "p_value": float(friedman.pvalue),
        "kendall_w": float(friedman.statistic) / (3 * (4 - 1)),
        "significant": bool(friedman.pvalue < ALPHA),
        "leader_topsis": str(frame.iloc[0]["algorithm"]),
        "leader_topsis_score": float(
            frame.iloc[0]["topsis_equal_weight"]
        ),
    }
    return frame, global_test


def hypothesis_decisions(
    objective_impact: pd.DataFrame,
    objective_tests: pd.DataFrame,
    primary: pd.DataFrame,
    global_test: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    alternative_supported: dict[str, bool] = {}
    for axis, meta in OBJECTIVES.items():
        impact = objective_impact[objective_impact["axis"] == axis]
        omnibus = objective_tests[
            (objective_tests["axis"] == axis)
            & (objective_tests["test"] == "Friedman")
        ].iloc[0]
        significant_impacts = impact[impact["significant_holm"]]
        posthoc = objective_tests[
            (objective_tests["axis"] == axis)
            & (objective_tests["test"].isna())
            & (objective_tests["significant_holm"] == True)  # noqa: E712
        ]
        impact_condition = not significant_impacts.empty
        difference_condition = bool(omnibus["significant"]) and not posthoc.empty
        supported = impact_condition and difference_condition
        alternative_supported[axis] = supported

        primary_axis = primary[primary["axis"] == axis].sort_values(
            "favorable_effect_percent", ascending=False
        )
        leader = primary_axis.iloc[0]
        if supported:
            decision = (
                f"Rechazar {meta['h0']} y respaldar {meta['h1']}; "
                "el impacto significativo es predominantemente desfavorable."
            )
        elif impact_condition and not difference_condition:
            decision = (
                f"No respaldar {meta['h1']}: existe impacto significativo en "
                "al menos un algoritmo, pero no diferencias globales/post hoc."
            )
        elif not impact_condition and difference_condition:
            decision = (
                f"No respaldar {meta['h1']}: existen diferencias entre "
                "algoritmos, pero no impacto frente al baseline."
            )
        else:
            decision = (
                f"No rechazar {meta['h0']} y no respaldar {meta['h1']}."
            )
        rows.append(
            {
                "scope": axis,
                "scenario": meta["scenario"],
                "dimension": meta["dimension"],
                "null_hypothesis": meta["h0"],
                "alternative_hypothesis": meta["h1"],
                "impact_condition": impact_condition,
                "difference_condition": difference_condition,
                "friedman_statistic": float(omnibus["statistic"]),
                "friedman_p": float(omnibus["p_value"]),
                "kendall_w": float(omnibus["kendall_w"]),
                "significant_impact_algorithms_holm": ", ".join(
                    significant_impacts["algorithm"].tolist()
                )
                or "ninguno",
                "significant_posthoc_pairs_holm": "; ".join(
                    (
                        posthoc["algorithm_1"]
                        + "-"
                        + posthoc["algorithm_2"]
                    ).tolist()
                )
                or "ninguno",
                "primary_leader": leader["algorithm"],
                "leader_effect_percent": float(
                    leader["favorable_effect_percent"]
                ),
                "decision": decision,
                "objective_compliance": (
                    "Cumplido cuantitativamente: se calculó el impacto, se "
                    "compararon cuatro algoritmos y se identificó el líder."
                ),
            }
        )

    all_specific = all(alternative_supported.values())
    global_difference = bool(global_test["significant"])
    h1g_supported = all_specific and global_difference
    rows.append(
        {
            "scope": "OG",
            "scenario": "E1-E3",
            "dimension": "Gestión coordinada integral",
            "null_hypothesis": "H0G",
            "alternative_hypothesis": "H1G",
            "impact_condition": all_specific,
            "difference_condition": global_difference,
            "friedman_statistic": global_test["statistic"],
            "friedman_p": global_test["p_value"],
            "kendall_w": global_test["kendall_w"],
            "significant_impact_algorithms_holm": (
                "La condición conjunta no se cumple en OE1, OE2 y OE3"
            ),
            "significant_posthoc_pairs_holm": "no aplicable con n=3 dimensiones",
            "primary_leader": global_test["leader_topsis"],
            "leader_effect_percent": global_test["leader_topsis_score"],
            "decision": (
                "Respaldar H1G y rechazar H0G."
                if h1g_supported
                else (
                    "No rechazar H0G y no respaldar H1G bajo la regla "
                    "conjuntiva: no se demostraron impacto y diferencias en "
                    "las tres dimensiones; el ranking global es descriptivo."
                )
            ),
            "objective_compliance": (
                "OG cumplido cuantitativamente: se integraron los tres efectos "
                "y TOPSIS identificó el mejor desempeño relativo, sin afirmar "
                "superioridad estadística global."
            ),
        }
    )
    return pd.DataFrame(rows)


def write_markdown(
    coverage: pd.DataFrame,
    primary: pd.DataFrame,
    objective_desc: pd.DataFrame,
    objective_impact: pd.DataFrame,
    objective_tests: pd.DataFrame,
    ranking: pd.DataFrame,
    global_test: dict[str, Any],
    decisions: pd.DataFrame,
    delta_audit: pd.DataFrame,
) -> None:
    lines = [
        "# Análisis cuantitativo completo de KPI y métricas",
        "",
        f"- Corrida: `{RUN_ID}`.",
        f"- Fuente exclusiva: [{DRIVE_URL}]({DRIVE_URL}).",
        "- Cobertura: 12/12 tratamientos; 50 episodios registrados por "
        "tratamiento; 17 edificios; 75 KPI por edificio; 1.275 filas por "
        "tratamiento.",
        "- HAPPO: los 50 episodios se reconstruyen sin imputación con 49 "
        "episodios pre-resume y el episodio final 49 del archivo Drive "
        "posterior al resume.",
        "",
        "## Indicadores primarios por objetivo",
        "",
        primary.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Pruebas y decisiones",
        "",
        decisions.to_markdown(index=False, floatfmt=".6g"),
        "",
        "## Ranking global",
        "",
        ranking.to_markdown(index=False, floatfmt=".6f"),
        "",
        (
            f"Friedman global sobre los tres efectos primarios: "
            f"χ²={global_test['statistic']:.6f}, "
            f"p={global_test['p_value']:.6f}, "
            f"Kendall W={global_test['kendall_w']:.6f}."
        ),
        "",
        "## Auditoría de deltas almacenados",
        "",
        "Los impactos totales de CO₂ y costo usan la resta directa "
        "`control - baseline`. Los campos `*_delta` almacenados se conservan "
        "en las matrices, pero no sustituyen esa resta cuando discrepan.",
        "",
        delta_audit.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Archivos cuantitativos",
        "",
        "- `run_coverage_quantitative.csv`: cobertura de los 12 tratamientos.",
        "- `district_all_kpis_long.csv`: todos los KPI distritales.",
        "- `objective_all_kpis_numeric.csv`: todos los KPI por eje.",
        "- `building_kpis_raw.csv`: 15.300 valores (12×17×75).",
        "- `building_kpis_summary.csv`: descriptivos de cada KPI por tratamiento.",
        "- `building_behavior_numeric_summary.csv`: métricas de comportamiento.",
        "- `episode_metrics_50.csv`: 600 observaciones episódicas.",
        "- `episode_descriptive_50.csv`: descriptivos de recompensa.",
        "- `primary_objective_values.csv`: impacto directo por objetivo.",
        "- `objective_effect_descriptive.csv`: efectos porcentuales.",
        "- `objective_impact_wilcoxon_holm.csv`: impacto frente al baseline.",
        "- `objective_friedman_posthoc_holm.csv`: diferencias entre algoritmos.",
        "- `global_ranking_topsis.csv`: selección global.",
        "- `hypothesis_decisions_quantitative.csv`: decisión de hipótesis.",
    ]
    (OUT_DIR / "complete_quantitative_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (
        coverage,
        district,
        objective_all,
        building,
        behavior,
        results_map,
    ) = coverage_and_kpis()

    building_summary = summarize_building_kpis(building)
    behavior_summary = summarize_behavior(behavior)
    episodes = episode_rows(results_map)
    episode_summary = episode_descriptives(episodes)
    delta_audit = audit_stored_deltas(district)

    primary = primary_objective_values(district, results_map)
    vectors_by_axis = {
        "OE1": flex_vectors(results_map),
        "OE2": building_metric_vectors(
            building,
            "E2",
            "building_emissions_total_baseline_kgco2",
            "building_emissions_total_control_kgco2",
        ),
        "OE3": building_metric_vectors(
            building,
            "E3",
            "building_cost_total_baseline_eur",
            "building_cost_total_control_eur",
        ),
    }

    desc_frames = []
    impact_frames = []
    test_frames = []
    for axis, vectors in vectors_by_axis.items():
        desc, impact, tests = analyze_objective_vectors(axis, vectors)
        desc_frames.append(desc)
        impact_frames.append(impact)
        test_frames.append(tests)
    objective_desc = pd.concat(desc_frames, ignore_index=True)
    objective_impact = pd.concat(impact_frames, ignore_index=True)
    objective_tests = pd.concat(test_frames, ignore_index=True)

    ranking, global_test = global_ranking(primary)
    decisions = hypothesis_decisions(
        objective_impact,
        objective_tests,
        primary,
        global_test,
    )

    target_objective_all = pd.concat(
        [
            objective_all[
                (objective_all["axis"] == axis)
                & (objective_all["scenario"] == meta["scenario"])
            ]
            for axis, meta in OBJECTIVES.items()
        ],
        ignore_index=True,
    )
    comparable = target_objective_all[
        target_objective_all["signed_relative_gain"].notna()
    ].copy()

    files = {
        "run_coverage_quantitative.csv": coverage,
        "district_all_kpis_long.csv": district,
        "objective_all_kpis_numeric.csv": objective_all,
        "objective_target_scenario_kpis_numeric.csv": target_objective_all,
        "objective_comparable_kpi_gains.csv": comparable,
        "building_kpis_raw.csv": building,
        "building_kpis_summary.csv": building_summary,
        "building_behavior_raw.csv": behavior,
        "building_behavior_numeric_summary.csv": behavior_summary,
        "episode_metrics_50.csv": episodes,
        "episode_descriptive_50.csv": episode_summary,
        "stored_delta_consistency_audit.csv": delta_audit,
        "primary_objective_values.csv": primary,
        "objective_effect_descriptive.csv": objective_desc,
        "objective_impact_wilcoxon_holm.csv": objective_impact,
        "objective_friedman_posthoc_holm.csv": objective_tests,
        "global_ranking_topsis.csv": ranking,
        "hypothesis_decisions_quantitative.csv": decisions,
    }
    for name, frame in files.items():
        frame.to_csv(OUT_DIR / name, index=False, encoding="utf-8-sig")

    write_markdown(
        coverage,
        primary,
        objective_desc,
        objective_impact,
        objective_tests,
        ranking,
        global_test,
        decisions,
        delta_audit,
    )

    audit = {
        "run_id": RUN_ID,
        "drive_source": DRIVE_URL,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(FULL_ROOT),
        "output_dir": str(OUT_DIR),
        "algorithms": ALGORITHMS,
        "scenarios": SCENARIOS,
        "coverage": {
            "treatments": len(coverage),
            "episodes_recorded_total": int(
                coverage["episodes_recorded"].sum()
            ),
            "district_kpi_values": len(district),
            "objective_kpi_values_all_axes": len(objective_all),
            "target_scenario_objective_kpi_values": len(
                target_objective_all
            ),
            "comparable_target_kpi_gains": len(comparable),
            "building_kpi_values": len(building),
            "building_behavior_rows": len(behavior),
            "episode_rows_reconstructed": len(episodes),
        },
        "global_test": global_test,
        "global_leader_topsis": ranking.iloc[0].to_dict(),
        "hypothesis_decisions": decisions.to_dict("records"),
        "delta_inconsistencies": int(
            (~delta_audit["consistent_at_1e_6_relative"]).sum()
        ),
        "limitations": [
            "Una sola semilla (seed=0) por tratamiento.",
            "La inferencia OE2/OE3 usa 17 edificios como bloques emparejados; "
            "no sustituye réplicas independientes de entrenamiento.",
            "La inferencia OE1 usa tres KPI de flexibilidad como bloques.",
            "HAPPO conserva 49 episodios históricos y el episodio final post-resume "
            "en artefactos separados; se unen por índice 0..49 sin imputación.",
        ],
    }
    (OUT_DIR / "complete_quantitative_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
