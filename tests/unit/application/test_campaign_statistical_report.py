"""SPEC-005 FR-005.5: the leader/decision separation of the report, over the single statistics engine.

SYNTHETIC VALUES ONLY: they are invented to exercise the projection and none may be cited in the thesis.
The statistics are the output of ``fresh_analysis.analyze_campaign``; only the seed values are synthetic.
The path from real attempts to the report is covered in tests/fresh_training/test_fresh_statistical_report.py.
"""
from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import numpy as np
import pytest

from tools.eval import build_campaign_statistical_report as report_tool
from uc3m.application import pipeline
from uc3m.application.evaluation import fresh_analysis as fa
from uc3m.application.evaluation.model_selection import select_best_model

AXES = (("E1", "flexibility"), ("E2", "co2_emissions"), ("E3", "energy_cost"))
ALGORITHMS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SEEDS = tuple(range(1001, 1013))
PROTOCOL = dataclasses.replace(fa.FrozenProtocol.default(), endpoints=AXES, seeds=SEEDS, resamples=200,
                               confirmatory_endpoints=AXES, not_applicable_endpoints=())
SEPARATED = {"HAPPO": 0.1, "MASAC": 0.2, "MATD3": 0.3, "MAAC": 0.4}
NOISE = np.linspace(-0.01, 0.01, len(SEEDS))


def _table(levels_by_axis):
    rows = []
    for (scenario, endpoint), levels in zip(AXES, levels_by_axis):
        for algorithm in ALGORITHMS:
            for index, seed in enumerate(SEEDS):
                level = levels[algorithm]
                value = level[index] if isinstance(level, (list, tuple)) else level + float(NOISE[index])
                rows.append({"campaign_id": "fresh_x_v1", "algorithm": algorithm, "scenario": scenario, "seed": seed,
                             "split": PROTOCOL.split, "endpoint": endpoint, "value": float(value),
                             "kpi_report_sha256": "0"*64})
    return fa.SeedTable.from_rows(rows)


def _analysis(levels_by_axis):
    table = _table(levels_by_axis)
    return table, fa.analyze_campaign(table, PROTOCOL).as_dict()


def _comparisons(levels_by_axis):
    _, report = _analysis(levels_by_axis)
    return {row["scenario"]: row for row in report_tool.comparison_rows(report, ALGORITHMS, PROTOCOL.alpha)}


def test_a_leader_is_superior_only_with_the_omnibus_and_every_pair_significant():
    row = _comparisons([SEPARATED]*3)["E1"]
    assert row["descriptive_leader"]["algorithm"] == "MAAC"
    decision = row["inferential_decision"]
    assert decision["omnibus"]["test"] == "friedman" and decision["omnibus"]["p_holm"] < decision["alpha"]
    assert decision["status"] == "superior" and decision["superior_algorithm"] == "MAAC"


def test_a_descriptive_leader_without_significance_is_not_superior():
    # Seed-to-seed swings are larger than the difference in level: Friedman cannot separate them.
    rng = np.random.default_rng(11)
    overlapping = {name: list(rng.normal(0.2, 0.2, len(SEEDS))) for name in ALGORITHMS}
    row = _comparisons([overlapping]*3)["E1"]
    decision = row["inferential_decision"]
    assert row["descriptive_leader"]["algorithm"] in ALGORITHMS
    assert decision["omnibus"]["p_holm"] >= decision["alpha"]
    assert decision["status"] == "no_significant_difference" and decision["superior_algorithm"] is None


def test_identical_values_are_a_tie_without_a_leader_or_a_decision():
    row = _comparisons([{name: [0.5]*len(SEEDS) for name in ALGORITHMS}]*3)["E1"]
    assert row["descriptive_leader"]["algorithm"] is None
    assert row["descriptive_leader"]["tied"] == sorted(ALGORITHMS)
    assert row["inferential_decision"]["superior_algorithm"] is None


def test_a_significant_omnibus_without_a_clear_top_pair_names_nobody():
    # MAAC and MATD3 alternate at the top, far above the rest: the omnibus detects a difference,
    # the pair at the top does not separate.
    high = [0.4 + (0.01 if i % 2 else -0.01)*(i + 1)/10 for i in range(len(SEEDS))]
    other = [0.4 - (0.01 if i % 2 else -0.01)*(i + 1)/10 for i in range(len(SEEDS))]
    levels = {"HAPPO": 0.1, "MASAC": 0.2, "MATD3": other, "MAAC": high}
    decision = _comparisons([levels]*3)["E1"]["inferential_decision"]
    assert decision["omnibus"]["p_holm"] < decision["alpha"]
    assert decision["status"] == "omnibus_significant_no_unique_superior"
    assert decision["superior_algorithm"] is None


def test_treatment_rows_copy_the_engine_and_pair_each_value_with_its_seed():
    table, report = _analysis([SEPARATED]*3)
    rows = report_tool.treatment_rows([dict(r) for r in table.rows], report)
    (row,) = [r for r in rows if r["algorithm"] == "MAAC" and r["scenario"] == "E2"]
    (source,) = [s for s in report["seed_statistics"] if s["algorithm"] == "MAAC" and s["scenario"] == "E2"]
    assert row["seeds"] == list(SEEDS) and row["values"] == pytest.approx(list(0.4 + NOISE))
    assert (row["mean"], row["iqm"]) == (source["mean"], source["iqm"])
    assert [row["ci_low"], row["ci_high"]] == list(source["ci95_mean"])


def test_the_tool_computes_no_statistic_of_its_own():
    source = Path(report_tool.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    forbidden = {"numpy", "scipy", "scipy.stats", "uc3m.multicriteria.stats_tests",
                 "uc3m.application.evaluation.fresh_analysis"}
    assert not imported & forbidden
    assert "kruskal" not in source.lower() and "uc3m.application.evaluation.results_catalog" in imported


@pytest.mark.parametrize('values, expected', [
    ([0.0, 1.0, 100.0], 17.3333333333333),
    ([1.0, 2.0, 3.0, 4.0, 5.0], 3.0),
    ([1.0, 2.0, 3.0, 4.0, 5.0, 60.0], 3.5),
    ([float(v) for v in range(1, 13)], 6.5),
    ([2.0, 2.0, 2.0, 9.0], 2.0),
])
def test_iqm_is_the_canonical_fractional_convention(values, expected):
    # P08/A13: one IQM for the project (fractional weights at the 25 %/75 % cuts).
    assert fa.iqm(values) == pytest.approx(expected, abs=1e-9)


# --- FR-005.6: the production input of select_best_model --------------------------------------------


def _selection(levels_by_axis):
    table, report = _analysis(levels_by_axis)
    return select_best_model(pipeline.selection_evaluation(table, report, PROTOCOL))


def test_a_winner_needs_all_three_axes():
    result = _selection([SEPARATED]*3)
    assert result["descriptive_candidate"] == "MAAC"
    assert result["inferential_winner"] == "MAAC" and result["inferential_status"] == "detected"


def test_winning_one_axis_is_not_a_universal_winner():
    reversed_levels = {"HAPPO": 0.4, "MASAC": 0.3, "MATD3": 0.2, "MAAC": 0.1}
    result = _selection([SEPARATED, SEPARATED, reversed_levels])
    assert result["inferential_winner"] is None and result["inferential_status"] == "no_inferential_winner"
    assert result["selection_kind"] == "descriptive"


def test_the_hypervolume_is_taken_per_seed_over_the_three_axes():
    table, report = _analysis([SEPARATED]*3)
    evaluation = pipeline.selection_evaluation(table, report, PROTOCOL)
    row = evaluation["algorithms"]["HAPPO"]
    expected = [(1.1 + float(noise))**3 for noise in NOISE]
    assert list(row["hypervolume_by_seed"].values()) == pytest.approx(expected)
    assert row["mean_hypervolume"] == pytest.approx(np.mean(expected))
    assert row["variance_hypervolume"] == pytest.approx(np.var(expected, ddof=1))
    assert row["n_seeds"] == len(SEEDS) and row["saturated_axes"] == {}


def test_a_campaign_without_all_three_axes_is_incomplete_for_selection():
    table, report = _analysis([SEPARATED]*3)
    only_e1 = dataclasses.replace(PROTOCOL, confirmatory_endpoints=AXES[:1])
    with pytest.raises(ValueError, match="incomplete"):
        select_best_model(pipeline.selection_evaluation(table, report, only_e1))
