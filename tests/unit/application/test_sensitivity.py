from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.eval.run_objective_weight_sensitivity import main
from uc3m.application.sensitivity import ExperimentMatrix, generate_weight_grid
from uc3m.domain.objectives import HierarchyLevels, canonical_objective_policies


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_weight_grid_is_deterministic_unique_and_contains_canonical_policies() -> None:
    first = generate_weight_grid(HierarchyLevels(), step=0.05)
    second = generate_weight_grid(HierarchyLevels(), step=0.05)
    canonical = canonical_objective_policies()

    assert [policy.fingerprint() for policy in first] == [
        policy.fingerprint() for policy in second
    ]
    assert len({policy.fingerprint() for policy in first}) == len(first)
    assert {policy.fingerprint() for policy in canonical.values()} <= {
        policy.fingerprint() for policy in first
    }
    for policy in first:
        assert sum(policy.weights.values()) == pytest.approx(1.0)
        assert min(policy.weights.values()) >= 0.15


def test_experiment_matrix_reports_budget_without_launching_training() -> None:
    policies = generate_weight_grid(HierarchyLevels(), step=0.25)
    matrix = ExperimentMatrix(
        algorithms=("HAPPO", "MASAC"),
        policies=policies,
        seeds=(0, 1, 2),
        timesteps_per_run=1000,
        study_kind="weights_only",
    )

    manifest = matrix.as_manifest()

    assert manifest["study_kind"] == "weights_only"
    assert manifest["run_count"] == 2 * len(policies) * 3
    assert manifest["estimated_environment_steps"] == manifest["run_count"] * 1000
    assert manifest["launch_authorized"] is False


def test_dry_run_cli_persists_reviewable_manifest(tmp_path: Path) -> None:
    output = tmp_path / "sensitivity.json"

    exit_code = main(
        [
            "--dry-run",
            "--config",
            str(
                PROJECT_ROOT
                / "configs"
                / "experiments"
                / "objective_weight_sensitivity.yaml"
            ),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["run_count"] > 0
    assert manifest["launch_authorized"] is False
    assert manifest["study_kind"] == "weights_only"
