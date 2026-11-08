"""SPEC-002 FR-002.5 — per-term reward telemetry.

The scalar reward is decomposed into the weighted contribution of each simplex
axis (flexibility, CO2, cost) plus each EV/BESS service/constraint term, which
is reported separately and never counted inside the simplex. The decomposition
is telemetry only: it must reproduce the reward that the current CityLearn v3
reward function computes, without changing weights or values.
"""

from __future__ import annotations

import copy
import math

import pytest

from citylearn.v3.reward import CityLearnV3MADRLRewardFunction
from uc3m.domain.objectives import ObjectiveAxis, canonical_objective_policies
from uc3m.reward.term_telemetry import (
    SERVICE_TERMS,
    SIMPLEX_AXES,
    RewardTermDecomposition,
    decompose_citylearn_v3_breakdown,
    decompose_reward_function,
    verify_reward_decomposition,
)

SCENARIOS = ("E1", "E2", "E3")
ATOL = 1e-12

# CityLearn key -> canonical domain axis.
AXIS_KEY_TO_DOMAIN = {
    "flex": ObjectiveAxis.FLEXIBILITY,
    "carbon": ObjectiveAxis.CO2_EMISSIONS,
    "cost": ObjectiveAxis.ENERGY_COST,
}

EXPECTED_WEIGHTS = {
    "E1": {"flex": 0.60, "carbon": 0.15, "cost": 0.25},
    "E2": {"flex": 0.25, "carbon": 0.60, "cost": 0.15},
    "E3": {"flex": 0.15, "carbon": 0.25, "cost": 0.60},
}


def _ev_charger(soc: float, required: float, hours: float, charged: float) -> dict:
    return {
        "connected": True,
        "battery_soc": soc,
        "previous_battery_soc": max(soc - 0.05, 0.0),
        "battery_capacity": 40.0,
        "min_capacity": 4.0,
        "last_charged_kwh": charged,
        "required_soc": required,
        "hours_until_departure": hours,
        "max_charging_power": 7.0,
        "max_discharging_power": 7.0,
    }


def _observations(step: int) -> list[dict]:
    """Three buildings: import with EV, export with BESS, plain import."""
    shift = 0.1 * step
    return [
        {
            "net_electricity_consumption": 18.0 + 4.0 * step,
            "electricity_pricing": 0.28,
            "carbon_intensity": 0.55,
            "electrical_storage_soc": 0.40 + shift,
            "electric_vehicles_chargers_dict": {
                "c1": _ev_charger(0.30, 0.80, 2.0, 0.0),
            },
        },
        {
            "net_electricity_consumption": -6.0 + step,
            "electricity_pricing": 0.12,
            "carbon_intensity": 0.40,
            "electrical_storage_soc": 0.85 - 2.0 * shift,
            "dhw_storage_soc": 0.50,
        },
        {
            "net_electricity_consumption": 9.0,
            "electricity_pricing": 0.20,
            "carbon_intensity": 0.50,
        },
    ]


def _run_two_steps(scenario: str, central_agent: bool = False):
    reward_function = CityLearnV3MADRLRewardFunction(
        {"central_agent": central_agent}, algorithm="MATD3", scenario=scenario
    )
    reward_function.calculate(_observations(0))
    rewards = reward_function.calculate(_observations(1))
    return reward_function, rewards


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_term_sum_equals_existing_reward_per_agent(scenario):
    reward_function, rewards = _run_two_steps(scenario)
    decompositions = decompose_reward_function(reward_function)

    assert len(decompositions) == len(rewards) == 3
    for decomposition, reward in zip(decompositions, rewards):
        assert isinstance(decomposition, RewardTermDecomposition)
        terms = list(decomposition.axis_contributions.values()) + list(
            decomposition.service_terms.values()
        )
        assert math.isclose(sum(terms), decomposition.total, abs_tol=ATOL)
        assert math.isclose(decomposition.total, reward, abs_tol=ATOL)
    verify_reward_decomposition(decompositions, rewards, atol=ATOL)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_term_sum_equals_existing_reward_central_agent(scenario):
    reward_function, rewards = _run_two_steps(scenario, central_agent=True)
    decompositions = decompose_reward_function(reward_function)

    assert len(rewards) == len(decompositions) == 1
    assert math.isclose(decompositions[0].total, rewards[0], abs_tol=ATOL)
    verify_reward_decomposition(decompositions, rewards, atol=ATOL)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_ev_bess_are_separate_terms_outside_the_simplex(scenario):
    reward_function, _ = _run_two_steps(scenario)
    decompositions = decompose_reward_function(reward_function)

    assert SIMPLEX_AXES == ("flex", "carbon", "cost")
    assert set(SERVICE_TERMS) == {"ev", "bess_cycle", "comfort"}
    assert not set(SIMPLEX_AXES) & set(SERVICE_TERMS)

    for decomposition in decompositions:
        assert tuple(decomposition.axis_contributions) == SIMPLEX_AXES
        assert tuple(decomposition.service_terms) == SERVICE_TERMS
        assert tuple(decomposition.axis_weights) == SIMPLEX_AXES
        assert math.isclose(
            sum(decomposition.axis_weights.values()), 1.0, abs_tol=1e-12
        )

    # Fixture must exercise both service terms, otherwise the check is vacuous.
    building_ev = decompositions[0].service_terms["ev"]
    building_bess = decompositions[1].service_terms["bess_cycle"]
    breakdown = reward_function._last_component_breakdown["components"]
    assert breakdown[0]["ev"] != 0.0
    assert breakdown[1]["bess_cycle"] != 0.0
    assert building_ev != 0.0
    assert building_bess != 0.0


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_simplex_weights_are_unchanged_canonical_policy(scenario):
    reward_function, _ = _run_two_steps(scenario)
    decompositions = decompose_reward_function(reward_function)
    policy = canonical_objective_policies()[scenario]

    for decomposition in decompositions:
        for key, weight in decomposition.axis_weights.items():
            assert weight == pytest.approx(EXPECTED_WEIGHTS[scenario][key], abs=1e-12)
            assert weight == pytest.approx(
                policy.weights[AXIS_KEY_TO_DOMAIN[key]], abs=1e-12
            )
    assert dict(reward_function.axis_weights) == pytest.approx(
        EXPECTED_WEIGHTS[scenario]
    )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_decomposition_does_not_change_reward_or_state(scenario):
    instrumented, rewards = _run_two_steps(scenario)
    snapshot = copy.deepcopy(instrumented._last_component_breakdown)
    snapshot_socs = dict(instrumented._last_bess_socs)
    snapshot_import = instrumented._last_district_power

    decompose_reward_function(instrumented)
    decompose_reward_function(instrumented)

    assert instrumented._last_component_breakdown == snapshot
    assert instrumented._last_bess_socs == snapshot_socs
    assert instrumented._last_district_power == snapshot_import

    # A reference run without any telemetry call gives identical rewards.
    _, reference_rewards = _run_two_steps(scenario)
    assert rewards == reference_rewards

    # Next step after decomposition is identical to the untouched reference.
    reference, _ = _run_two_steps(scenario)
    assert instrumented.calculate(_observations(2)) == reference.calculate(
        _observations(2)
    )


def test_hand_computed_team_mixing_decomposition():
    breakdown = {
        "axis_weights": {"flex": 0.60, "carbon": 0.15, "cost": 0.25},
        "components": [
            {
                "weighted_flex": -0.30,
                "weighted_carbon": -0.06,
                "weighted_cost": -0.10,
                "ev": -0.05,
                "bess_cycle": 0.0,
            },
            {
                "weighted_flex": -0.10,
                "weighted_carbon": 0.02,
                "weighted_cost": -0.04,
                "ev": 0.0,
                "bess_cycle": -0.08,
            },
        ],
    }
    profile = {"reward_scale": 2.0, "team_reward_ratio": 0.70}
    decompositions = decompose_citylearn_v3_breakdown(breakdown, profile=profile)

    local = [2.0 * (-0.30 - 0.06 - 0.10 - 0.05), 2.0 * (-0.10 + 0.02 - 0.04 - 0.08)]
    team = sum(local) / 2.0
    expected = [0.3 * value + 0.7 * team for value in local]
    for decomposition, value in zip(decompositions, expected):
        assert decomposition.total == pytest.approx(value, abs=1e-12)

    ev_mixed = 0.3 * (2.0 * -0.05) + 0.7 * (2.0 * -0.05 + 0.0) / 2.0
    assert decompositions[0].service_terms["ev"] == pytest.approx(ev_mixed, abs=1e-12)
    flex_mixed = 0.3 * (2.0 * -0.10) + 0.7 * (2.0 * (-0.30 - 0.10)) / 2.0
    assert decompositions[1].axis_contributions["flex"] == pytest.approx(
        flex_mixed, abs=1e-12
    )


def test_verify_rejects_mismatched_total():
    reward_function, rewards = _run_two_steps("E1")
    decompositions = decompose_reward_function(reward_function)
    tampered = [rewards[0] + 1e-3, *rewards[1:]]
    with pytest.raises(ValueError, match="decomposition"):
        verify_reward_decomposition(decompositions, tampered, atol=1e-9)


def test_as_dict_is_auditable_and_json_ready():
    reward_function, rewards = _run_two_steps("E2")
    record = decompose_reward_function(reward_function)[0].as_dict()

    assert set(record) == {
        "axis_weights",
        "axis_contributions",
        "service_terms",
        "total",
    }
    assert record["service_terms"].keys() == {"ev", "bess_cycle", "comfort"}
    assert record["total"] == pytest.approx(rewards[0], abs=ATOL)
    assert all(
        isinstance(value, float) for value in record["axis_contributions"].values()
    )


def test_missing_breakdown_raises():
    reward_function = CityLearnV3MADRLRewardFunction(
        {"central_agent": False}, scenario="E1"
    )
    with pytest.raises(ValueError, match="breakdown"):
        decompose_reward_function(reward_function)


# --- Audit 2026-11-01 (items 5d, 7): episode supervision summaries ---------------------------------

def test_default_profile_has_no_team_mixing_and_decomposition_is_local():
    reward_function, rewards = _run_two_steps("E1")
    assert "team_reward_ratio" not in reward_function.profile
    decompositions = decompose_reward_function(reward_function)
    local = [c["local_reward"] for c in reward_function._last_component_breakdown["components"]]
    assert [d.total for d in decompositions] == pytest.approx(local, abs=ATOL)


def test_recorder_summarizes_dominance_saturation_and_action_spread():
    from uc3m.reward.term_telemetry import RewardTelemetryRecorder

    recorder = RewardTelemetryRecorder()
    reward_function = CityLearnV3MADRLRewardFunction({"central_agent": False}, algorithm="MATD3", scenario="E1")
    for step in range(3):
        reward_function.calculate(_observations(step))
        recorder.record_step(reward_function._last_component_breakdown,
                             actions={"agent_0": [0.1 * step, -0.2], "agent_1": [0.5, 0.5]})
    episode = recorder.close_episode()
    assert episode["steps"] == 3 and episode["episode"] == 0
    assert set(episode["axis_means"]) == {"flex", "carbon", "cost"}
    assert set(episode["weighted_axis_means"]) == {"flex", "carbon", "cost"}
    assert set(episode["constraint_means"]) == {"ev", "bess_cycle", "comfort"}
    assert episode["effective_axis_weights"] == pytest.approx(EXPECTED_WEIGHTS["E1"])
    components = reward_function._last_component_breakdown["components"]
    assert episode["constraint_dominance_ratio"] > 0
    assert 0.0 <= episode["saturation_fraction"] <= 1.0
    assert episode["action_std_by_agent"]["agent_1"] == pytest.approx(0.0)
    assert episode["action_std_by_agent"]["agent_0"] > 0.0
    summary = recorder.summary()
    assert summary["episodes"] == 1 and summary["steps"] == 3
    assert summary["constraint_dominance_ratio"] == pytest.approx(episode["constraint_dominance_ratio"])
    assert summary["effective_axis_weights"] == pytest.approx(EXPECTED_WEIGHTS["E1"])
    assert len(components) == 3


def test_recorder_dominance_is_hand_computable():
    from uc3m.reward.term_telemetry import RewardTelemetryRecorder

    breakdown = {"axis_weights": {"flex": 0.6, "carbon": 0.15, "cost": 0.25},
                 "components": [{"flex": -1.0, "carbon": -1.0, "cost": -1.0, "weighted_flex": -0.6,
                                 "weighted_carbon": -0.15, "weighted_cost": -0.25, "ev": -0.5,
                                 "bess_cycle": -0.5, "sat_peak": 1.0, "sat_ramp": 0.0,
                                 "net": 1.0, "price": 0.1, "carbon_intensity": 0.5}]}
    recorder = RewardTelemetryRecorder()
    recorder.record_step(breakdown)
    episode = recorder.close_episode()
    assert episode["constraint_dominance_ratio"] == pytest.approx(1.0 / 1.0)
    assert episode["saturation_fraction"] == pytest.approx(0.5)
    assert recorder.close_episode() is None      # an empty episode is not recorded
