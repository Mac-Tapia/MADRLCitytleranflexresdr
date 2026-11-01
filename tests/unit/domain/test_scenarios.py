from __future__ import annotations

import pytest

from uc3m.domain.objectives import canonical_objective_policies
from uc3m.domain.scenarios import (
    ConstraintPolicy,
    ScenarioCatalog,
    ScenarioDefinition,
    TariffPolicy,
)


POLICIES = canonical_objective_policies()
CONSTRAINTS = ConstraintPolicy(
    policy_id="ev-bess-safe-v1",
    ev_service_enabled=True,
    bess_limits_enabled=True,
)


def _scenario(
    scenario_id: str,
    objective_id: str,
    tariff: TariffPolicy,
    study_kind: str = "weights_only",
) -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=scenario_id,
        objective_policy=POLICIES[objective_id],
        tariff_policy=tariff,
        constraint_policy=CONSTRAINTS,
        study_kind=study_kind,
    )


def test_tariff_changes_scenario_fingerprint_independently_of_weights() -> None:
    flat = TariffPolicy("flat-v1", "flat", 1.0)
    tou = TariffPolicy("tou-v1", "tou", 1.0)

    first = _scenario("E1-flat", "E1", flat, "composite")
    second = _scenario("E1-tou", "E1", tou, "composite")

    assert first.objective_policy.fingerprint() == second.objective_policy.fingerprint()
    assert first.fingerprint() != second.fingerprint()


def test_weights_only_catalog_requires_identical_tariff_and_constraints() -> None:
    flat = TariffPolicy("flat-v1", "flat", 1.0)
    tou = TariffPolicy("tou-v1", "tou", 1.0)

    with pytest.raises(ValueError, match="identical tariff"):
        ScenarioCatalog(
            [
                _scenario("E1", "E1", flat),
                _scenario("E2", "E2", tou),
            ]
        )

    different_constraints = ConstraintPolicy(
        policy_id="other", ev_service_enabled=False, bess_limits_enabled=True
    )
    with pytest.raises(ValueError, match="identical constraints"):
        ScenarioCatalog(
            [
                _scenario("E1", "E1", flat),
                ScenarioDefinition(
                    "E2",
                    POLICIES["E2"],
                    flat,
                    different_constraints,
                    "weights_only",
                ),
            ]
        )


def test_composite_scenarios_are_explicit_and_do_not_claim_weights_only() -> None:
    catalog = ScenarioCatalog(
        [
            _scenario("E1", "E1", TariffPolicy("flat", "flat", 1.0), "composite"),
            _scenario("E2", "E2", TariffPolicy("tou", "tou", 1.2), "composite"),
            _scenario("E3", "E3", TariffPolicy("rtp", "rtp", 0.9), "composite"),
        ]
    )

    assert tuple(catalog) == ("E1", "E2", "E3")
    assert all(item.study_kind == "composite" for item in catalog.values())


@pytest.mark.parametrize("mode", ["invalid", "", "TOU"])
def test_tariff_rejects_unknown_modes(mode: str) -> None:
    with pytest.raises(ValueError, match="mode"):
        TariffPolicy("bad", mode, 1.0)


def test_tariff_rejects_non_positive_multiplier() -> None:
    with pytest.raises(ValueError, match="positive"):
        TariffPolicy("bad", "flat", 0.0)
