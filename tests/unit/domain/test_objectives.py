from __future__ import annotations

from collections import Counter

import numpy as np
import pytest

from uc3m.domain.objectives import (
    HierarchyLevels,
    ObjectiveAxis,
    ObjectivePolicy,
    RewardVector,
    canonical_objective_policies,
)


AXES = (
    ObjectiveAxis.FLEXIBILITY,
    ObjectiveAxis.CO2_EMISSIONS,
    ObjectiveAxis.ENERGY_COST,
)


def test_reward_vector_uses_canonical_axis_order_and_rejects_non_finite() -> None:
    reward = RewardVector(flexibility=1.0, co2_emissions=-2.0, energy_cost=3.5)

    np.testing.assert_array_equal(reward.as_array(), np.array([1.0, -2.0, 3.5]))

    with pytest.raises(ValueError, match="finite"):
        RewardVector(float("nan"), 0.0, 0.0)
    with pytest.raises(ValueError, match="finite"):
        RewardVector(0.0, float("inf"), 0.0)


def test_hierarchy_requires_sum_one_and_strict_primary_majority() -> None:
    levels = HierarchyLevels()

    assert (levels.primary, levels.secondary, levels.residual) == (0.60, 0.25, 0.15)

    with pytest.raises(ValueError, match="sum to 1"):
        HierarchyLevels(primary=0.6, secondary=0.3, residual=0.2)
    with pytest.raises(ValueError, match="strict majority"):
        HierarchyLevels(primary=0.5, secondary=0.3, residual=0.2)


def test_policy_validates_axes_weights_and_scalarizes_in_canonical_order() -> None:
    policy = ObjectivePolicy(
        policy_id="E1",
        weights={
            ObjectiveAxis.ENERGY_COST: 0.25,
            ObjectiveAxis.FLEXIBILITY: 0.60,
            ObjectiveAxis.CO2_EMISSIONS: 0.15,
        },
    )

    assert policy.as_dict()["weights"] == {
        "flexibility": 0.60,
        "co2_emissions": 0.15,
        "energy_cost": 0.25,
    }
    assert policy.scalarize(RewardVector(1.0, 2.0, 4.0)) == pytest.approx(1.9)

    with pytest.raises(ValueError, match="non-negative"):
        ObjectivePolicy(
            policy_id="bad",
            weights={AXES[0]: 0.7, AXES[1]: 0.4, AXES[2]: -0.1},
        )
    with pytest.raises(ValueError, match="exactly the canonical axes"):
        ObjectivePolicy(policy_id="missing", weights={AXES[0]: 1.0})


def test_fingerprint_is_stable_across_mapping_order() -> None:
    forward = ObjectivePolicy(
        "E1", {AXES[0]: 0.60, AXES[1]: 0.15, AXES[2]: 0.25}
    )
    reverse = ObjectivePolicy(
        "E1", {AXES[2]: 0.25, AXES[1]: 0.15, AXES[0]: 0.60}
    )

    assert forward.fingerprint() == reverse.fingerprint()
    assert len(forward.fingerprint()) == 64


def test_canonical_policies_are_cyclically_balanced() -> None:
    policies = canonical_objective_policies()

    assert tuple(policies) == ("E1", "E2", "E3")
    assert policies["E1"].as_dict()["weights"] == {
        "flexibility": 0.60,
        "co2_emissions": 0.15,
        "energy_cost": 0.25,
    }
    assert policies["E2"].as_dict()["weights"] == {
        "flexibility": 0.25,
        "co2_emissions": 0.60,
        "energy_cost": 0.15,
    }
    assert policies["E3"].as_dict()["weights"] == {
        "flexibility": 0.15,
        "co2_emissions": 0.25,
        "energy_cost": 0.60,
    }
    for axis in AXES:
        assert Counter(policy.weights[axis] for policy in policies.values()) == Counter(
            [0.60, 0.25, 0.15]
        )
