from __future__ import annotations

import json
from pathlib import Path

import pytest

from uc3m.application.evaluation.results_catalog import (
    AmbiguousCampaign,
    campaign_layout,
    discover_runs,
    resolve_results_root,
)


def _run(root: Path, run_id: str, algorithm: str, scenario: str, seed: int, status: str = "verified") -> Path:
    run = root / run_id
    scenario_dir = run / (scenario if seed == 0 else f"{scenario}_s{seed}")
    (scenario_dir / "data").mkdir(parents=True)
    (scenario_dir / "data" / "results.json").write_text("{}", encoding="utf-8")
    (run / "experiment.json").write_text(
        json.dumps({"algorithm": algorithm, "scenario_id": scenario, "seed": seed}), encoding="utf-8"
    )
    (run / "evidence.json").write_text(
        json.dumps({"run_id": run_id, "status": status, "completed_episodes": 50, "target_episodes": 50}),
        encoding="utf-8",
    )
    return scenario_dir


def test_discovers_verified_runs_from_the_modular_layout(tmp_path: Path) -> None:
    happo = _run(tmp_path, "happo-e1-s000-aaa", "HAPPO", "E1", 0)
    _run(tmp_path, "masac-e2-s001-bbb", "MASAC", "E2", 1)
    _run(tmp_path, "matd3-e3-s000-ccc", "MATD3", "E3", 0, status="partial")

    runs = discover_runs(tmp_path)

    assert [(r.algorithm, r.scenario, r.seed) for r in runs] == [("HAPPO", "E1", 0), ("MASAC", "E2", 1)]
    assert runs[0].scenario_dir == happo
    assert runs[0].completed_episodes == 50


def test_partial_runs_are_listed_only_on_request(tmp_path: Path) -> None:
    _run(tmp_path, "matd3-e3-s000-ccc", "MATD3", "E3", 0, status="partial")

    assert discover_runs(tmp_path) == []
    assert [r.status for r in discover_runs(tmp_path, verified_only=False)] == ["partial"]


def test_campaign_layout_maps_algorithm_and_scenario_to_one_directory(tmp_path: Path) -> None:
    e1 = _run(tmp_path, "happo-e1-s000-aaa", "HAPPO", "E1", 0)
    _run(tmp_path, "happo-e1-s001-ddd", "HAPPO", "E1", 1)

    assert campaign_layout(tmp_path, seed=0) == {("HAPPO", "E1"): e1}


def test_two_verified_runs_for_one_treatment_are_rejected(tmp_path: Path) -> None:
    _run(tmp_path, "happo-e1-s000-aaa", "HAPPO", "E1", 0)
    _run(tmp_path, "happo-e1-s000-zzz", "HAPPO", "E1", 0)

    with pytest.raises(AmbiguousCampaign, match="HAPPO E1 seed 0"):
        campaign_layout(tmp_path, seed=0)


def test_results_root_comes_from_argument_then_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("MADRL_RESULTS_ROOT", raising=False)
    assert resolve_results_root(tmp_path) == tmp_path
    monkeypatch.setenv("MADRL_RESULTS_ROOT", str(tmp_path / "from_env"))
    assert resolve_results_root(None) == tmp_path / "from_env"
    monkeypatch.delenv("MADRL_RESULTS_ROOT")
    assert resolve_results_root(None).as_posix().endswith("outputs/campaign")
