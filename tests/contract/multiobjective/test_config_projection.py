from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from uc3m.application.configuration import (
    load_scenario_catalog,
    project_runtime_config,
)
from uc3m.domain.objectives import canonical_objective_policies


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCENARIO_CONFIG = PROJECT_ROOT / "configs" / "scenarios.yaml"


def test_canonical_yaml_domain_and_runtime_projection_do_not_drift() -> None:
    catalog = load_scenario_catalog(SCENARIO_CONFIG)
    canonical = canonical_objective_policies()

    assert tuple(catalog) == ("E1", "E2", "E3")
    for scenario_id in catalog:
        definition = catalog[scenario_id]
        runtime = project_runtime_config(definition)

        assert definition.objective_policy.fingerprint() == canonical[
            scenario_id
        ].fingerprint()
        assert runtime["scenario"]["fingerprint"] == definition.fingerprint()
        assert runtime["reward"]["policy_fingerprint"] == canonical[
            scenario_id
        ].fingerprint()
        assert runtime["reward"]["axes"] == [
            "flexibility",
            "co2_emissions",
            "energy_cost",
        ]
        assert runtime["reward"]["lambdas"] == pytest.approx(
            [
                canonical[scenario_id].weights[axis]
                for axis in canonical[scenario_id].weights
            ]
        )


def _write_catalog(tmp_path: Path, weights: dict[str, float]) -> Path:
    policy_path = tmp_path / "objective_policies.yaml"
    policy_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "policies": {
                    "E1": {
                        "method": "compensatory_hierarchical_weighted_sum",
                        "weights": weights,
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scenario_path = tmp_path / "scenarios.yaml"
    scenario_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "objective_policies_file": "objective_policies.yaml",
                "tariff_policies": {
                    "baseline": {"mode": "flat", "multiplier": 1.0}
                },
                "constraint_policies": {
                    "safe": {
                        "ev_service_enabled": True,
                        "bess_limits_enabled": True,
                    }
                },
                "scenarios": {
                    "E1": {
                        "objective_policy": "E1",
                        "tariff_policy": "baseline",
                        "constraint_policy": "safe",
                        "study_kind": "weights_only",
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return scenario_path


def test_loader_rejects_missing_axis(tmp_path: Path) -> None:
    scenario_path = _write_catalog(
        tmp_path,
        {"flexibility": 0.60, "co2_emissions": 0.15},
    )

    with pytest.raises(ValueError, match="canonical axes"):
        load_scenario_catalog(scenario_path)


def test_loader_rejects_obsolete_070_canonical_weight(tmp_path: Path) -> None:
    scenario_path = _write_catalog(
        tmp_path,
        {"flexibility": 0.70, "co2_emissions": 0.15, "energy_cost": 0.15},
    )

    with pytest.raises(ValueError, match="canonical policy E1 drift"):
        load_scenario_catalog(scenario_path)
