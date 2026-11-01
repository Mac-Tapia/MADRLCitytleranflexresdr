"""Per-term reward telemetry for the three-objective simplex (SPEC-002 FR-002.5).

The CityLearn v3 MADRL reward combines, per building ``i``::

    local_i = reward_scale * (w_flex*flex_i + w_carbon*carbon_i + w_cost*cost_i
                              + ev_i + bess_cycle_i)
    reward_i = (1 - team_ratio) * local_i + team_ratio * mean_j(local_j)

and, for a central agent, ``sum_i reward_i``. Only ``flex``, ``carbon`` and
``cost`` belong to the weighted simplex (E1-E3). ``ev`` and ``bess_cycle`` are
service/constraint terms added outside it. Because team mixing and the central
sum are linear, each term can be propagated separately and the per-term
contributions add up exactly to the reward the environment returned.

This module is read-only telemetry: it consumes the breakdown that the reward
function already records and never alters weights, profiles or reward values.
It does not import CityLearn; the reward function is accessed by duck typing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, List, Mapping, Sequence

SIMPLEX_AXES = ("flex", "carbon", "cost")
SERVICE_TERMS = ("ev", "bess_cycle")

_WEIGHTED_KEY = {axis: f"weighted_{axis}" for axis in SIMPLEX_AXES}
_DEFAULT_TEAM_RATIO = 0.70


@dataclass(frozen=True)
class RewardTermDecomposition:
    """Auditable split of one agent's step reward."""

    axis_weights: Mapping[str, float]
    axis_contributions: Mapping[str, float]
    service_terms: Mapping[str, float]
    total: float

    def as_dict(self) -> dict:
        return {
            "axis_weights": {k: float(v) for k, v in self.axis_weights.items()},
            "axis_contributions": {
                k: float(v) for k, v in self.axis_contributions.items()
            },
            "service_terms": {k: float(v) for k, v in self.service_terms.items()},
            "total": float(self.total),
        }


def _clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _local_terms(component: Mapping[str, Any], scale: float) -> dict:
    terms = {
        axis: scale * float(component[_WEIGHTED_KEY[axis]]) for axis in SIMPLEX_AXES
    }
    for name in SERVICE_TERMS:
        terms[name] = scale * float(component.get(name, 0.0))
    return terms


def _build(axis_weights: Mapping[str, float], terms: Mapping[str, float]):
    axes = MappingProxyType({axis: terms[axis] for axis in SIMPLEX_AXES})
    service = MappingProxyType({name: terms[name] for name in SERVICE_TERMS})
    total = math.fsum(list(axes.values()) + list(service.values()))
    return RewardTermDecomposition(axis_weights, axes, service, total)


def decompose_citylearn_v3_breakdown(
    breakdown: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    central_agent: bool = False,
) -> List[RewardTermDecomposition]:
    """Decompose a ``CityLearnV3MADRLRewardFunction`` component breakdown.

    ``profile`` supplies ``reward_scale`` and ``team_reward_ratio`` exactly as
    the reward function reads them. Returns one decomposition per returned
    reward (one per building, or a single one for a central agent).
    """

    components = breakdown.get("components") if breakdown else None
    if not components:
        raise ValueError("reward breakdown is empty; call calculate() first")

    raw_weights = breakdown["axis_weights"]
    axis_weights = MappingProxyType(
        {axis: float(raw_weights[axis]) for axis in SIMPLEX_AXES}
    )
    scale = float(profile.get("reward_scale", 1.0))
    team_ratio = _clip01(float(profile.get("team_reward_ratio", _DEFAULT_TEAM_RATIO)))
    individual_ratio = 1.0 - team_ratio

    local = [_local_terms(component, scale) for component in components]
    names = SIMPLEX_AXES + SERVICE_TERMS
    team_mean = {name: math.fsum(t[name] for t in local) / len(local) for name in names}
    mixed = [
        {
            name: individual_ratio * t[name] + team_ratio * team_mean[name]
            for name in names
        }
        for t in local
    ]

    if central_agent:
        summed = {name: math.fsum(t[name] for t in mixed) for name in names}
        return [_build(axis_weights, summed)]
    return [_build(axis_weights, terms) for terms in mixed]


def decompose_reward_function(reward_function: Any) -> List[RewardTermDecomposition]:
    """Decompose the last ``calculate()`` of a CityLearn v3 MADRL reward function."""

    breakdown = getattr(reward_function, "_last_component_breakdown", None)
    if not breakdown:
        raise ValueError("reward breakdown is empty; call calculate() first")
    return decompose_citylearn_v3_breakdown(
        breakdown,
        profile=reward_function.profile,
        central_agent=bool(reward_function.central_agent),
    )


def verify_reward_decomposition(
    decompositions: Sequence[RewardTermDecomposition],
    rewards: Sequence[float],
    atol: float = 1e-9,
    rtol: float = 0.0,
) -> None:
    """Raise ``ValueError`` unless every decomposition total matches its reward."""

    if len(decompositions) != len(rewards):
        raise ValueError(
            f"decomposition count {len(decompositions)} != reward count {len(rewards)}"
        )
    for index, (decomposition, reward) in enumerate(zip(decompositions, rewards)):
        terms = list(decomposition.axis_contributions.values()) + list(
            decomposition.service_terms.values()
        )
        if not math.isclose(math.fsum(terms), decomposition.total, abs_tol=atol):
            raise ValueError(f"decomposition {index}: terms do not sum to total")
        if not math.isclose(
            decomposition.total, float(reward), rel_tol=rtol, abs_tol=atol
        ):
            raise ValueError(
                f"decomposition {index}: total {decomposition.total!r} != reward {reward!r}"
            )
