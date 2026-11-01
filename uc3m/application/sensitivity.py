"""Deterministic objective-weight sensitivity design without training side effects."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Literal, Tuple

from uc3m.domain.objectives import (
    CANONICAL_AXES,
    HierarchyLevels,
    ObjectivePolicy,
    canonical_objective_policies,
)


def _weight_key(policy: ObjectivePolicy) -> Tuple[float, ...]:
    return tuple(round(policy.weights[axis], 12) for axis in CANONICAL_AXES)


def generate_weight_grid(
    levels: HierarchyLevels,
    step: float,
) -> Tuple[ObjectivePolicy, ...]:
    """Generate an auditable simplex grid while retaining every objective.

    The residual hierarchy level is the minimum admissible weight. Canonical
    E1-E3 policies are always included with their stable IDs and fingerprints.
    """

    if not math.isfinite(step) or step <= 0.0 or step > 1.0:
        raise ValueError("step must be finite and in (0, 1]")
    units = round(1.0 / step)
    if units <= 0 or not math.isclose(units * step, 1.0, abs_tol=1e-12):
        raise ValueError("step must divide the unit simplex exactly")
    minimum_units = math.ceil((levels.residual - 1e-12) / step)

    policies = list(canonical_objective_policies().values())
    existing_weights = {_weight_key(policy) for policy in policies}
    for flexibility_units in range(minimum_units, units + 1):
        for co2_units in range(minimum_units, units + 1):
            cost_units = units - flexibility_units - co2_units
            if cost_units < minimum_units:
                continue
            values = (
                flexibility_units * step,
                co2_units * step,
                cost_units * step,
            )
            rounded = tuple(round(value, 12) for value in values)
            if rounded in existing_weights:
                continue
            policy_id = "SENS-{:03d}-{:03d}-{:03d}".format(
                *(round(value * 100) for value in values)
            )
            policies.append(
                ObjectivePolicy(
                    policy_id=policy_id,
                    weights=dict(zip(CANONICAL_AXES, values)),
                )
            )
            existing_weights.add(rounded)
    return tuple(policies)


@dataclass(frozen=True)
class ExperimentMatrix:
    algorithms: Tuple[str, ...]
    policies: Tuple[ObjectivePolicy, ...]
    seeds: Tuple[int, ...]
    timesteps_per_run: int
    study_kind: Literal["weights_only", "composite"]

    def __post_init__(self) -> None:
        if not self.algorithms or len(set(self.algorithms)) != len(self.algorithms):
            raise ValueError("algorithms must be non-empty and unique")
        if not self.policies or len(
            {policy.fingerprint() for policy in self.policies}
        ) != len(self.policies):
            raise ValueError("policies must be non-empty and unique")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be non-empty and unique")
        if self.timesteps_per_run <= 0:
            raise ValueError("timesteps_per_run must be positive")
        if self.study_kind not in {"weights_only", "composite"}:
            raise ValueError("study_kind must be weights_only or composite")

    def as_manifest(self) -> Dict[str, object]:
        run_count = len(self.algorithms) * len(self.policies) * len(self.seeds)
        return {
            "schema_version": "1.0",
            "study_kind": self.study_kind,
            "launch_authorized": False,
            "algorithms": list(self.algorithms),
            "seeds": list(self.seeds),
            "timesteps_per_run": self.timesteps_per_run,
            "run_count": run_count,
            "estimated_environment_steps": run_count * self.timesteps_per_run,
            "treatments": [
                {
                    "policy_id": policy.policy_id,
                    "fingerprint": policy.fingerprint(),
                    "weights": policy.as_dict()["weights"],
                }
                for policy in self.policies
            ],
        }
