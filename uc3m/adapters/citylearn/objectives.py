"""Project canonical ObjectivePolicy into CityLearn reward_weights format."""
from typing import Dict

from uc3m.domain.objectives import canonical_objective_policies, ObjectiveAxis


_AXIS_TO_CITYLEARN = {
    ObjectiveAxis.FLEXIBILITY: "flexibility",
    ObjectiveAxis.CO2_EMISSIONS: "co2_emissions",
    ObjectiveAxis.ENERGY_COST: "energy_cost",
}


def project_reward_weights(scenario_id: str) -> Dict[str, float]:
    policies = canonical_objective_policies()
    policy = policies[scenario_id]
    return {_AXIS_TO_CITYLEARN[axis]: weight for axis, weight in policy.weights.items()}
