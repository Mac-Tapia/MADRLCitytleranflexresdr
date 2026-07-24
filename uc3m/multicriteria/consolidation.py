"""Consolidation helpers: master tables, learning curves, Pareto plots."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from uc3m.multicriteria.criteria import CRITERION_SPECS, mean_std_report
from uc3m.multicriteria.topsis import pareto_nondominated


def master_table_from_seed_metrics(
    seed_metrics: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    scenario: str = "base",
) -> pd.DataFrame:
    """Build master table: rows=algorithms, columns=metric mean±std.

    ``seed_metrics`` maps algorithm -> metric_name -> seed values.
    """

    rows = []
    for algo, metrics in seed_metrics.items():
        row: Dict[str, object] = {"algorithm": algo, "scenario": scenario}
        for name, values in metrics.items():
            arr = np.asarray(list(values), dtype=float)
            arr = arr[np.isfinite(arr)]
            mean = float(np.mean(arr)) if arr.size else float("nan")
            std = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
            row[f"{name}_mean"] = mean
            row[f"{name}_std"] = std
            row[f"{name}_n"] = int(arr.size)
            row[f"{name}_mean_pm_std"] = mean_std_report(mean, std)
        rows.append(row)
    return pd.DataFrame(rows)


def decision_matrix_frame(
    decision_matrix: Mapping[str, Mapping[str, float]],
) -> pd.DataFrame:
    frame = pd.DataFrame.from_dict(decision_matrix, orient="index")
    frame.index.name = "algorithm"
    # Attach kind annotations as a secondary header-friendly table.
    kinds = {cid: CRITERION_SPECS[cid].kind for cid in frame.columns if cid in CRITERION_SPECS}
    frame.attrs["criteria_kind"] = kinds
    return frame


def learning_curve_bands(
    curves: Mapping[str, Sequence[Sequence[float]]],
) -> Dict[str, pd.DataFrame]:
    """Per-algorithm mean±std learning curves over seeds.

    ``curves[algo]`` = list of seed trajectories (equal or unequal length;
    truncated to the shortest common length).
    """

    out: Dict[str, pd.DataFrame] = {}
    for algo, seed_curves in curves.items():
        arrays = [np.asarray(c, dtype=float) for c in seed_curves if len(c)]
        if not arrays:
            continue
        length = min(len(a) for a in arrays)
        stacked = np.vstack([a[:length] for a in arrays])
        mean = np.mean(stacked, axis=0)
        std = np.std(stacked, axis=0, ddof=1) if stacked.shape[0] > 1 else np.zeros(length)
        out[algo] = pd.DataFrame(
            {
                "step": np.arange(length),
                "mean": mean,
                "std": std,
                "lo": mean - std,
                "hi": mean + std,
            }
        )
    return out


def plot_learning_curves(
    curves: Mapping[str, Sequence[Sequence[float]]],
    *,
    ax=None,
    title: str = "Learning curves (mean ± std over seeds)",
):
    """Plot overlapping learning curves with std bands."""

    import matplotlib.pyplot as plt

    bands = learning_curve_bands(curves)
    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(8, 4.5))
    for algo, frame in bands.items():
        ax.plot(frame["step"], frame["mean"], label=algo)
        ax.fill_between(frame["step"], frame["lo"], frame["hi"], alpha=0.2)
    ax.set_xlabel("Step / episode")
    ax.set_ylabel("Reward")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    return ax


def plot_pareto_cost_co2_flex(
    points: Mapping[str, Mapping[str, float]],
    *,
    cost_key: str = "C1",
    co2_key: str = "C2",
    flex_key: str = "C3",
    ax=None,
    title: str = "Pareto: cost vs CO2 avoided (marker size = flexibility)",
):
    """Scatter cost vs CO2 with flexibility as marker size."""

    import matplotlib.pyplot as plt

    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(7, 5))
    flex_vals = np.asarray([float(p[flex_key]) for p in points.values()], dtype=float)
    flex_min = float(np.min(flex_vals)) if flex_vals.size else 0.0
    flex_max = float(np.max(flex_vals)) if flex_vals.size else 1.0
    span = max(flex_max - flex_min, 1e-9)

    for algo, vals in points.items():
        size = 80 + 320 * ((float(vals[flex_key]) - flex_min) / span)
        ax.scatter(
            float(vals[cost_key]),
            float(vals[co2_key]),
            s=size,
            label=algo,
            alpha=0.85,
        )
        ax.annotate(algo, (float(vals[cost_key]), float(vals[co2_key])), fontsize=9)

    front = pareto_nondominated(
        points,
        minimize=(cost_key,),
        maximize=(co2_key, flex_key),
    )
    ax.set_xlabel(f"{cost_key} cost (minimize)")
    ax.set_ylabel(f"{co2_key} CO2 avoided (maximize)")
    ax.set_title(title + f" | nondominated: {', '.join(front)}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return ax, front


def plot_degradation_bars(
    degradation: Mapping[str, float],
    *,
    ax=None,
    title: str = "Performance degradation by scenario",
    ylabel: str = "Degradation",
):
    """Bar chart of robustness / scalability degradation per algorithm."""

    import matplotlib.pyplot as plt

    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(7, 4))
    algos = list(degradation.keys())
    values = [float(degradation[a]) for a in algos]
    ax.bar(algos, values, color="#4C78A8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def save_consolidation_bundle(
    output_dir: Path | str,
    *,
    master_table: pd.DataFrame,
    decision_matrix: Mapping[str, Mapping[str, float]],
    ranking: Sequence[Mapping[str, object]],
    figures: Optional[Mapping[str, object]] = None,
) -> Dict[str, str]:
    """Persist CSV/JSON artefacts for the selection pipeline."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}

    master_path = out / "master_metrics_table.csv"
    master_table.to_csv(master_path, index=False)
    paths["master_table"] = str(master_path)

    dm = decision_matrix_frame(decision_matrix)
    dm_path = out / "decision_matrix.csv"
    dm.to_csv(dm_path)
    paths["decision_matrix"] = str(dm_path)

    rank_path = out / "topsis_ranking.csv"
    pd.DataFrame(list(ranking)).to_csv(rank_path, index=False)
    paths["ranking"] = str(rank_path)

    if figures:
        fig_dir = out / "figures"
        fig_dir.mkdir(exist_ok=True)
        for name, fig in figures.items():
            target = fig_dir / f"{name}.png"
            fig.savefig(target, dpi=140, bbox_inches="tight")
            paths[f"figure_{name}"] = str(target)
    return paths
