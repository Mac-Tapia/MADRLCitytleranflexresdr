"""SPEC-005 FR-005.5: multiseed statistical report of the new campaign.

SYNTHETIC FIXTURES ONLY. Every KPI value below is invented to exercise the
report logic (IQM, bootstrap CI, leader/decision separation, fail-closed
gates). None of them is a training result and none may be cited in the thesis.

The fixture mimics the layout written by the modular Colab campaign:
``<root>/<run_id>/{evidence.json, experiment.json}`` and
``<root>/<run_id>/<E1_s<seed>>/figures/tables/core_kpis.csv``.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Mapping, Sequence

import pytest

from tools.eval import build_campaign_statistical_report as report_tool

SEEDS = (1, 2, 3)
SCENARIO = "E1"

# Synthetic values. peak_average: MATD3 fully separated (lower is better).
# ramping_average: overlapping groups -> HAPPO is the descriptive leader only.
# pv_self_consumption_ratio: identical everywhere -> not testable, tied leader.
SYNTHETIC_KPIS: Dict[str, Dict[str, Sequence[float]]] = {
    "HAPPO": {
        "peak_average": (0.90, 0.92, 0.94),
        "ramping_average": (1.00, 1.20, 1.10),
        "pv_self_consumption_ratio": (0.50, 0.50, 0.50),
        "battery_throughput_total": (10.0, 11.0, 12.0),
    },
    "MATD3": {
        "peak_average": (0.80, 0.81, 0.82),
        "ramping_average": (1.05, 1.15, 1.12),
        "pv_self_consumption_ratio": (0.50, 0.50, 0.50),
        "battery_throughput_total": (9.0, 13.0, 11.0),
    },
}


def _write_campaign_yaml(path: Path, algorithms: Sequence[str], seeds: Sequence[int]) -> Path:
    path.write_text(
        "campaign_id: synthetic_fixture\n"
        f"algorithms: [{', '.join(algorithms)}]\n"
        f"scenarios: [{SCENARIO}]\n"
        f"seeds: [{', '.join(str(s) for s in seeds)}]\n"
        "episodes: 50\n",
        encoding="utf-8",
    )
    return path


def _write_run(
    root: Path,
    algorithm: str,
    seed: int,
    kpis: Mapping[str, float],
    *,
    status: str = "verified",
    completed_episodes: int = 50,
) -> Path:
    run_id = f"{algorithm.lower()}-{SCENARIO.lower()}-s{seed:03d}-synthetic"
    run = root / run_id
    tables = run / f"{SCENARIO}_s{seed}" / "figures" / "tables"
    tables.mkdir(parents=True)
    with (tables / "core_kpis.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kpi", "value"])
        writer.writeheader()
        for name, value in kpis.items():
            writer.writerow({"kpi": name, "value": value})
    (run / "experiment.json").write_text(
        json.dumps({"algorithm": algorithm, "scenario_id": SCENARIO, "seed": seed}), encoding="utf-8"
    )
    (run / "evidence.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": status,
                "completed_episodes": completed_episodes,
                "target_episodes": 50,
            }
        ),
        encoding="utf-8",
    )
    return run


def _synthetic_campaign(root: Path, algorithms: Sequence[str] = ("HAPPO", "MATD3")) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for algorithm in algorithms:
        for index, seed in enumerate(SEEDS):
            kpis = {name: values[index] for name, values in SYNTHETIC_KPIS[algorithm].items()}
            _write_run(root, algorithm, seed, kpis)
    return root


def _comparison(report: dict, kpi: str) -> dict:
    (match,) = [c for c in report["comparisons"] if c["scenario"] == SCENARIO and c["kpi"] == kpi]
    return match


def _treatment(report: dict, algorithm: str, kpi: str) -> dict:
    (match,) = [
        t
        for t in report["treatments"]
        if t["algorithm"] == algorithm and t["scenario"] == SCENARIO and t["kpi"] == kpi
    ]
    return match


@pytest.fixture()
def campaign(tmp_path: Path):
    root = _synthetic_campaign(tmp_path / "synthetic_campaign")
    spec = report_tool.load_campaign_spec(_write_campaign_yaml(tmp_path / "campaign.yaml", ("HAPPO", "MATD3"), SEEDS))
    return root, spec


# --- estimators ---------------------------------------------------------------------------------


def test_iqm_is_the_25_percent_trimmed_mean() -> None:
    assert report_tool.iqm([1, 2, 3, 4, 5, 6, 7, 8]) == pytest.approx(4.5)
    # With three runs a 25 % trim removes int(0.75) = 0 values per tail: IQM equals the mean.
    assert report_tool.iqm([0.90, 0.92, 0.94]) == pytest.approx(0.92)


def test_bootstrap_ci_is_deterministic_and_bounded() -> None:
    values = [0.90, 0.92, 0.94]
    first = report_tool.bootstrap_ci(values, stream="HAPPO|E1|peak_average")
    second = report_tool.bootstrap_ci(values, stream="HAPPO|E1|peak_average")
    assert first == second
    low, high = first
    assert min(values) <= low <= report_tool.iqm(values) <= high <= max(values)
    assert low < high
    assert report_tool.bootstrap_ci([0.5, 0.5, 0.5], stream="x") == (0.5, 0.5)


def test_three_seed_ci_is_only_the_sample_range() -> None:
    # Each extreme resample has probability 1/27 > 2.5 %, so the 95 % percentile
    # interval collapses to [min, max]: a limitation reported, not hidden.
    assert report_tool.bootstrap_ci([0.80, 0.81, 0.82], stream="MATD3|E1|peak_average") == pytest.approx(
        (0.80, 0.82)
    )


# --- report ------------------------------------------------------------------------------------


def test_report_aggregates_each_treatment_over_its_seeds(campaign) -> None:
    root, spec = campaign
    report = report_tool.build_report(root, spec)

    happo = _treatment(report, "HAPPO", "peak_average")
    assert happo["seeds"] == list(SEEDS)
    assert happo["values"] == pytest.approx([0.90, 0.92, 0.94])
    assert happo["n_seeds"] == 3
    assert happo["mean"] == pytest.approx(0.92)
    assert happo["iqm"] == pytest.approx(0.92)
    assert happo["ci_low"] <= happo["iqm"] <= happo["ci_high"]
    assert report["bootstrap"]["seed"] == report_tool.BOOTSTRAP_SEED
    assert report["bootstrap"]["n_resamples"] == report_tool.N_RESAMPLES
    assert report["scientific_acceptance"] is False
    assert report["source_results_root"] == str(root)


def test_report_is_reproducible_and_independent_of_algorithm_order(campaign, tmp_path: Path) -> None:
    root, spec = campaign
    reordered = report_tool.load_campaign_spec(
        _write_campaign_yaml(tmp_path / "reordered.yaml", ("MATD3", "HAPPO"), SEEDS)
    )

    def _cis(report: dict) -> dict:
        return {(t["algorithm"], t["kpi"]): (t["ci_low"], t["ci_high"]) for t in report["treatments"]}

    assert _cis(report_tool.build_report(root, spec)) == _cis(report_tool.build_report(root, spec))
    assert _cis(report_tool.build_report(root, spec)) == _cis(report_tool.build_report(root, reordered))


def test_significant_difference_declares_the_leader_superior(campaign) -> None:
    root, spec = campaign
    comparison = _comparison(report_tool.build_report(root, spec), "peak_average")

    assert comparison["higher_is_better"] is False
    assert comparison["descriptive_leader"]["algorithm"] == "MATD3"
    decision = comparison["inferential_decision"]
    assert decision["omnibus"]["test"] == "kruskal_wallis"
    assert decision["omnibus"]["p_value"] < decision["alpha"]
    assert decision["status"] == "superior"
    assert decision["superior_algorithm"] == "MATD3"


def test_descriptive_leader_without_significance_is_not_superior(campaign) -> None:
    root, spec = campaign
    comparison = _comparison(report_tool.build_report(root, spec), "ramping_average")

    assert comparison["descriptive_leader"]["algorithm"] == "HAPPO"
    decision = comparison["inferential_decision"]
    assert decision["omnibus"]["p_value"] >= decision["alpha"]
    assert decision["status"] == "no_significant_difference"
    assert decision["superior_algorithm"] is None


def test_alpha_controls_the_decision_not_the_leader(campaign) -> None:
    root, spec = campaign
    comparison = _comparison(report_tool.build_report(root, spec, alpha=0.01), "peak_average")

    assert comparison["descriptive_leader"]["algorithm"] == "MATD3"
    assert comparison["inferential_decision"]["status"] == "no_significant_difference"
    assert comparison["inferential_decision"]["superior_algorithm"] is None


def test_identical_values_are_a_tie_and_not_testable(campaign) -> None:
    root, spec = campaign
    comparison = _comparison(report_tool.build_report(root, spec), "pv_self_consumption_ratio")

    assert comparison["higher_is_better"] is True
    assert comparison["descriptive_leader"]["algorithm"] is None
    assert comparison["descriptive_leader"]["tied"] == ["HAPPO", "MATD3"]
    assert comparison["inferential_decision"]["status"] == "not_testable"
    assert comparison["inferential_decision"]["superior_algorithm"] is None


def test_kpis_without_declared_orientation_are_descriptive_only(campaign) -> None:
    root, spec = campaign
    report = report_tool.build_report(root, spec)

    assert _treatment(report, "MATD3", "battery_throughput_total")["orientation"] == "undeclared"
    assert not [c for c in report["comparisons"] if c["kpi"] == "battery_throughput_total"]


def test_main_writes_json_and_csv(campaign, tmp_path: Path) -> None:
    root, _ = campaign
    config = _write_campaign_yaml(tmp_path / "main.yaml", ("HAPPO", "MATD3"), SEEDS)
    out = tmp_path / "report"

    code = report_tool.main(["--results-root", str(root), "--campaign-config", str(config), "--output-dir", str(out)])

    assert code == 0
    payload = json.loads((out / report_tool.REPORT_JSON).read_text(encoding="utf-8"))
    assert {c["kpi"] for c in payload["comparisons"]} >= {"peak_average", "ramping_average"}
    with (out / report_tool.TREATMENTS_CSV).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {"algorithm", "scenario", "kpi", "n_seeds", "mean", "iqm", "ci_low", "ci_high"} <= set(rows[0])
    with (out / report_tool.COMPARISONS_CSV).open(encoding="utf-8") as handle:
        comparisons = list(csv.DictReader(handle))
    assert {"descriptive_leader", "inferential_status", "superior_algorithm", "p_value"} <= set(comparisons[0])


# --- fail closed --------------------------------------------------------------------------------


def _main_fails(root: Path, config: Path, out: Path, capsys) -> str:
    code = report_tool.main(["--results-root", str(root), "--campaign-config", str(config), "--output-dir", str(out)])
    assert code == 2
    assert not out.exists() or not any(out.iterdir())
    return capsys.readouterr().err


def test_missing_declared_algorithm_fails_closed(tmp_path: Path, capsys) -> None:
    root = _synthetic_campaign(tmp_path / "synthetic_campaign", algorithms=("HAPPO",))
    config = _write_campaign_yaml(tmp_path / "campaign.yaml", ("HAPPO", "MATD3"), SEEDS)

    err = _main_fails(root, config, tmp_path / "out", capsys)

    assert "MATD3 E1 seed 1" in err
    assert "missing" in err.lower()


def test_unverified_run_counts_as_missing(tmp_path: Path, capsys) -> None:
    root = _synthetic_campaign(tmp_path / "synthetic_campaign")
    evidence = root / "matd3-e1-s002-synthetic" / "evidence.json"
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["status"] = "partial"
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    config = _write_campaign_yaml(tmp_path / "campaign.yaml", ("HAPPO", "MATD3"), SEEDS)

    err = _main_fails(root, config, tmp_path / "out", capsys)

    assert "MATD3 E1 seed 2 (status=partial)" in err


def test_missing_kpi_table_fails_closed(tmp_path: Path, capsys) -> None:
    root = _synthetic_campaign(tmp_path / "synthetic_campaign")
    (root / "happo-e1-s003-synthetic" / "E1_s3" / "figures" / "tables" / "core_kpis.csv").unlink()
    config = _write_campaign_yaml(tmp_path / "campaign.yaml", ("HAPPO", "MATD3"), SEEDS)

    err = _main_fails(root, config, tmp_path / "out", capsys)

    assert "HAPPO E1 seed 3 (missing figures/tables/core_kpis.csv)" in err


def test_run_short_of_declared_episodes_fails_closed(tmp_path: Path, capsys) -> None:
    root = _synthetic_campaign(tmp_path / "synthetic_campaign")
    evidence = root / "happo-e1-s001-synthetic" / "evidence.json"
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["completed_episodes"] = 8
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    config = _write_campaign_yaml(tmp_path / "campaign.yaml", ("HAPPO", "MATD3"), SEEDS)

    err = _main_fails(root, config, tmp_path / "out", capsys)

    assert "HAPPO E1 seed 1 (completed 8/50 episodes)" in err


def test_fewer_than_two_declared_seeds_fails_closed(tmp_path: Path, capsys) -> None:
    root = _synthetic_campaign(tmp_path / "synthetic_campaign")
    config = _write_campaign_yaml(tmp_path / "campaign.yaml", ("HAPPO", "MATD3"), (1,))

    err = _main_fails(root, config, tmp_path / "out", capsys)

    assert "at least 2 seeds" in err


def test_build_report_raises_on_incomplete_campaign(tmp_path: Path) -> None:
    root = _synthetic_campaign(tmp_path / "synthetic_campaign", algorithms=("HAPPO",))
    spec = report_tool.load_campaign_spec(_write_campaign_yaml(tmp_path / "c.yaml", ("HAPPO", "MATD3"), SEEDS))

    with pytest.raises(report_tool.IncompleteCampaign, match="MATD3 E1 seed 3"):
        report_tool.build_report(root, spec)


@pytest.mark.parametrize('values, expected', [
    ([0.0, 1.0, 100.0], 17.3333333333333),
    ([1.0, 2.0, 3.0, 4.0, 5.0], 3.0),
    ([1.0, 2.0, 3.0, 4.0, 5.0, 60.0], 3.5),
    ([float(v) for v in range(1, 13)], 6.5),
    ([2.0, 2.0, 2.0, 9.0], 2.0),
])
def test_iqm_is_the_canonical_fractional_convention(values, expected):
    # P08/A13: one IQM for the project (fractional weights at the 25 %/75 % cuts).
    from uc3m.application.evaluation.fresh_analysis import iqm as canonical
    assert canonical(values) == pytest.approx(expected, abs=1e-9)
    assert _iqm_under_test(values) == pytest.approx(canonical(values), abs=1e-12)


def _iqm_under_test(values):
    from tools.eval.build_campaign_statistical_report import iqm
    return iqm(values)
