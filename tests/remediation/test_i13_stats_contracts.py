"""I13-B mathematical regressions; real NumPy/SciPy, isolated temporary artifacts."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from uc3m.application.evaluation.fresh_analysis import kendall_w
from uc3m.multicriteria.ahp import ahp_priority_weights, consistency_ratio, ahp_rank_alternatives
from uc3m.multicriteria.artifacts import (
    decision_matrix_from_district_objectives,
    load_decision_matrix,
    load_episode_reward_series,
    pareto_quality_from_decision_matrix,
    training_stability_from_episode_rewards,
)
from uc3m.multicriteria.criteria import (
    CRITERION_SPECS, aggregate_seed_values, steps_to_fraction_of_asymptotic,
)
from uc3m.multicriteria.pipeline import run_selection_pipeline
from uc3m.multicriteria.stats_tests import (
    holm_correction, pairwise_wilcoxon, wilcoxon_signed_rank,
)
from uc3m.multicriteria.topsis import topsis_rank


@pytest.mark.parametrize("matrix", [
    [[1, 1, 2], [1, 1, 2]],
    [[1, 2, 3], [1, 2, 3]],
    [[1, 1, 2], [1, 2, 2], [3, 2, 1]],
])
def test_r011_kendall_matches_corrected_friedman(matrix):
    data = np.array(matrix)
    expected = stats.friedmanchisquare(*data.T).statistic / (len(data) * (data.shape[1] - 1))
    assert kendall_w(data) == pytest.approx(expected)


def test_r011_degenerate_and_reversal():
    assert kendall_w([[1, 1, 2], [1, 1, 2]]) == pytest.approx(1)
    assert kendall_w([[1, 2, 3], [3, 2, 1]]) == pytest.approx(0)
    assert kendall_w([[1, 1, 1], [2, 2, 2]]) == pytest.approx(0)
    assert kendall_w([[1, 2, 3]]) == pytest.approx(0)
    assert kendall_w([[1], [2]]) == pytest.approx(0)


@pytest.mark.parametrize("matrix", [
    np.eye(6), np.ones((2, 3)), np.ones((0, 0)),
    [[1, 2], [2, 1]], [[2, 1], [1, 1]],
    [[1, np.nan], [1, 1]], [[1, np.inf], [1, 1]],
    [[1, -2], [-0.5, 1]], np.array(1),
])
def test_r012_invalid_ahp_rejected_before_eigen(matrix):
    for function in (consistency_ratio, ahp_priority_weights):
        with pytest.raises(ValueError):
            function(matrix)


def test_r012_consistent_ratios_and_normalized_weights():
    weights = np.array([1, 2, 3, 4, 5, 6.0])
    matrix = weights[:, None] / weights[None, :]
    result = ahp_priority_weights(matrix)
    assert result["consistency_ratio"] == pytest.approx(0, abs=1e-12)
    assert result["consistency_ratio"] >= 0
    assert list(result["weights"].values()) == pytest.approx(weights / weights.sum())
    assert consistency_ratio(np.ones((1, 1)))["consistent"]


@pytest.mark.parametrize("weights", [[1, -1], [1, 0], [1], [1, np.nan]])
def test_r012_invalid_supplied_weights(weights):
    with pytest.raises(ValueError):
        consistency_ratio(np.ones((2, 2)), weights=weights)


@pytest.mark.parametrize("kind,value", [("cost", 0), ("cost", -1), ("benefit", 0), ("benefit", -1)])
def test_r012_automatic_ahp_does_not_clip_nonpositive_values(kind, value):
    matrix = {"a": {"C1": value, "C2": 2}, "b": {"C1": 3, "C2": 4}}
    with pytest.raises(ValueError, match="positive.*alternative_pairwise"):
        ahp_rank_alternatives(matrix, criteria_kind={"C1": kind, "C2": "benefit"},
                              criteria_pairwise=np.ones((2, 2)))
    # Explicit positive reciprocal judgments retain the supported alternative route.
    result = ahp_rank_alternatives(matrix, criteria_kind={"C1": kind, "C2": "benefit"},
                                   criteria_pairwise=np.ones((2, 2)),
                                   alternative_pairwise={"C1": np.array([[1, 2], [0.5, 1]])})
    assert len(result["ranking"]) == 2


def test_r012_signed_pipeline_preserves_topsis_and_declares_ahp_unavailable(tmp_path):
    campaign = _campaign(tmp_path)
    path = campaign / "resumen_comparativo" / "multiobjetivo" / "district_objectives_by_algorithm.csv"
    frame = pd.read_csv(path)
    frame["electricity_cost_delta_eur"] = [-10, -5]
    frame.to_csv(path, index=False)
    result = run_selection_pipeline(run_dir=campaign, sensitivity_samples=2)
    assert result["topsis"]["ranking"][0]["algorithm"] == "MASAC"
    assert result["ahp_only"]["status"] == "unavailable_nonpositive_automatic_scores"
    assert result["ranking_consistency"]["ahp_winner"] is None
    assert "alternative_pairwise" in result["ahp_only"]["reason"]


def _district(path, *, include_flex=True):
    rows = []
    for algorithm, ratio in [("MASAC", 0.8), ("MATD3", 1.2)]:
        row = dict(algorithm=algorithm, scenario="E1", electricity_cost_delta_eur=10,
                   carbon_emissions_delta_kg=-20, grid_import_delta=(-100 if ratio < 1 else 100))
        if include_flex:
            row["flex_composite"] = ratio
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def test_r013_ratio_orientation_topsis_and_pareto(tmp_path):
    path = tmp_path / "district.csv"
    _district(path)
    matrix, provenance = decision_matrix_from_district_objectives(path)
    matrix = {a: matrix[a] for a in ("MASAC", "MATD3")}
    spec = CRITERION_SPECS["C3"]
    assert spec.kind == "cost" and not spec.higher_is_better
    assert spec.unit == "ratio_to_baseline"
    assert matrix["MASAC"]["C3"] == pytest.approx(0.8)
    assert "ratio_to_baseline" in provenance["MASAC"]["C3"]
    result = topsis_rank(matrix, weights={c: 1/3 for c in ("C1", "C2", "C3")},
                         criteria_kind={c: CRITERION_SPECS[c].kind for c in matrix["MASAC"]})
    assert result["ranking"][0]["algorithm"] == "MASAC"
    pareto = pareto_quality_from_decision_matrix(matrix)
    assert pareto["front"] == ["MASAC"]
    assert pareto["orientation"] == ["min", "max", "min"]


def test_r013_no_absolute_import_fallback(tmp_path):
    path = tmp_path / "district.csv"
    _district(path, include_flex=False)
    matrix, provenance = decision_matrix_from_district_objectives(path)
    for algorithm in ("MASAC", "MATD3"):
        assert "C3" not in matrix[algorithm]
        assert "unavailable" in provenance[algorithm]["C3"]


def _campaign(tmp_path):
    district = tmp_path / "resumen_comparativo" / "multiobjetivo"
    district.mkdir(parents=True)
    _district(district / "district_objectives_by_algorithm.csv")
    for algo, rewards in [("MASAC", [1, 5]), ("MATD3", [2, 4])]:
        run = tmp_path / (algo.lower() + "_run")
        table = run / "E1" / "figures" / "tables"
        table.mkdir(parents=True)
        (run / "experiment.json").write_text(json.dumps(dict(algorithm=algo, scenario_id="E1", seed=0)))
        (run / "evidence.json").write_text(json.dumps(dict(status="verified", completed_episodes=2)))
        pd.DataFrame({"episode": [1, 2], "reward_mean": rewards}).to_csv(table / "episode_summary.csv", index=False)
    return tmp_path


def test_r014_one_variance_per_actual_seed(tmp_path):
    campaign = _campaign(tmp_path)
    loaded = load_decision_matrix(run_dir=campaign)
    assert loaded["decision_matrix"]["MASAC"]["C4"] == pytest.approx(8)
    assert loaded["seed_metric_samples"]["C4"]["MASAC"] == [8]
    assert loaded["learning_curves"]["MASAC"] == [[1, 5]]
    assert CRITERION_SPECS["C4"].name == "episodic_reward_variance_per_seed"
    result = run_selection_pipeline(run_dir=campaign, make_plots=False, sensitivity_samples=2)
    row = result["master_table"].set_index("algorithm").loc["MASAC"]
    assert row["C4_mean"] == pytest.approx(8)
    assert row["C4_n"] == row["C4_n_seeds"] == 1
    assert pd.isna(row["C4_std"])
    assert row["C4_uncertainty_status"] == "insufficient_replicas"


def test_r014_missing_variance_and_seed_uncertainty():
    assert "C4" not in training_stability_from_episode_rewards([1])
    one = aggregate_seed_values("C4", [8])
    assert one.n == 1 and one.std is None
    two = aggregate_seed_values("C4", [8, 2])
    assert two.mean == pytest.approx(5)
    assert two.std == pytest.approx(np.sqrt(18))


def test_r014_serialization_null_std_status_csv_and_no_nan_literal(tmp_path):
    campaign = _campaign(tmp_path / "campaign")
    output = tmp_path / "published"
    run_selection_pipeline(run_dir=campaign, output_dir=output, sensitivity_samples=2)
    text = (output / "selection_report.json").read_text(encoding="utf-8")
    assert "NaN" not in text and "Infinity" not in text
    report = json.loads(text)
    row = next(r for r in report["seed_metric_summary"] if r["algorithm"] == "MASAC")
    assert row["C4_std"] is None
    assert row["C4_n_seeds"] == 1 and row["C4_mean"] == 8
    assert row["C4_uncertainty_status"] == "insufficient_replicas"
    csv_row = pd.read_csv(output / "master_metrics_table.csv").set_index("algorithm").loc["MASAC"]
    assert pd.isna(csv_row["C4_std"])
    assert csv_row["C4_n_seeds"] == 1
    assert csv_row["C4_uncertainty_status"] == "insufficient_replicas"


def test_r013_plot_front_uses_same_ratio_orientation(tmp_path):
    import matplotlib
    matplotlib.use("Agg")
    campaign = _campaign(tmp_path)
    result = run_selection_pipeline(run_dir=campaign, make_plots=True, sensitivity_samples=2)
    assert result["extras"]["pareto_plot_front"] == result["pareto_front"]
    assert result["extras"]["pareto_plot_transform"] == "C3_preference=-C3_ratio_to_baseline"


def test_r013_legacy_illustration_has_separate_units_and_orientation():
    loaded = load_decision_matrix(prefer_real=False, allow_illustrative_fill=True)
    assert loaded["criteria_kind"]["C3"] == "benefit"
    assert loaded["criterion_units"]["C3"] == "kWh"
    result = run_selection_pipeline(prefer_real=False, allow_illustrative_fill=True, sensitivity_samples=2)
    assert result["topsis"]["criteria_kind"]["C3"] == "benefit"
    assert result["pareto_quality"]["orientation"] == ["min", "max", "max"]


@pytest.mark.parametrize("illustrative", [False, True])
def test_r013_returned_frame_metadata_matches_active_topsis_and_pareto(tmp_path, illustrative):
    if illustrative:
        result = run_selection_pipeline(prefer_real=False, allow_illustrative_fill=True, sensitivity_samples=2)
        expected_kind, expected_unit = "benefit", "kWh"
    else:
        result = run_selection_pipeline(run_dir=_campaign(tmp_path), sensitivity_samples=2)
        expected_kind, expected_unit = "cost", "ratio_to_baseline"
    frame = result["decision_matrix_frame"]
    assert frame.attrs["criteria_kind"] == result["topsis"]["criteria_kind"]
    assert frame.attrs["criteria_kind"]["C3"] == expected_kind
    assert frame.attrs["criterion_units"]["C3"] == expected_unit
    assert frame.attrs["orientation"]["C3"] == result["pareto_quality"]["orientation"][2]


def test_r013_no_kwh_illustrative_fill_into_real_ratio_matrix():
    from uc3m.multicriteria.artifacts import merge_with_illustrative
    partial = {"MASAC": {"C1": 10, "C2": 20}}
    matrix, provenance = merge_with_illustrative(partial)
    assert "C3" not in matrix["MASAC"]
    assert "unavailable" in provenance["MASAC"]["C3"]


def test_r014_other_seeds_do_not_become_episodes_or_hpo_replicas(tmp_path):
    campaign = _campaign(tmp_path)
    run = campaign / "hpo_candidate"
    table = run / "E1_s99" / "figures" / "tables"
    table.mkdir(parents=True)
    (run / "experiment.json").write_text(json.dumps(dict(algorithm="MASAC", scenario_id="E1", seed=99)))
    (run / "evidence.json").write_text(json.dumps(dict(status="verified")))
    pd.DataFrame({"episode": [1, 2], "reward_mean": [100, 200]}).to_csv(table / "episode_summary.csv", index=False)
    loaded = load_decision_matrix(run_dir=campaign)
    assert loaded["seed_metric_samples"]["C4"]["MASAC"] == [8]
    assert loaded["extras"]["seed_metric_replication"]["selected_seed"] == 0
    assert loaded["extras"]["seed_metric_replication"]["unit"] == "independent_training_seed"


def test_r014_missing_episode_does_not_reindex_or_impute(tmp_path):
    campaign = _campaign(tmp_path)
    for algo in ("masac", "matd3"):
        path = campaign / (algo + "_run") / "E1" / "figures" / "tables" / "episode_summary.csv"
        pd.DataFrame({"episode": [1, 2, 3], "reward_mean": [1, np.nan, 5]}).to_csv(path, index=False)
        (campaign / (algo + "_run") / "evidence.json").write_text(
            json.dumps(dict(status="verified", completed_episodes=3)))
    with pytest.raises(FileNotFoundError, match="missing campaign C1"):
        load_decision_matrix(run_dir=campaign)


@pytest.mark.parametrize("ids", [[1, 3], [1, 1], [1], [2], [1, 2.5], [-1, 1], [1, np.nan]])
def test_r014_episode_ids_reject_gaps_duplicates_and_nonintegers(tmp_path, ids):
    campaign = _campaign(tmp_path)
    path = campaign / "masac_run/E1/figures/tables/episode_summary.csv"
    pd.DataFrame({"episode": ids, "reward_mean": [1, 5][:len(ids)]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="episode"):
        load_episode_reward_series(campaign, algorithms=["MASAC"])


def test_r014_episode_column_is_required(tmp_path):
    campaign = _campaign(tmp_path)
    pd.DataFrame({"reward_mean": [1, 5]}).to_csv(
        campaign / "masac_run/E1/figures/tables/episode_summary.csv", index=False)
    with pytest.raises(ValueError, match="episode"):
        load_episode_reward_series(campaign, algorithms=["MASAC"])


def test_r014_sorted_ids_are_preserved_in_curve_metadata(tmp_path):
    campaign = _campaign(tmp_path)
    pd.DataFrame({"episode": [2, 1], "reward_mean": [5, 1]}).to_csv(
        campaign / "masac_run/E1/figures/tables/episode_summary.csv", index=False)
    loaded = load_decision_matrix(run_dir=campaign)
    assert loaded["learning_curves"]["MASAC"] == [[1, 5]]
    assert loaded["extras"]["episode_curve_index"]["MASAC"] == {
        "episode_ids": [1, 2], "episode_index_origin": 1, "expected_completed_episodes": 2,
    }


@pytest.mark.parametrize("origin", [0, 1])
def test_r014_explicit_origin_valid_without_rebasing_ids(tmp_path, origin):
    campaign = _campaign(tmp_path)
    for algo in ("masac", "matd3"):
        pd.DataFrame({"episode": [origin, origin + 1], "reward_mean": [1, 5]}).to_csv(
            campaign / (algo + "_run/E1/figures/tables/episode_summary.csv"), index=False)
    loaded = load_decision_matrix(run_dir=campaign, episode_index_origin=origin)
    assert loaded["seed_metric_samples"]["C4"]["MASAC"] == [8]
    assert loaded["extras"]["episode_curve_index"]["MASAC"]["episode_ids"] == [origin, origin + 1]


@pytest.mark.parametrize("ids", [[1, 2], [0, 2], [0, 0]])
def test_r014_zero_origin_missing_initial_internal_or_duplicate_rejected(tmp_path, ids):
    campaign = _campaign(tmp_path)
    pd.DataFrame({"episode": ids, "reward_mean": [1, 5]}).to_csv(
        campaign / "masac_run/E1/figures/tables/episode_summary.csv", index=False)
    with pytest.raises(ValueError, match="episode"):
        load_episode_reward_series(campaign, algorithms=["MASAC"], episode_index_origin=0)


def test_r019_bilateral_family_raw_and_holm_match_scipy():
    groups = {"a": [2, 3, 4], "b": [1, 1, 1], "c": [0, 2, 5]}
    rows = pairwise_wilcoxon(groups)
    raw = [stats.wilcoxon(groups[r["algorithm_a"]], groups[r["algorithm_b"]],
                           zero_method="wilcox", alternative="two-sided").pvalue for r in rows]
    assert [r["p_value"] for r in rows] == pytest.approx(raw)
    assert holm_correction([r["p_value"] for r in rows]) == pytest.approx(holm_correction(raw))


@pytest.mark.parametrize("curve", [[-1, -1, -1], [1, 1, 1], [0, 1, 2, 3, 4], [-5, -3, -1], [5, 3, 1]])
def test_r015_translation_invariant_progress(curve):
    index = steps_to_fraction_of_asymptotic(curve, asymptotic_window=1)
    assert index == steps_to_fraction_of_asymptotic(np.array(curve) + 100, asymptotic_window=1)
    assert index == steps_to_fraction_of_asymptotic(np.array(curve) - 100, asymptotic_window=1)


def test_r015_known_progress_and_missing():
    assert steps_to_fraction_of_asymptotic([-1, -1, -1]) == 0
    assert steps_to_fraction_of_asymptotic([1, 1, 1]) == 0
    assert steps_to_fraction_of_asymptotic([-10, -6, 0], fraction=0.9, asymptotic_window=1) == 2
    assert steps_to_fraction_of_asymptotic([10, 6, 0], fraction=0.9, asymptotic_window=1) == 2
    assert np.isnan(steps_to_fraction_of_asymptotic([1, np.nan, 2]))
    assert np.isnan(steps_to_fraction_of_asymptotic([]))


@pytest.mark.parametrize("fraction", [-0.1, 1.1, np.nan])
def test_r015_invalid_fraction(fraction):
    with pytest.raises(ValueError):
        steps_to_fraction_of_asymptotic([0, 1], fraction=fraction)


@pytest.mark.parametrize("x,y,expected,n", [
    ([2, 3, 4], [1, 1, 1], 1, 3),
    ([1, 1, 1], [2, 3, 4], -1, 3),
    ([0, 2, -1], [0, 0, 0], 1/3, 2),
    ([0, 1, -1], [0, 0, 0], 0, 2),
    ([1, 1], [1, 1], 0, 0),
    ([np.nan, 2, 4], [0, 1, 1], 1, 2),
])
def test_r019_signed_rank_effect_and_zeros(x, y, expected, n):
    row = pairwise_wilcoxon({"a": x, "b": y})[0]
    assert row["rank_biserial"] == pytest.approx(expected)
    assert row["n"] == n
    reverse = wilcoxon_signed_rank(y, x)
    assert reverse["rank_biserial"] == pytest.approx(-expected)
    assert reverse["p_value"] == pytest.approx(row["p_value"])
    if n:
        a, b = np.array(x), np.array(y)
        valid = np.isfinite(a) & np.isfinite(b)
        ref = stats.wilcoxon(a[valid], b[valid], zero_method="wilcox", alternative="two-sided")
        assert row["p_value"] == pytest.approx(ref.pvalue)
        assert row["statistic"] == pytest.approx(ref.statistic)


def test_r019_small_real_difference_is_not_allclose_zero():
    result = wilcoxon_signed_rank([1 + 1e-7] * 3, [1] * 3)
    assert result["rank_biserial"] == 1
    assert result["status"] == "ok"


def test_r019_holm_known_family():
    assert holm_correction([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_i13_uses_canonical_project_modules():
    import inspect
    stage = Path(__file__).resolve().parents[2]/'uc3m'
    for function in (kendall_w, consistency_ratio, load_decision_matrix, run_selection_pipeline, wilcoxon_signed_rank):
        Path(inspect.getfile(function)).resolve().relative_to(stage)
