"""Scenario contracts that separate objectives, tariffs, and constraints."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterator, Literal, Mapping, Sequence, ValuesView

from uc3m.domain.objectives import ObjectivePolicy


def _fingerprint(payload: Mapping[str, object]) -> str:
    serialized = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclass(frozen=True)
class TariffPolicy:
    policy_id: str
    mode: Literal["rtp", "flat", "tou"]
    multiplier: float

    def __post_init__(self) -> None:
        if self.mode not in {"rtp", "flat", "tou"}:
            raise ValueError("Unsupported tariff mode")
        if not math.isfinite(self.multiplier) or self.multiplier <= 0.0:
            raise ValueError("Tariff multiplier must be finite and positive")

    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "mode": self.mode,
                "multiplier": float(self.multiplier),
            }
        )


@dataclass(frozen=True)
class ConstraintPolicy:
    policy_id: str
    ev_service_enabled: bool
    bess_limits_enabled: bool

    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "ev_service_enabled": self.ev_service_enabled,
                "bess_limits_enabled": self.bess_limits_enabled,
            }
        )


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    objective_policy: ObjectivePolicy
    tariff_policy: TariffPolicy
    constraint_policy: ConstraintPolicy
    study_kind: Literal["weights_only", "composite"]

    def __post_init__(self) -> None:
        if self.study_kind not in {"weights_only", "composite"}:
            raise ValueError("study_kind must be weights_only or composite")

    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "scenario_id": self.scenario_id,
                "study_kind": self.study_kind,
                "objective_policy": self.objective_policy.fingerprint(),
                "tariff_policy": self.tariff_policy.fingerprint(),
                "constraint_policy": self.constraint_policy.fingerprint(),
            }
        )


class ScenarioCatalog:
    def __init__(self, scenarios: Sequence[ScenarioDefinition]) -> None:
        by_id = {scenario.scenario_id: scenario for scenario in scenarios}
        if len(by_id) != len(scenarios):
            raise ValueError("Scenario IDs must be unique")

        weights_only = [
            scenario for scenario in scenarios if scenario.study_kind == "weights_only"
        ]
        tariff_fingerprints = {
            scenario.tariff_policy.fingerprint() for scenario in weights_only
        }
        if len(tariff_fingerprints) > 1:
            raise ValueError("weights_only scenarios require identical tariff policies")
        constraint_fingerprints = {
            scenario.constraint_policy.fingerprint() for scenario in weights_only
        }
        if len(constraint_fingerprints) > 1:
            raise ValueError("weights_only scenarios require identical constraints")

        self._scenarios = MappingProxyType(by_id)

    def __iter__(self) -> Iterator[str]:
        return iter(self._scenarios)

    def __getitem__(self, scenario_id: str) -> ScenarioDefinition:
        return self._scenarios[scenario_id]

    def __len__(self) -> int:
        return len(self._scenarios)

    def values(self) -> ValuesView[ScenarioDefinition]:
        return self._scenarios.values()
