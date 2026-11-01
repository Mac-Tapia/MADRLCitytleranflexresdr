from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from uc3m.application.configuration import load_scenario_catalog
from uc3m.domain.experiments import ExperimentSpec, RunIdentity, RunStatus


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CATALOG = load_scenario_catalog(PROJECT_ROOT / "configs" / "scenarios.yaml")


def _spec() -> ExperimentSpec:
    return ExperimentSpec(
        algorithm="MASAC",
        scenario=CATALOG["E3"],
        seed=7,
        dataset_sha256="a" * 64,
        code_commit="b" * 40,
        submodule_commits={"CityLearn": "c" * 40, "external/MARL": "d" * 40},
        target_episodes=50,
    )


def test_experiment_identity_is_stable_and_timestamp_free() -> None:
    first = _spec()
    second = _spec()

    assert first.fingerprint() == second.fingerprint()
    assert first.as_dict() == second.as_dict()
    assert "timestamp" not in repr(first.as_dict()).lower()
    assert RunIdentity.from_spec(first) == RunIdentity.from_spec(second)


def test_every_scientific_input_changes_experiment_identity() -> None:
    base = _spec()
    variants = (
        replace(base, algorithm="MATD3"),
        replace(base, scenario=CATALOG["E2"]),
        replace(base, seed=8),
        replace(base, dataset_sha256="e" * 64),
        replace(base, code_commit="f" * 40),
        replace(base, submodule_commits={"CityLearn": "0" * 40}),
        replace(base, target_episodes=51),
    )

    assert all(variant.fingerprint() != base.fingerprint() for variant in variants)


def test_run_identity_and_status_are_explicit() -> None:
    identity = RunIdentity.from_spec(_spec())

    assert identity.run_id.startswith("masac-e3-s007-")
    assert identity.experiment_fingerprint == _spec().fingerprint()
    assert {status.value for status in RunStatus} == {
        "planned",
        "running",
        "partial",
        "verified",
        "blocked",
    }
