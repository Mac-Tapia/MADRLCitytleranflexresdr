"""Evaluation tools locate results through the modular campaign catalog.

The fixture writes the layout produced by ``uc3m.application.training.colab``:
``<root>/<run_id>/{evidence.json, experiment.json}`` and
``<root>/<run_id>/<E1|E1_s<seed>>/{data, figures/tables}``. All numbers are
fixture values for path resolution only; they are not thesis results.
"""
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[3]
INVENTORY = REPO / "data" / "audits" / "evaluation_tools_inventory.json"
ALGORITHMS = ("HAPPO", "MAAC", "MASAC", "MATD3")
SCENARIOS = ("E1", "E2", "E3")
LEGACY_PATTERNS = (
    "_drive_madrl",
    "full_data",
    "madrl_v3_20260627",
    "citylearn_v3_madrl_full_20260615",
    "thesis_objective_evidence",
    "modular_smoke",
)
BUILDINGS = [f"Building_{index}" for index in range(1, 18)]
PRIMARY_BUILDING_KPIS = (
    "building_emissions_total_baseline_kgco2",
    "building_emissions_total_control_kgco2",
    "building_cost_total_baseline_eur",
    "building_cost_total_control_eur",
)


def _write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _axis_kpi(value: float, baseline: float) -> Dict[str, object]:
    return {
        "value": float(value),
        "comparison": {"baseline": baseline, "available": True, "improved_vs_baseline": bool(value < baseline)},
        "trace": {"lower_is_better": True, "source": "fixture", "note": "fixture"},
    }


def _treatment(
    root: Path,
    algorithm: str,
    scenario: str,
    seed: int,
    rng: np.random.Generator,
    status: str = "verified",
) -> Tuple[str, Path]:
    run_id = f"{algorithm.lower()}-{scenario.lower()}-s{seed:03d}-fixture"
    run = root / run_id
    scenario_dir = run / (scenario if seed == 0 else f"{scenario}_s{seed}")
    data = scenario_dir / "data"
    tables = scenario_dir / "figures" / "tables"
    data.mkdir(parents=True)
    tables.mkdir(parents=True)
    (run / "experiment.json").write_text(
        json.dumps({"algorithm": algorithm, "scenario_id": scenario, "seed": seed}), encoding="utf-8"
    )
    (run / "evidence.json").write_text(
        json.dumps({"run_id": run_id, "status": status, "completed_episodes": 50, "target_episodes": 50}),
        encoding="utf-8",
    )

    flex = rng.uniform(0.8, 1.2, size=3)
    co2_base, cost_base = 1000.0, 500.0
    co2_control = co2_base * rng.uniform(0.9, 1.1)
    cost_control = cost_base * rng.uniform(0.9, 1.1)
    all_values = {
        "peak_average": flex[0],
        "ramping_average": flex[1],
        "one_minus_load_factor_average": flex[2],
        "carbon_emissions": co2_control / co2_base,
        "carbon_emissions_baseline": co2_base,
        "carbon_emissions_control": co2_control,
        "carbon_emissions_delta": co2_control - co2_base,
        "electricity_cost": cost_control / cost_base,
        "electricity_cost_baseline": cost_base,
        "electricity_cost_control": cost_control,
        "electricity_cost_delta": cost_control - cost_base,
        "reward_mean": float(rng.uniform(-1.0, 0.0)),
    }
    results = {
        "algorithm": algorithm,
        "episodes_recorded": 50,
        "timeseries_rows": 2,
        "trace_rows": 2,
        "episode_summaries": [
            {
                "episode": episode,
                "steps": 8760,
                "reward_mean_average": float(rng.normal(-0.5, 0.05)),
                "reward_sum_total": float(rng.normal(-100.0, 5.0)),
            }
            for episode in range(50)
        ],
        "citylearn_v3_report": {
            "all_values": all_values,
            "objective_axis_kpis": {
                "OE1": {"kpis": {"peak_average": _axis_kpi(flex[0], 1.0)}},
                "OE2": {"kpis": {"carbon_emissions_control": _axis_kpi(co2_control, co2_base)}},
                "OE3": {"kpis": {"electricity_cost_control": _axis_kpi(cost_control, cost_base)}},
            },
        },
    }
    (data / "results.json").write_text(json.dumps(results), encoding="utf-8")

    building_rows = []
    for name in BUILDINGS:
        for kpi in PRIMARY_BUILDING_KPIS:
            base = 100.0 if "baseline" in kpi else 100.0 * rng.uniform(0.8, 1.2)
            building_rows.append({"name": name, "cost_function": kpi, "value": base})
        for index in range(75 - len(PRIMARY_BUILDING_KPIS)):
            building_rows.append({"name": name, "cost_function": f"fixture_kpi_{index}", "value": rng.uniform()})
    _write_csv(data / "building_kpis.csv", building_rows)
    _write_csv(
        data / "building_behavior_summary.csv",
        (
            {
                "agent": name,
                "grid_role_control": "importer",
                "grid_import_max": rng.uniform(1, 2),
                "grid_export_max": rng.uniform(0, 1),
                "pv_self_consumption_ratio": rng.uniform(0, 1),
                "carbon_emissions_delta_kgco2": rng.normal(),
                "electricity_cost_delta_eur": rng.normal(),
            }
            for name in BUILDINGS
        ),
    )
    _write_csv(data / "timeseries.csv", [{"step": 0, "reward": 0.0}, {"step": 1, "reward": 0.1}])
    _write_csv(data / "trace.csv", [{"step": 0, "agent": "Building_1"}, {"step": 1, "agent": "Building_1"}])
    _write_csv(
        tables / "core_kpis.csv",
        (
            {"kpi": kpi, "value": all_values[kpi]}
            for kpi in (
                "peak_average",
                "ramping_average",
                "one_minus_load_factor_average",
                "carbon_emissions_delta",
                "electricity_cost_delta",
            )
        ),
    )
    _write_csv(tables / "episode_summary.csv", results["episode_summaries"])
    _write_csv(
        data / "building_observation_action_schema.csv",
        (
            {"agent": name, "variable_type": kind, "variable_name": variable}
            for name in BUILDINGS
            for kind, variable in (("action", "electrical_storage"), ("observation", "hour"))
        ),
    )
    return run_id, scenario_dir


def _campaign(root: Path, *, skip=(), seeds=(0,), partial=()) -> Dict[Tuple[str, str, int], str]:
    rng = np.random.default_rng(7)
    run_ids = {}
    for seed in seeds:
        for algorithm in ALGORITHMS:
            for scenario in SCENARIOS:
                if (algorithm, scenario) in skip:
                    continue
                status = "partial" if (algorithm, scenario) in partial else "verified"
                run_id, _ = _treatment(root, algorithm, scenario, seed, rng, status=status)
                run_ids[(algorithm, scenario, seed)] = run_id
    return run_ids


# --- run_complete_drive_kpi_objective_analysis -------------------------------------------------


def test_complete_analysis_reads_every_treatment_from_the_catalog(tmp_path: Path) -> None:
    from tools.eval import run_complete_drive_kpi_objective_analysis as tool

    root = tmp_path / "campaign"
    run_ids = _campaign(root)
    out = tmp_path / "analysis"

    assert tool.main(["--results-root", str(root), "--output-dir", str(out)]) == 0

    audit = json.loads((out / "complete_quantitative_audit.json").read_text(encoding="utf-8"))
    assert audit["source_root"] == str(root)
    assert audit["coverage"]["treatments"] == 12
    assert audit["coverage"]["episode_rows_reconstructed"] == 600
    assert audit["coverage"]["building_kpi_values"] == 12 * 1275
    with (out / "run_coverage_quantitative.csv").open(encoding="utf-8-sig") as handle:
        coverage = list(csv.DictReader(handle))
    assert {(row["algorithm"], row["scenario"]): row["run_id"] for row in coverage} == {
        (algorithm, scenario): run_id for (algorithm, scenario, _), run_id in run_ids.items()
    }
    assert all(row["source_dir"].startswith(str(root)) for row in coverage)


def test_complete_analysis_uses_the_environment_results_root(tmp_path: Path, monkeypatch) -> None:
    from tools.eval import run_complete_drive_kpi_objective_analysis as tool

    root = tmp_path / "campaign"
    _campaign(root)
    monkeypatch.setenv("MADRL_RESULTS_ROOT", str(root))
    out = tmp_path / "analysis"

    assert tool.main(["--output-dir", str(out)]) == 0
    assert json.loads((out / "complete_quantitative_audit.json").read_text(encoding="utf-8"))[
        "source_root"
    ] == str(root)


def test_complete_analysis_names_missing_and_unverified_treatments(tmp_path: Path, capsys) -> None:
    from tools.eval import run_complete_drive_kpi_objective_analysis as tool

    root = tmp_path / "campaign"
    _campaign(root, skip={("MAAC", "E3")}, partial={("HAPPO", "E1")})
    out = tmp_path / "analysis"

    assert tool.main(["--results-root", str(root), "--output-dir", str(out)]) == 2

    err = capsys.readouterr().err
    assert "MAAC E3" in err and "HAPPO E1" in err
    assert not (out / "complete_quantitative_audit.json").exists()


# --- aggregate_colab_drive_kpis ----------------------------------------------------------------


def test_aggregate_reads_core_kpis_and_results_from_the_catalog(tmp_path: Path) -> None:
    from tools.eval import aggregate_colab_drive_kpis as tool

    root = tmp_path / "campaign"
    run_ids = _campaign(root)
    out = tmp_path / "resumen"

    assert tool.main(["--results-root", str(root), "--output-dir", str(out)]) == 0

    report = json.loads((out / "best_madrl_report.json").read_text(encoding="utf-8"))
    assert report["results_root"] == str(root)
    assert set(report["kpis_primarios"]["flex_composite_e1"]) == set(ALGORITHMS)
    assert {item["algorithm"] for item in report["ranking"]} == set(ALGORITHMS)
    assert all(item["episodes_e1"] == 50 for item in report["ranking"])
    assert report["run_ids"]["MATD3/E2"] == run_ids[("MATD3", "E2", 0)]
    with (out / "comparison_metrics_colab.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 12
    assert {row["run_id"] for row in rows} == set(run_ids.values())

    expected_flex = json.loads(
        (root / run_ids[("HAPPO", "E1", 0)] / "E1" / "data" / "results.json").read_text(encoding="utf-8")
    )["citylearn_v3_report"]["all_values"]
    assert report["kpis_primarios"]["flex_composite_e1"]["HAPPO"] == pytest.approx(
        (
            expected_flex["peak_average"]
            + expected_flex["ramping_average"]
            + expected_flex["one_minus_load_factor_average"]
        )
        / 3.0
    )


def test_aggregate_reports_missing_treatments_without_writing_a_ranking(tmp_path: Path, capsys) -> None:
    from tools.eval import aggregate_colab_drive_kpis as tool

    root = tmp_path / "campaign"
    _campaign(root, skip={("HAPPO", "E2")})
    out = tmp_path / "resumen"

    assert tool.main(["--results-root", str(root), "--output-dir", str(out)]) == 2

    assert "HAPPO E2" in capsys.readouterr().err
    assert not (out / "best_madrl_report.json").exists()


# --- analyze_colab_drive_multiobjective_buildings ----------------------------------------------


def test_multiobjective_tables_come_from_catalog_run_directories(tmp_path: Path) -> None:
    from tools.eval import analyze_colab_drive_multiobjective_buildings as tool

    root = tmp_path / "campaign"
    run_ids = _campaign(root)
    layout = tool.locate_treatments(root)

    district, building, missing = tool.collect_tables([], layout)

    assert missing == []
    assert {(row["algorithm"], row["scenario"]): row["run_id"] for row in district} == {
        (algorithm, scenario): run_ids[(algorithm, scenario, 0)]
        for algorithm in tool.ALGOS
        for scenario in SCENARIOS
    }
    assert len(building) == len(tool.ALGOS) * len(SCENARIOS) * len(BUILDINGS)


def test_multiobjective_reports_missing_treatments(tmp_path: Path, capsys) -> None:
    from tools.eval import analyze_colab_drive_multiobjective_buildings as tool

    root = tmp_path / "campaign"
    _campaign(root, skip={("MASAC", "E2")})

    assert tool.main(["--results-root", str(root), "--output-dir", str(tmp_path / "mo")]) == 2
    assert "MASAC E2" in capsys.readouterr().err
    assert not (tmp_path / "mo").exists()


# --- run_madrl_nonparametric_battery -----------------------------------------------------------


def test_battery_collects_one_value_per_seed_through_the_catalog(tmp_path: Path) -> None:
    from scripts.run_madrl_nonparametric_battery import load_oe_groups_from_results_root

    root = tmp_path / "campaign"
    _campaign(root, seeds=(0, 1))

    groups, meta = load_oe_groups_from_results_root(root, seeds=range(3), expected_n_seeds=3)

    assert {algo: len(values) for algo, values in groups["OE.2"].items()} == {a: 2 for a in ALGORITHMS}
    assert "MATD3/E2/seed=2" in meta["missing"]
    assert meta["source_results_root"] == str(root)


def test_battery_without_results_fails_instead_of_using_illustrative_values(tmp_path: Path, capsys) -> None:
    from scripts.run_madrl_nonparametric_battery import main

    empty = tmp_path / "empty"
    empty.mkdir()

    code = main(["--results-root", str(empty), "--n-seeds", "2", "--output-dir", str(tmp_path / "out")])

    assert code == 2
    assert "no verified" in capsys.readouterr().err.lower()
    assert not (tmp_path / "out" / "nonparametric_battery.json").exists()


# --- uc3m.multicriteria.artifacts --------------------------------------------------------------


def test_multicriteria_reads_episode_curves_through_the_catalog(tmp_path: Path) -> None:
    from uc3m.multicriteria.artifacts import load_episode_reward_series, resolve_run_dir

    root = tmp_path / "campaign"
    _campaign(root)

    assert resolve_run_dir(run_dir=root) == root
    series = load_episode_reward_series(root, scenario="E1")
    assert set(series) == set(ALGORITHMS)
    assert all(len(values) == 50 for values in series.values())


def test_multicriteria_real_only_matrix_reads_campaign_summaries(tmp_path: Path) -> None:
    from uc3m.multicriteria.artifacts import load_decision_matrix

    root = tmp_path / "campaign"
    _campaign(root)
    _write_csv(
        root / "resumen_comparativo" / "multiobjetivo" / "district_objectives_by_algorithm.csv",
        (
            {
                "algorithm": algorithm,
                "scenario": "E1",
                "electricity_cost_delta_eur": 10.0 + index,
                "carbon_emissions_delta_kg": -5.0 - index,
                "flex_composite": 0.9 + index / 100.0,
            }
            for index, algorithm in enumerate(ALGORITHMS)
        ),
    )

    loaded = load_decision_matrix(run_dir=root, allow_illustrative_fill=False)

    assert set(loaded["decision_matrix"]) == set(ALGORITHMS)
    assert loaded["extras"]["run_dir"] == str(root)
    assert all("illustrative" not in str(v) for p in loaded["provenance"].values() for v in p.values())


def test_multicriteria_default_root_without_verified_runs_is_not_a_run(tmp_path: Path, monkeypatch) -> None:
    from uc3m.multicriteria.artifacts import resolve_run_dir

    monkeypatch.delenv("MADRL_RESULTS_ROOT", raising=False)
    (tmp_path / "outputs" / "campaign").mkdir(parents=True)

    assert resolve_run_dir(repo=tmp_path) is None


# --- static guard ------------------------------------------------------------------------------


def _inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_inventory_classifies_every_listed_file() -> None:
    inventory = _inventory()
    assert inventory["schema_version"] == "1.0"
    allowed = {"adapted", "obsolete_old_campaign", "needs_owner_decision"}
    for entry in inventory["files"]:
        assert entry["classification"] in allowed, entry
        assert (REPO / entry["path"]).is_file(), entry["path"]
        assert entry.get("reason") or entry.get("locates_data_via"), entry
    counts = Counter(entry["classification"] for entry in inventory["files"])
    assert inventory["counts"] == {"total": len(inventory["files"]), **{key: counts[key] for key in allowed}}


def test_inventory_lists_every_file_still_referencing_the_retired_campaign() -> None:
    tracked = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "--", "tools", "scripts", "uc3m"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    referencing = {
        path
        for path in tracked
        if (REPO / path).is_file()
        and any(pattern in (REPO / path).read_text(encoding="utf-8", errors="ignore") for pattern in LEGACY_PATTERNS)
    }
    listed = {entry["path"] for entry in _inventory()["files"]}
    assert referencing - listed == set()


def test_adapted_tools_no_longer_reference_the_retired_campaign() -> None:
    adapted = [entry["path"] for entry in _inventory()["files"] if entry["classification"] == "adapted"]
    assert {
        "tools/eval/run_complete_drive_kpi_objective_analysis.py",
        "tools/eval/aggregate_colab_drive_kpis.py",
    } <= set(adapted)
    offenders = {
        path: [pattern for pattern in LEGACY_PATTERNS if pattern in (REPO / path).read_text(encoding="utf-8")]
        for path in adapted
    }
    assert {path: hits for path, hits in offenders.items() if hits} == {}
    for path in adapted:
        assert "results_catalog" in (REPO / path).read_text(encoding="utf-8"), path
