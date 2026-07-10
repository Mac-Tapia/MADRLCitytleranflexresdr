"""Metricas de convergencia, aprendizaje y heterogeneidad por algoritmo MADRL."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RUN_ID = "madrl_v3_20260627_164047"
EPISODE_CSV = (
    REPO
    / "outputs"
    / "_drive_madrl"
    / "full_data"
    / "analysis_real_drive"
    / "tables"
    / "district_episode_kpis.csv"
)
DISTRICT_CSV = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "multiobjetivo" / "district_objectives_by_algorithm.csv"
BUILDING_CSV = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "multiobjetivo" / "building_objectives_by_algorithm.csv"
OUT_JSON = (
    REPO
    / "outputs"
    / RUN_ID
    / "resumen_comparativo"
    / "estadistica"
    / "madrl_per_algorithm_metrics.json"
)

ALGOS_FULL = ("MATD3", "MAAC", "MASAC")
ALGOS_ALL = ("MATD3", "MAAC", "MASAC", "HAPPO")
SCENARIOS = ("E1", "E2", "E3")

BUILDING_KPI = {
    "E1": "flex_composite_proxy",
    "E2": "carbon_emissions_delta_kgco2",
    "E3": "electricity_cost_delta_eur",
}

DISTRICT_KPI = {
    "E1": "flex_composite",
    "E2": "carbon_emissions_delta_kg",
    "E3": "electricity_cost_delta_eur",
}

FIG_RUN = REPO / "outputs" / RUN_ID


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _plateau_episode(values: list[float], window: int = 5, tol: float = 0.05) -> int | None:
    if len(values) < window + 1:
        return None
    final = statistics.mean(values[-window:])
    denom = max(abs(final), 1e-9)
    for i in range(window - 1, len(values)):
        rolling = statistics.mean(values[max(0, i - window + 1) : i + 1])
        if abs(rolling - final) / denom < tol:
            return i
    return None


def convergence_metrics(algo: str) -> dict[str, Any]:
    rows = [r for r in _read_csv(EPISODE_CSV) if r["algorithm"] == algo]
    out: dict[str, Any] = {}
    for scen in SCENARIOS:
        rewards = [float(r["reward_mean"]) for r in rows if r["scenario"] == scen]
        if not rewards:
            continue
        n = len(rewards)
        first10 = statistics.mean(rewards[: min(10, n)])
        last10 = statistics.mean(rewards[-min(10, n) :])
        out[scen] = {
            "n_episodes": n,
            "reward_mean": statistics.mean(rewards),
            "reward_median": statistics.median(rewards),
            "reward_std": statistics.pstdev(rewards) if n > 1 else 0.0,
            "reward_min": min(rewards),
            "reward_max": max(rewards),
            "first10_mean": first10,
            "last10_mean": last10,
            "improvement_first_to_last": last10 - first10,
            "plateau_episode": _plateau_episode(rewards),
            "coefficient_of_variation": (
                statistics.pstdev(rewards) / abs(statistics.mean(rewards)) if n > 1 else 0.0
            ),
        }
    return out


def district_kpis(algo: str) -> dict[str, dict[str, float]]:
    rows = [r for r in _read_csv(DISTRICT_CSV) if r["algorithm"] == algo]
    out: dict[str, dict[str, float]] = {}
    for scen in SCENARIOS:
        row = next((r for r in rows if r["scenario"] == scen), None)
        if not row:
            continue
        out[scen] = {
            "flex_composite": float(row["flex_composite"]),
            "carbon_emissions_delta_kg": float(row["carbon_emissions_delta_kg"]),
            "electricity_cost_delta_eur": float(row["electricity_cost_delta_eur"]),
            "ev_departure_success_rate": float(row["ev_departure_success_rate"]),
            "grid_import_delta": float(row["grid_import_delta"]),
            "peak_average": float(row["peak_average"]),
            "ramping_average": float(row["ramping_average"]),
        }
    return out


def building_heterogeneity(algo: str) -> dict[str, dict[str, float]]:
    rows = [r for r in _read_csv(BUILDING_CSV) if r["algorithm"] == algo]
    out: dict[str, dict[str, float]] = {}
    for scen in SCENARIOS:
        kpi = BUILDING_KPI[scen]
        vals = [float(r[kpi]) for r in rows if r["scenario"] == scen and r.get(kpi)]
        if not vals:
            continue
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        out[scen] = {
            "n_buildings": len(vals),
            "mean": mean,
            "std": std,
            "cv": std / abs(mean) if mean else 0.0,
            "min": min(vals),
            "max": max(vals),
        }
    return out


def figure_paths(algo: str, scen: str) -> dict[str, str]:
    fig_dir = FIG_RUN / algo / scen / "figures"
    names = (
        "convergence_returns.png",
        "exploration_action_l2.png",
        "reward_timeseries.png",
        "axis_baseline_comparison.png",
        "agent_reward_contribution.png",
    )
    out: dict[str, str] = {}
    for name in names:
        path = fig_dir / name
        if path.is_file():
            out[name.replace(".png", "")] = str(path)
    return out


def algorithm_profile(algo: str, *, has_kpis: bool = True) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "algorithm": algo,
        "has_final_kpis": has_kpis,
        "convergence": convergence_metrics(algo),
        "figures": {scen: figure_paths(algo, scen) for scen in SCENARIOS},
    }
    if has_kpis:
        profile["district_kpis"] = district_kpis(algo)
        profile["building_heterogeneity"] = building_heterogeneity(algo)
    return profile


def build_all_profiles() -> dict[str, Any]:
    profiles = {
        "run_id": RUN_ID,
        "algorithms": {
            "MATD3": algorithm_profile("MATD3"),
            "MAAC": algorithm_profile("MAAC"),
            "MASAC": algorithm_profile("MASAC"),
            "HAPPO": algorithm_profile("HAPPO", has_kpis=False),
        },
    }
    return profiles


def write_metrics_json(path: Path | None = None) -> Path:
    target = path or OUT_JSON
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_all_profiles(), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


if __name__ == "__main__":
    out = write_metrics_json()
    print(f"OK -> {out}")
