"""End-to-end multicriteria MADRL selection pipeline (TOPSIS + AHP)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from uc3m.multicriteria.ahp import (
    DEFAULT_AHP_PAIRWISE,
    NonPositiveAutomaticAHP,
    ahp_priority_weights,
    ahp_rank_alternatives,
    default_weights_or_ahp,
)
from uc3m.multicriteria.artifacts import (
    ILLUSTRATIVE_DECISION_MATRIX,
    load_decision_matrix,
    pareto_quality_from_decision_matrix,
)
from uc3m.multicriteria.consolidation import (
    decision_matrix_frame,
    master_table_from_seed_metrics,
    plot_degradation_bars,
    plot_learning_curves,
    plot_pareto_cost_co2_flex,
    save_consolidation_bundle,
)
from uc3m.multicriteria.criteria import CRITERION_SPECS, criteria_manifest, mean_std_report
from uc3m.multicriteria.scenarios import DEFAULT_PROTOCOL, list_scenarios
from uc3m.multicriteria.stats_tests import (
    kruskal_wallis,
    pairwise_wilcoxon,
    significance_gate_top_metrics,
)
from uc3m.multicriteria.topsis import (
    topsis_rank,
    weight_sweep_sensitivity,
)

# Re-export for notebook/script convenience.
__all__ = [
    "ILLUSTRATIVE_DECISION_MATRIX",
    "run_selection_pipeline",
]


def _criteria_kind() -> Dict[str, str]:
    return {cid: spec.kind for cid, spec in CRITERION_SPECS.items()}


def run_selection_pipeline(
    *,
    repo: Optional[Path] = None,
    run_dir: Optional[Path] = None,
    scenario: str = "E1",
    prefer_real: bool = True,
    allow_illustrative_fill: bool = False,
    use_ahp_weights: bool = True,
    output_dir: Optional[Path] = None,
    make_plots: bool = False,
    sensitivity_samples: int = 48,
    seed_curves: Optional[Mapping[str, Sequence[Sequence[float]]]] = None,
    degradation: Optional[Mapping[str, float]] = None,
    episode_index_origin: int = 1,
) -> Dict[str, Any]:
    """Run metrics load → AHP weights → TOPSIS → sensitivity → stats gates."""

    loaded = load_decision_matrix(
        repo=repo,
        run_dir=run_dir,
        scenario=scenario,
        prefer_real=prefer_real,
        allow_illustrative_fill=allow_illustrative_fill,
        episode_index_origin=episode_index_origin,
    )
    decision_matrix = loaded["decision_matrix"]
    criteria_kind = loaded.get("criteria_kind") or _criteria_kind()
    active_manifest = criteria_manifest()
    if (loaded.get("criterion_units") or {}).get("C3") == "kWh":
        active_manifest["criteria"]["C3"].update(
            name="illustrative_flexibility_activated", kind="benefit", unit="kWh", higher_is_better=True
        )
    active_frame = decision_matrix_frame(decision_matrix)
    active_frame.attrs["criteria_kind"] = dict(criteria_kind)
    active_frame.attrs["criterion_units"] = {
        cid: spec["unit"] for cid, spec in active_manifest["criteria"].items()
    }
    active_frame.attrs["orientation"] = {
        cid: "min" if kind == "cost" else "max" for cid, kind in criteria_kind.items()
    }

    ahp_info = ahp_priority_weights(
        DEFAULT_AHP_PAIRWISE,
        require_consistent=True,
    )
    weights = default_weights_or_ahp(use_ahp=use_ahp_weights)

    topsis = topsis_rank(
        decision_matrix,
        weights=weights,
        criteria_kind=criteria_kind,
    )
    try:
        ahp_only = ahp_rank_alternatives(
            decision_matrix,
            criteria_kind=criteria_kind,
            criteria_pairwise=DEFAULT_AHP_PAIRWISE,
        )
    except NonPositiveAutomaticAHP as exc:
        # Signed deltas remain valid TOPSIS/Pareto inputs. AHP cannot silently
        # replace them by epsilon or invent an additive utility transformation.
        ahp_only = {"status": "unavailable_nonpositive_automatic_scores", "reason": str(exc),
                    "ranking": [], "method": "ahp_only"}
    sensitivity = weight_sweep_sensitivity(
        decision_matrix,
        base_weights=weights,
        relative_delta=0.20,
        n_samples=sensitivity_samples,
        criteria_kind=criteria_kind,
    )
    pareto_quality = pareto_quality_from_decision_matrix(decision_matrix, criteria_kind=criteria_kind)
    pareto_front = pareto_quality["front"]
    topsis_winner = str(topsis["ranking"][0]["algorithm"])
    topsis_second = (
        str(topsis["ranking"][1]["algorithm"]) if len(topsis["ranking"]) > 1 else topsis_winner
    )
    ahp_winner = str(ahp_only["ranking"][0]["algorithm"]) if ahp_only["ranking"] else None

    seed_samples = loaded.get("seed_metric_samples") or {}
    stats_block: Dict[str, object] = {}
    if seed_samples:
        # Kruskal on C2 seed samples across algorithms (benefit metric).
        if "C2" in seed_samples:
            stats_block["kruskal_C2"] = kruskal_wallis(seed_samples["C2"])
            stats_block["pairwise_wilcoxon_C2"] = pairwise_wilcoxon(seed_samples["C2"])
        stats_block["significance_gate"] = significance_gate_top_metrics(
            seed_samples,
            top_criteria=("C1", "C2"),
            first=topsis_winner,
            second=topsis_second,
        )

    ranking_consistency = {
        "topsis_winner": topsis_winner,
        "ahp_winner": ahp_winner,
        "topsis_ahp_agree": topsis_winner == ahp_winner,
        "topsis_on_pareto_front": topsis_winner in pareto_front,
        "sensitivity_majority_winner": sensitivity.get("majority_winner"),
        "sensitivity_stability_ratio": sensitivity.get("stability_ratio"),
    }

    # Prefer real Drive episodic curves; synthetic only when illustrative fill allowed.
    if seed_curves is None:
        real_curves = loaded.get("learning_curves") or {}
        if real_curves:
            seed_curves = real_curves
        elif allow_illustrative_fill:
            seed_curves = _synthetic_learning_curves(decision_matrix)
        else:
            raise RuntimeError(
                "real_only multicriteria: missing Drive episode learning curves"
            )

    figures = {}
    fig_axes = []
    if make_plots:
        lc_title = (
            "Learning curves (Drive 50 ep, reward_mean)"
            if str(loaded.get("source", "")).startswith("real_drive")
            else "Learning curves (mean ± std over seeds)"
        )
        ax = plot_learning_curves(seed_curves, title=lc_title)
        figures["learning_curves"] = ax.figure
        fig_axes.append(ax)
        # The legacy plot helper maximizes its marker criterion. Adapt the raw
        # ratio to a preference solely for drawing; retain raw values in tables.
        cost_ratio = criteria_kind["C3"] == "cost"
        plot_points = {
            algo: dict(values, C3_preference=(-1 if cost_ratio else 1) * float(values["C3"]))
            for algo, values in decision_matrix.items()
        }
        ax2, _front = plot_pareto_cost_co2_flex(
            plot_points, flex_key="C3_preference",
            title=("Pareto: cost vs CO2 avoided (larger marker = lower flexibility ratio)"
                   if cost_ratio else "Illustrative Pareto (larger marker = activated flexibility kWh)"),
        )
        loaded["extras"]["pareto_plot_front"] = _front
        loaded["extras"]["pareto_plot_transform"] = (
            "C3_preference=-C3_ratio_to_baseline" if cost_ratio else "C3_preference=C3_illustrative_kWh"
        )
        if set(_front) != set(pareto_front):
            raise RuntimeError("Pareto plot and decision criteria have inconsistent orientation")
        figures["pareto_cost_co2_flex"] = ax2.figure
        fig_axes.append(ax2)
        deg = degradation or {
            algo: float(decision_matrix[algo]["C6"]) for algo in decision_matrix
        }
        deg_title = (
            "Early–late episode reward gap (C6, Drive 50 ep)"
            if str(loaded.get("source", "")).startswith("real_drive")
            else "Train-test gap (C6)"
        )
        ax3 = plot_degradation_bars(deg, title=deg_title, ylabel="Gap")
        figures["degradation_bars"] = ax3.figure
        fig_axes.append(ax3)

    # Master table from decision matrix means (std unknown → 0 unless seeds exist).
    seed_metrics = {}
    for algo, vals in decision_matrix.items():
        seed_metrics[algo] = {}
        for cid, value in vals.items():
            if cid in seed_samples and algo in seed_samples[cid]:
                seed_metrics[algo][cid] = list(seed_samples[cid][algo])
            else:
                seed_metrics[algo][cid] = [float(value)]
    master = master_table_from_seed_metrics(seed_metrics, scenario=scenario)
    # The shared table helper historically emits std=0 for n=1. At this boundary
    # report seed uncertainty honestly, including the per-seed episodic C4 scalar.
    for cid in CRITERION_SPECS:
        count = master[f"{cid}_n"]
        master[f"{cid}_n_seeds"] = count
        master.loc[count < 2, f"{cid}_std"] = float("nan")
        master[f"{cid}_uncertainty_status"] = [
            "estimated" if n > 1 else "insufficient_replicas" for n in count
        ]
        master[f"{cid}_mean_pm_std"] = [
            mean_std_report(mean, std)
            for mean, std in zip(master[f"{cid}_mean"], master[f"{cid}_std"])
        ]

    saved_paths: Dict[str, str] = {}
    if output_dir is not None:
        saved_paths = save_consolidation_bundle(
            output_dir,
            master_table=master,
            decision_matrix=decision_matrix,
            ranking=topsis["ranking"],
            figures=figures or None,
        )
        report_path = Path(output_dir) / "selection_report.json"
        serializable = {
            "source": loaded["source"],
            "scenario": scenario,
            "weights": weights,
            "ahp": {
                "consistency_ratio": ahp_info["consistency_ratio"],
                "consistent": ahp_info["consistent"],
                "weights": ahp_info["weights"],
            },
            "topsis_ranking": topsis["ranking"],
            "ahp_ranking": ahp_only["ranking"],
            "ahp_only_status": ahp_only.get("status", "ok"),
            "ahp_only_reason": ahp_only.get("reason"),
            "pareto_front": pareto_front,
            "pareto_quality": pareto_quality,
            "ranking_consistency": ranking_consistency,
            "sensitivity": {
                "majority_winner": sensitivity.get("majority_winner"),
                "stability_ratio": sensitivity.get("stability_ratio"),
                "winner_counts": sensitivity.get("winner_counts"),
            },
            "stats": stats_block,
            "provenance": loaded["provenance"],
            "protocol": DEFAULT_PROTOCOL.as_dict(),
            "scenarios": list_scenarios(),
            "criteria_manifest": active_manifest,
            "criterion_sampling": loaded.get("extras", {}).get("seed_metric_replication", {}),
            "episode_curve_index": loaded.get("extras", {}).get("episode_curve_index", {}),
            "seed_metric_summary": [
                {key: (None if isinstance(value, float) and not math.isfinite(value) else value)
                 for key, value in row.items()}
                for row in master.to_dict(orient="records")
            ],
        }
        report_path.write_text(
            json.dumps(serializable, indent=2, ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )
        saved_paths["selection_report"] = str(report_path)

    if make_plots:
        import matplotlib.pyplot as plt

        plt.close("all")

    return {
        "decision_matrix": decision_matrix,
        "decision_matrix_frame": active_frame,
        "master_table": master,
        "weights": weights,
        "ahp": ahp_info,
        "topsis": topsis,
        "ahp_only": ahp_only,
        "sensitivity": sensitivity,
        "pareto_front": pareto_front,
        "pareto_quality": pareto_quality,
        "ranking_consistency": ranking_consistency,
        "stats": stats_block,
        "source": loaded["source"],
        "provenance": loaded["provenance"],
        "extras": loaded.get("extras", {}),
        "saved_paths": saved_paths,
        "protocol": DEFAULT_PROTOCOL,
        "scenarios": list_scenarios(),
    }


def _synthetic_learning_curves(
    decision_matrix: Mapping[str, Mapping[str, float]],
    *,
    n_steps: int = 40,
    n_seeds: int = 5,
) -> Dict[str, list]:
    """Cheap illustrative curves scaled by C5 (sample efficiency)."""

    import numpy as np

    rng = np.random.default_rng(0)
    curves: Dict[str, list] = {}
    for algo, vals in decision_matrix.items():
        speed = max(float(vals.get("C5", 400.0)), 1.0)
        asymptote = -float(vals.get("C1", 1200.0)) / 1000.0
        seed_list = []
        for _ in range(n_seeds):
            noise = rng.normal(0.0, 0.03, size=n_steps)
            t = np.arange(n_steps) / max(n_steps - 1, 1)
            # Faster algorithms (lower C5) rise sooner.
            rate = 400.0 / speed
            series = asymptote * (1.0 - np.exp(-rate * t * 3.0)) + noise
            seed_list.append(series.tolist())
        curves[algo] = seed_list
    return curves
