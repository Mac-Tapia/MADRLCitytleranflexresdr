"""Project canonical ObjectivePolicy into CityLearn reward_weights format.

CityLearn's ScenarioConfig keys its weights as flex/carbon/cost;
tests/integration/test_citylearn_objective_adapter.py keeps this projection,
CityLearn's built-in E1-E3 weights and its canonical catalog path identical.
"""
from typing import Dict

from uc3m.domain.objectives import canonical_objective_policies, ObjectiveAxis


_AXIS_TO_CITYLEARN = {
    ObjectiveAxis.FLEXIBILITY: "flex",
    ObjectiveAxis.CO2_EMISSIONS: "carbon",
    ObjectiveAxis.ENERGY_COST: "cost",
}


def project_reward_weights(scenario_id: str) -> Dict[str, float]:
    policies = canonical_objective_policies()
    policy = policies[scenario_id]
    return {_AXIS_TO_CITYLEARN[axis]: weight for axis, weight in policy.weights.items()}
