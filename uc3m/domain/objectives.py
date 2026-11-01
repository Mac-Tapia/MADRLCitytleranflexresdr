"""Canonical multiobjective values and compensatory hierarchy policies."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping

import numpy as np


class ObjectiveAxis(str, Enum):
    FLEXIBILITY = "flexibility"
    CO2_EMISSIONS = "co2_emissions"
    ENERGY_COST = "energy_cost"


CANONICAL_AXES = (
    ObjectiveAxis.FLEXIBILITY,
    ObjectiveAxis.CO2_EMISSIONS,
    ObjectiveAxis.ENERGY_COST,
)


@dataclass(frozen=True)
class RewardVector:
    flexibility: float
    co2_emissions: float
    energy_cost: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in self.as_array()):
            raise ValueError("RewardVector values must be finite")

    def as_array(self) -> np.ndarray:
        return np.asarray(
            [self.flexibility, self.co2_emissions, self.energy_cost], dtype=float
        )


@dataclass(frozen=True)
class HierarchyLevels:
    primary: float = 0.60
    secondary: float = 0.25
    residual: float = 0.15

    def __post_init__(self) -> None:
        values = (self.primary, self.secondary, self.residual)
        if not all(math.isfinite(value) and value >= 0.0 for value in values):
            raise ValueError("Hierarchy levels must be finite and non-negative")
        if not math.isclose(sum(values), 1.0, abs_tol=1e-12):
            raise ValueError("Hierarchy levels must sum to 1")
        if not self.primary > self.secondary + self.residual:
            raise ValueError("Primary level must have a strict majority")


@dataclass(frozen=True)
class ObjectivePolicy:
    policy_id: str
    weights: Mapping[ObjectiveAxis, float]
    method: str = "compensatory_hierarchical_weighted_sum"

    def __post_init__(self) -> None:
        normalized = dict(self.weights)
        if set(normalized) != set(CANONICAL_AXES):
            raise ValueError("ObjectivePolicy requires exactly the canonical axes")
        if not all(
            math.isfinite(value) and value >= 0.0 for value in normalized.values()
        ):
            raise ValueError("Objective weights must be finite and non-negative")
        if not math.isclose(sum(normalized.values()), 1.0, abs_tol=1e-12):
            raise ValueError("Objective weights must sum to 1")
        ordered = {axis: float(normalized[axis]) for axis in CANONICAL_AXES}
        object.__setattr__(self, "weights", MappingProxyType(ordered))

    def scalarize(self, reward: RewardVector) -> float:
        weight_array = np.asarray([self.weights[axis] for axis in CANONICAL_AXES])
        return float(np.dot(weight_array, reward.as_array()))

    def as_dict(self) -> Dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "method": self.method,
            "weights": {axis.value: self.weights[axis] for axis in CANONICAL_AXES},
        }

    def fingerprint(self) -> str:
        serialized = json.dumps(
            self.as_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()


def canonical_objective_policies() -> Mapping[str, ObjectivePolicy]:
    policies = {
        "E1": ObjectivePolicy(
            "E1",
            {
                ObjectiveAxis.FLEXIBILITY: 0.60,
                ObjectiveAxis.CO2_EMISSIONS: 0.15,
                ObjectiveAxis.ENERGY_COST: 0.25,
            },
        ),
        "E2": ObjectivePolicy(
            "E2",
            {
                ObjectiveAxis.FLEXIBILITY: 0.25,
                ObjectiveAxis.CO2_EMISSIONS: 0.60,
                ObjectiveAxis.ENERGY_COST: 0.15,
            },
        ),
        "E3": ObjectivePolicy(
            "E3",
            {
                ObjectiveAxis.FLEXIBILITY: 0.15,
                ObjectiveAxis.CO2_EMISSIONS: 0.25,
                ObjectiveAxis.ENERGY_COST: 0.60,
            },
        ),
    }
    return MappingProxyType(policies)
