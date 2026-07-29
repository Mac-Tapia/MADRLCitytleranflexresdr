"""Unit tests for multicriteria MADRL selection (TOPSIS, AHP, metrics, Wilcoxon)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from uc3m.multicriteria.ahp import (
    DEFAULT_AHP_PAIRWISE,
    ahp_priority_weights,
    ahp_rank_alternatives,
    consistency_ratio,
)
from uc3m.multicriteria.artifacts import ILLUSTRATIVE_DECISION_MATRIX
from uc3m.multicriteria.criteria import (
    DEFAULT_CRITERION_WEIGHTS,
    aggregate_seed_values,
    compute_dimension_metrics,
    co2_avoided,
    criteria_manifest,
    flexibility_activated,
    inter_seed_variance,
    mean_std_report,
    reward_drop_count,
    steps_to_fraction_of_asymptotic,
    total_operating_cost,
)
from uc3m.multicriteria.pipeline import run_selection_pipeline
from uc3m.multicriteria.scenarios import DEFAULT_PROTOCOL
from uc3m.multicriteria.reward import multiobjective_reward
from uc3m.multicriteria.stats_tests import (
    cliffs_delta,
    cliffs_delta_magnitude,
    dunns_posthoc_holm,
    friedman_test,
    kruskal_wallis,
    run_full_methodology_battery,
    run_oe_battery,
    significance_gate_top_metrics,
    wilcoxon_signed_rank,
)
from uc3m.multicriteria.topsis import pareto_nondominated, topsis_rank, vector_normalize


def test_default_protocol_uses_twelve_seeds():
    assert DEFAULT_PROTOCOL.n_seeds == 12
    assert ">=12 seeds" in criteria_manifest()["reporting"]


def test_aggregate_seed_values_mean_std():
    agg = aggregate_seed_values("R", [1.0, 2.0, 3.0], unit="reward")
    assert agg.n == 3
    assert agg.mean == pytest.approx(2.0)
    assert agg.std == pytest.approx(1.0)
    assert "±" in mean_std_report(agg.mean, agg.std)


def test_technical_metric_formulas():
    prices = [2.0, 3.0]
    energy = [[1.0, 1.0], [0.5, 0.0]]  # agents x time
    assert total_operating_cost(prices, energy) == pytest.approx(2 * 1 + 3 * 1 + 2 * 0.5 + 3 * 0)
    assert co2_avoided(100.0, 80.0) == pytest.approx(20.0)
    assert flexibility_activated([[1.0, 2.0]], [[0.0, 1.0]]) == pytest.approx(2.0)


def test_stability_and_efficiency_helpers():
    assert inter_seed_variance([1.0, 1.0, 1.0]) == pytest.approx(0.0)
    assert reward_drop_count([1.0, 1.2, 0.5, 1.3], drop_fraction=0.2) >= 1
    steps = steps_to_fraction_of_asymptotic(list(range(1, 21)), fraction=0.9)
    assert steps < 20


def test_compute_dimension_metrics_bundle():
    metrics = compute_dimension_metrics(
        seed_returns=[1.0, 1.1, 0.9],
        episode_rewards=[0.5, 1.0, 0.7, 1.2],
        step_rewards=list(np.linspace(0.0, 1.0, 50)),
        prices=[1.0, 1.0],
        energy_by_agent=[[1.0, 2.0]],
        energy_ref=[[0.0, 0.0]],
        co2_baseline=10.0,
        co2_policy=7.0,
        n_violation_steps=5,
        n_total_steps=100,
        violation_excesses=[0.1, 0.2],
        elapsed_seconds=20.0,
        n_env_steps=2000,
        reward_by_n_agents={5: 1.0, 50: 0.7},
        time_by_n_agents={5: 10.0, 20: 30.0, 50: 80.0},
        reward_train=1.0,
        reward_test=0.8,
        reward_noise_0=1.0,
        reward_noise_20=0.85,
    )
    assert metrics["technical_performance"]["co2_avoided"] == pytest.approx(3.0)
    assert metrics["constraint_compliance"]["violation_rate_pct"] == pytest.approx(5.0)
    assert "inter_seed_variance" in metrics["training_stability"]
    assert "steps_to_90pct_asymptotic" in metrics["sample_compute_efficiency"]
    assert "reward_degradation_N50_minus_N5" in metrics["scalability"]
    assert metrics["robustness_generalization"]["train_test_gap"] == pytest.approx(0.2)


def test_multiobjective_reward_shape():
    r = multiobjective_reward([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], [0.0, 1.0, 2.0])
    assert r.shape == (3,)
    assert np.all(np.isfinite(r))


def test_ahp_consistency_ratio_below_threshold():
    info = consistency_ratio(DEFAULT_AHP_PAIRWISE)
    assert info["consistency_ratio"] < 0.1
    assert info["consistent"] is True
    weights = ahp_priority_weights(DEFAULT_AHP_PAIRWISE)
    w = weights["weights"]
    assert set(w) == {"C1", "C2", "C3", "C4", "C5", "C6"}
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-6)
    # C1/C2 should be the heaviest criteria.
    assert w["C1"] == pytest.approx(w["C2"], abs=0.02)
    assert w["C1"] > w["C4"]


def test_topsis_vector_normalization_and_illustrative_ranking():
    x = np.asarray([[3.0, 4.0], [0.0, 0.0]], dtype=float)
    r = vector_normalize(x)
    assert r[0, 0] == pytest.approx(1.0)
    assert r[0, 1] == pytest.approx(1.0)

    result = topsis_rank(
        ILLUSTRATIVE_DECISION_MATRIX,
        weights=DEFAULT_CRITERION_WEIGHTS,
    )
    ranking = [row["algorithm"] for row in result["ranking"]]
    # Exact TOPSIS on the methodology section 3.2 matrix (the printed
    # ranking table in the text was approximate; this is the computed order).
    assert ranking == ["MASAC", "HAPPO", "MATD3", "MAAC"]
    assert result["ranking"][0]["closeness"] > result["ranking"][-1]["closeness"]
    for row in result["ranking"]:
        assert 0.0 <= row["closeness"] <= 1.0


def test_ahp_only_ranking_runs():
    kinds = {cid: "cost" if cid in {"C1", "C4", "C5", "C6"} else "benefit" for cid in DEFAULT_CRITERION_WEIGHTS}
    result = ahp_rank_alternatives(
        ILLUSTRATIVE_DECISION_MATRIX,
        criteria_kind=kinds,
        criteria_pairwise=DEFAULT_AHP_PAIRWISE,
    )
    assert len(result["ranking"]) == 4
    assert math.isclose(sum(result["scores"].values()), 1.0, rel_tol=1e-5)


def test_pareto_nondomination_hook():
    front = pareto_nondominated(
        ILLUSTRATIVE_DECISION_MATRIX,
        minimize=("C1",),
        maximize=("C2", "C3"),
    )
    assert "MAAC" in front  # lowest cost + high CO2/flex
    assert isinstance(front, list)


def test_wilcoxon_and_kruskal_small_fixtures():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    b = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 11.0]
    wc = wilcoxon_signed_rank(a, b)
    assert wc["status"] in {"ok", "identical_samples"}
    assert wc["p_value"] is not None
    assert wc["significant"] is True

    kw = kruskal_wallis({"A": a, "B": b, "C": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0]})
    assert kw["status"] == "ok"
    assert kw["p_value"] < 0.05

    gate = significance_gate_top_metrics(
        {
            "C1": {"MATD3": a, "HAPPO": b},
            "C2": {"MATD3": b, "HAPPO": a},
        },
        first="MATD3",
        second="HAPPO",
    )
    assert "details" in gate
    assert gate["any_significant"] is True


def test_pipeline_illustrative_end_to_end(tmp_path):
    result = run_selection_pipeline(
        prefer_real=False,
        output_dir=tmp_path,
        make_plots=False,
        sensitivity_samples=12,
    )
    assert result["source"] == "illustrative"
    assert result["ahp"]["consistent"] is True
    assert result["topsis"]["ranking"][0]["algorithm"] == "MASAC"
    assert (tmp_path / "selection_report.json").is_file()
    assert (tmp_path / "topsis_ranking.csv").is_file()
    assert result["ranking_consistency"]["topsis_on_pareto_front"] in {True, False}


def test_pipeline_real_only_drive_50ep_no_illustrative(tmp_path):
    """Closure path: C1–C6 and curves must come from Drive artefacts only."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    run = repo / "outputs" / "madrl_v3_20260627_164047"
    district = (
        run
        / "resumen_comparativo"
        / "multiobjetivo"
        / "district_objectives_by_algorithm.csv"
    )
    if not district.is_file():
        pytest.skip("canonical Drive district_objectives missing")
    ep = run / "MAAC" / "E1" / "figures" / "tables" / "episode_summary.csv"
    if not ep.is_file():
        pytest.skip("canonical episode_summary missing")

    result = run_selection_pipeline(
        repo=repo,
        run_dir=run,
        scenario="E1",
        prefer_real=True,
        allow_illustrative_fill=False,
        output_dir=tmp_path,
        make_plots=True,
        sensitivity_samples=8,
    )
    assert result["source"] == "real_drive_50ep_c1c6"
    assert set(result["decision_matrix"]) >= {"MAAC", "MASAC", "MATD3"}
    for algo, prov in result["provenance"].items():
        for cid, tag in prov.items():
            assert "illustrative" not in str(tag).lower(), (algo, cid, tag)
            assert "synthetic" not in str(tag).lower(), (algo, cid, tag)
    assert (tmp_path / "figures" / "learning_curves.png").is_file()
    assert (tmp_path / "figures" / "degradation_bars.png").is_file()
    assert (tmp_path / "figures" / "pareto_cost_co2_flex.png").is_file()


def test_merge_skips_algorithms_without_real_technical_kpis():
    from uc3m.multicriteria.artifacts import merge_with_illustrative

    partial = {
        "MASAC": {"C1": 100.0, "C2": 10.0, "C3": 1.0},
        "MATD3": {"C1": 90.0, "C2": 12.0, "C3": 1.1},
        # HAPPO / MAAC intentionally missing real C1–C3
    }
    matrix, prov = merge_with_illustrative(partial, require_real_technical=True)
    assert set(matrix) == {"MASAC", "MATD3"}
    assert matrix["MASAC"]["C1"] == 100.0
    assert prov["MASAC"]["C4"].startswith("illustrative")


def test_oe_battery_minimum_keys_and_cost_orientation():
    rng = np.random.default_rng(0)
    groups = {
        "HAPPO": list(rng.normal(400, 10, 12)),
        "MAAC": list(rng.normal(320, 10, 12)),
        "MASAC": list(rng.normal(480, 10, 12)),
        "MATD3": list(rng.normal(360, 10, 12)),
    }
    result = run_oe_battery(
        groups,
        objective="OE.3",
        higher_is_better=False,
        complementary=False,
        expected_n_seeds=12,
    )
    assert result["kruskal_wallis"]["status"] == "ok"
    assert result["epsilon_squared"] is not None
    assert len(result["dunn_holm"]) == 6
    assert result["winner"]["winners"]
    assert result["sample_coverage"]["complete"] is True
    assert result["sample_coverage"]["expected_n_seeds"] == 12
    # Lower cost → better after orientation: MAAC should have highest mean rank.
    ranks = result["kruskal_wallis"]["mean_ranks"]
    assert ranks["MAAC"] == max(ranks.values())
    delta = cliffs_delta(groups["MAAC"], groups["MASAC"])
    assert cliffs_delta_magnitude(delta) in {"negligible", "small", "medium", "large"}


def test_full_methodology_battery_smoke():
    rng = np.random.default_rng(1)
    oe = {
        "OE.1": {
            "HAPPO": list(rng.normal(-0.5, 0.05, 12)),
            "MAAC": list(rng.normal(-0.6, 0.05, 12)),
            "MASAC": list(rng.normal(-0.7, 0.05, 12)),
            "MATD3": list(rng.normal(-0.65, 0.05, 12)),
        },
        "OE.2": {
            "HAPPO": list(rng.normal(900, 30, 12)),
            "MAAC": list(rng.normal(850, 30, 12)),
            "MASAC": list(rng.normal(980, 30, 12)),
            "MATD3": list(rng.normal(820, 30, 12)),
        },
        "OE.3": {
            "HAPPO": list(rng.normal(400, 20, 12)),
            "MAAC": list(rng.normal(320, 20, 12)),
            "MASAC": list(rng.normal(480, 20, 12)),
            "MATD3": list(rng.normal(360, 20, 12)),
        },
    }
    battery = run_full_methodology_battery(
        oe,
        oe_higher_is_better={"OE.1": True, "OE.2": False, "OE.3": False},
        complementary=True,
        page_order=["MASAC", "HAPPO", "MATD3", "MAAC"],
        expected_n_seeds=12,
    )
    assert set(battery["oe"]) == {"OE.1", "OE.2", "OE.3"}
    assert battery["expected_n_seeds"] == 12
    assert battery["sample_unit"] == "seed"
    for oe_name in ("OE.1", "OE.2", "OE.3"):
        assert battery["oe"][oe_name]["sample_coverage"]["complete"] is True
    assert battery["og"]["friedman"]["status"] == "ok"
    assert battery["og"]["kendalls_w"] is not None
    assert battery["og"]["nemenyi"]["pairs"]
    assert battery["og"]["topsis"]["ranking"]
    assert "topsis_vs_friedman" in battery["og"]
    assert "quade" in battery["og"]["complementary"]
    dunn = dunns_posthoc_holm(oe["OE.1"], higher_is_better=True)
    assert dunn
    fr = friedman_test(
        {
            "OE.1": {a: float(np.mean(v)) for a, v in oe["OE.1"].items()},
            "OE.2": {a: float(np.mean(v)) for a, v in oe["OE.2"].items()},
            "OE.3": {a: float(np.mean(v)) for a, v in oe["OE.3"].items()},
        },
        higher_is_better={"OE.1": True, "OE.2": False, "OE.3": False},
    )
    assert fr["status"] == "ok"
