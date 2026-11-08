"""Per-term reward telemetry for the three-objective simplex (SPEC-002 FR-002.5).

The CityLearn v3 MADRL reward (citylearn.v3.reward, profile
fresh_kpi_aligned_v6_net_billing) returns, per
building ``i``, the local reward::

    local_i = reward_scale * (w_flex*flex_i + w_carbon*carbon_i + w_cost*cost_i
                              + ev_i + bess_cycle_i)

and, for a central agent, ``sum_i local_i``. The common-payoff team reward is
applied afterwards by ``CityLearnDecPOMDPEnv`` (``reward_aggregation='team_mean'``);
the former in-reward 0.70/0.30 mixing was removed because team_mean made it
inert. ``team_reward_ratio`` is still accepted here (default 0) to decompose
historical breakdowns. Only ``flex``, ``carbon`` and ``cost`` belong to the
weighted simplex (E1-E3); ``ev``, ``bess_cycle`` and ``comfort`` (SPEC-016 D-V6-53) are constraint
terms added outside it. Because mixing and the central sum are linear, each term can be
propagated separately and the per-term contributions add up exactly to the
reward the environment returned.

``RewardTelemetryRecorder`` accumulates the breakdown of every step into
episode summaries for attempt supervision: axis means before and after
weighting, constraint means, the dominance ratio of constraint terms over the
weighted axes, the saturation fraction of bounded terms and an action-spread
proxy per agent.

This module is read-only telemetry: it consumes the breakdown that the reward
function already records and never alters weights, profiles or reward values.
The reward function is accessed by duck typing; only price_signal_deviation reuses
the CityLearn v3 formula (citylearn.v3.objectives), imported lazily.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, List, Mapping, Sequence

SIMPLEX_AXES = ("flex", "carbon", "cost")
SERVICE_TERMS = ("ev", "bess_cycle", "comfort")   # comfort: SPEC-016 D-V6-53/54, P-V6-25

_WEIGHTED_KEY = {axis: f"weighted_{axis}" for axis in SIMPLEX_AXES}
_DEFAULT_TEAM_RATIO = 0.0


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


THESIS_INDICATORS = ("peak_average", "ramping_average", "one_minus_load_factor_average", "flex_composite",
                     "carbon_emissions_total", "carbon_emissions_delta", "ci_weighted_consumption",
                     "electricity_cost_total", "electricity_cost_delta", "peak_billing", "price_signal_deviation")
PENDING_INDICATORS = {"peak_billing": "reward term pending D04 (weight 0); the KPI is evaluated from data/tariffs/osinergmin/bill_tariffs.csv"}


def _daily_peak(series, steps_per_day):
    days = [series[i:i + steps_per_day] for i in range(0, len(series), steps_per_day)]
    return sum(max(abs(v) for v in day) for day in days) / len(days)


def _ramping(series):
    if len(series) < 2:
        return None
    return math.fsum(abs(b - a) for a, b in zip(series, series[1:])) / (len(series) - 1)


def _one_minus_lf(series, steps_per_day):
    values = []
    for i in range(0, len(series), steps_per_day):
        day = series[i:i + steps_per_day]
        peak = max(abs(v) for v in day)
        if peak <= 0:
            return None
        values.append(1 - (math.fsum(abs(v) for v in day) / len(day)) / peak)
    return math.fsum(values) / len(values)


def _ratio(control, baseline):
    if control is None or baseline is None or baseline == 0:
        return None
    return control / baseline


def exogenous_signals(component) -> dict:
    """Series values of one building step; a missing signal is an error, never a zero."""
    for name in ("net", "price", "carbon_intensity"):
        if name not in component:
            raise ValueError(f"reward component without {name}")
    return {"net": float(component["net"]), "baseline": float(component.get("baseline_net", component["net"])),
            "price": float(component["price"]), "carbon": float(component["carbon_intensity"])}


def thesis_indicators_from_series(net, baseline, price, carbon, steps_per_day=24) -> dict:
    """Layer A indicators (tesis Tabla 2.1) of one series: district or one building.

    Same conventions as configs/evaluation/kpis.yaml: |P| shape KPIs as CityLearn-style
    ratios to the per-step baseline (WITHOUT_STORAGE_BUT_WITH_PV), net billing for CO2
    and cost; peak_billing stays pending (None).
    """
    shape = {
        "peak_average": _ratio(_daily_peak(net, steps_per_day), _daily_peak(baseline, steps_per_day)),
        "ramping_average": _ratio(_ramping(net), _ramping(baseline)),
        "one_minus_load_factor_average": _ratio(_one_minus_lf(net, steps_per_day), _one_minus_lf(baseline, steps_per_day)),
    }
    parts = list(shape.values())
    co2 = math.fsum(n * c for n, c in zip(net, carbon))
    co2_base = math.fsum(b * c for b, c in zip(baseline, carbon))
    cost = math.fsum(n * q for n, q in zip(net, price))
    cost_base = math.fsum(b * q for b, q in zip(baseline, price))
    try:
        from citylearn.v3.objectives import price_signal_deviation
        psd = price_signal_deviation(net, price)
    except Exception:  # noqa: BLE001 - CityLearn unavailable or flat price: reported as None
        psd = None
    return {
        **shape,
        "flex_composite": None if any(v is None for v in parts) else math.fsum(parts) / 3.0,
        "carbon_emissions_total": co2,
        "carbon_emissions_delta": co2 - co2_base,
        "ci_weighted_consumption": math.fsum(max(n, 0.0) * c for n, c in zip(net, carbon)),
        "electricity_cost_total": cost,
        "electricity_cost_delta": cost - cost_base,
        "peak_billing": None,
        "price_signal_deviation": None if psd is None else float(psd),
    }


def _abs_sum(values) -> float:
    return math.fsum(abs(float(v)) for v in values)


REWARD_TERMS = SIMPLEX_AXES + SERVICE_TERMS + ("total",)
# The terms are rebuilt in float64 from the same breakdown: they must equal local_reward exactly
# up to rounding. The returned reward passes through float32 in CityLearnDecPOMDPEnv.
TERM_TOLERANCE = 1e-9
RETURNED_REWARD_TOLERANCE = 1e-5


def _empty_reconciliation() -> dict:
    return {"steps": 0, "returned_checked": 0, "unreconciled_steps": 0, "max_abs_term_error": 0.0,
            "max_abs_returned_error": 0.0, "aggregations": []}


def _reconciliation_report(record: Mapping[str, Any]) -> dict:
    aggregations = list(record["aggregations"])
    return {**{k: v for k, v in record.items() if k != "aggregations"},
            "aggregation": aggregations[0] if len(aggregations) == 1 else (aggregations or None),
            "term_tolerance": TERM_TOLERANCE, "returned_reward_tolerance": RETURNED_REWARD_TOLERANCE}


def _aggregate(locals_: Sequence[float], aggregation: str = None):
    """Reward each agent receives from the local rewards (CityLearnDecPOMDPEnv._aggregate_rewards)."""
    if not locals_:
        return []
    mean = math.fsum(locals_) / len(locals_)
    if aggregation in (None, "team_mean"):
        return [mean] * len(locals_)
    if aggregation == "individual":
        return list(locals_)
    if aggregation == "team_sum":
        return [math.fsum(locals_)] * len(locals_)
    if aggregation == "mixed":
        return [0.7 * v + 0.3 * mean for v in locals_]
    return None


class RewardTelemetryRecorder:
    """Accumulate reward breakdowns and actions into episode supervision summaries.

    ``constraint_dominance_ratio = sum(|ev| + |bess_cycle|) / sum(|weighted axes|)``
    over every building and step; ``saturation_fraction`` is the share of bounded
    terms (``sat_*`` flags) that hit their bound. ``action_std_by_agent`` is the
    mean over action dimensions of the per-dimension standard deviation over the
    episode, an exploration/entropy proxy that needs no access to the policy.
    """

    def __init__(self, steps_per_day: int = 24) -> None:
        self.steps_per_day = int(steps_per_day)
        self.episodes: List[dict] = []
        self._weights = None
        self._attempt_reconciliation = _empty_reconciliation()
        self._reset_episode()

    def _reset_episode(self) -> None:
        self._steps = 0
        self._axis = {axis: 0.0 for axis in SIMPLEX_AXES}
        self._weighted = {axis: 0.0 for axis in SIMPLEX_AXES}
        self._constraints = {name: 0.0 for name in SERVICE_TERMS}
        self._abs_weighted = 0.0
        self._abs_constraints = 0.0
        self._terms = 0
        self._saturated = 0.0
        self._count = 0
        self._actions: dict = {}
        self._series: dict = {}
        self._building_terms: dict = {}
        self._reconciliation = _empty_reconciliation()

    def _record_terms(self, breakdown: Mapping[str, Any], components: Sequence[Mapping[str, Any]],
                      returned_rewards: Sequence[float] = None, aggregation: str = None) -> None:
        """Scaled terms per building and the check that they add up to the reward that was returned."""
        scale = float(breakdown.get("reward_scale", 1.0))
        locals_ = []
        term_error = 0.0
        for index, component in enumerate(components):
            terms = _local_terms(component, scale)
            total = math.fsum(terms[name] for name in REWARD_TERMS[:-1])
            terms["total"] = total
            local = float(component.get("local_reward", total))
            term_error = max(term_error, abs(total - local))
            locals_.append(local)
            sums = self._building_terms.setdefault(index, {name: 0.0 for name in REWARD_TERMS})
            for name in REWARD_TERMS:
                sums[name] += terms[name]
        returned_error = None
        if returned_rewards is not None:
            expected = _aggregate(locals_, aggregation)
            values = [float(v) for v in returned_rewards]
            if expected is not None and len(values) == len(expected):
                returned_error = max((abs(a - b) for a, b in zip(values, expected)), default=0.0)
                scale_ref = max([1.0] + [abs(v) for v in expected])
                mismatch = returned_error > RETURNED_REWARD_TOLERANCE*scale_ref
            else:
                mismatch = True
        else:
            mismatch = False
        for record in (self._reconciliation, self._attempt_reconciliation):
            record["steps"] += 1
            record["max_abs_term_error"] = max(record["max_abs_term_error"], term_error)
            if term_error > TERM_TOLERANCE:
                record["unreconciled_steps"] += 1
            if returned_rewards is not None:
                record["returned_checked"] += 1
                if returned_error is not None:
                    record["max_abs_returned_error"] = max(record["max_abs_returned_error"], returned_error)
                if mismatch and term_error <= TERM_TOLERANCE:
                    record["unreconciled_steps"] += 1
            if aggregation is not None and aggregation not in record["aggregations"]:
                record["aggregations"].append(aggregation)

    def record_step(self, breakdown: Mapping[str, Any], actions: Mapping[str, Sequence[float]] = None, *,
                    returned_rewards: Sequence[float] = None, aggregation: str = None) -> None:
        components = (breakdown or {}).get("components") or []
        if not components:
            return
        self._weights = {axis: float(breakdown["axis_weights"][axis]) for axis in SIMPLEX_AXES}
        self._steps += 1
        self._record_terms(breakdown, components, returned_rewards, aggregation)
        for component in components:
            self._count += 1
            for axis in SIMPLEX_AXES:
                self._axis[axis] += float(component.get(axis, 0.0))
                self._weighted[axis] += float(component[_WEIGHTED_KEY[axis]])
            for name in SERVICE_TERMS:
                self._constraints[name] += float(component.get(name, 0.0))
            self._abs_weighted += _abs_sum(component[_WEIGHTED_KEY[a]] for a in SIMPLEX_AXES)
            self._abs_constraints += _abs_sum(component.get(n, 0.0) for n in SERVICE_TERMS)
            flags = [float(v) for k, v in component.items() if k.startswith("sat_")]
            self._terms += len(flags)
            self._saturated += math.fsum(flags)
        for index, component in enumerate(components):
            series = self._series.setdefault(index, {"net": [], "baseline": [], "price": [], "carbon": []})
            for key, value in exogenous_signals(component).items():
                series[key].append(value)
        for agent, action in (actions or {}).items():
            raw = action.tolist() if hasattr(action, "tolist") else action
            values = [float(v) for v in (raw if isinstance(raw, (list, tuple)) else [raw])]
            sums = self._actions.setdefault(str(agent), {"n": 0, "sum": [0.0] * len(values),
                                                         "sq": [0.0] * len(values)})
            if len(sums["sum"]) != len(values):
                continue
            sums["n"] += 1
            for index, value in enumerate(values):
                sums["sum"][index] += value
                sums["sq"][index] += value * value

    @staticmethod
    def _ratio(numerator: float, denominator: float) -> float:
        if denominator > 0.0:
            return numerator / denominator
        return 0.0 if numerator == 0.0 else math.inf

    def _action_std(self) -> dict:
        out = {}
        for agent, sums in self._actions.items():
            n = sums["n"]
            if not n or not sums["sum"]:
                continue
            stds = [math.sqrt(max(sq / n - (s / n) ** 2, 0.0)) for s, sq in zip(sums["sum"], sums["sq"])]
            out[agent] = math.fsum(stds) / len(stds)
        return out

    def _episode_indicators(self) -> dict:
        if not self._series:
            return {}
        buildings = {f"building_{i}": thesis_indicators_from_series(
            v["net"], v["baseline"], v["price"], v["carbon"], self.steps_per_day) for i, v in self._series.items()}
        first = self._series[min(self._series)]
        district = {key: [math.fsum(v[key][t] for v in self._series.values()) for t in range(len(first["net"]))]
                    for key in ("net", "baseline")}
        aggregate = thesis_indicators_from_series(district["net"], district["baseline"], first["price"],
                                                  first["carbon"], self.steps_per_day)
        # Shape ratios use the district flow. Settlements use each building's
        # actual tariff/intensity before aggregation, including signed exports.
        for key in ("electricity_cost_total", "electricity_cost_delta", "carbon_emissions_total",
                    "carbon_emissions_delta", "ci_weighted_consumption"):
            aggregate[key] = math.fsum(row[key] for row in buildings.values())
        unavailable = {}
        if any(v["price"] != first["price"] for v in self._series.values()):
            aggregate["price_signal_deviation"] = None
            unavailable["district.price_signal_deviation"] = "heterogeneous_building_prices"
        return {"district": aggregate, "buildings": buildings, "pending": dict(PENDING_INDICATORS),
                "unavailable": unavailable}

    def close_episode(self, citylearn_v3=None):
        """Close the running episode; returns its summary, or None if it had no step.

        ``citylearn_v3``: optional Layer B record of the episode (KPI-gain rows of
        evaluate_objectives, district and building), stored as given.
        """
        if not self._steps:
            return None
        count = max(self._count, 1)
        summary = {
            "episode": len(self.episodes),
            "steps": self._steps,
            "effective_axis_weights": dict(self._weights),
            "axis_means": {a: v / count for a, v in self._axis.items()},
            "weighted_axis_means": {a: v / count for a, v in self._weighted.items()},
            "constraint_means": {n: v / count for n, v in self._constraints.items()},
            "abs_weighted_axes_sum": self._abs_weighted,
            "abs_constraint_sum": self._abs_constraints,
            "constraint_dominance_ratio": self._ratio(self._abs_constraints, self._abs_weighted),
            "saturation_fraction": (self._saturated / self._terms) if self._terms else 0.0,
            "action_std_by_agent": self._action_std(),
            "thesis_indicators": self._episode_indicators(),
            "citylearn_v3": citylearn_v3,
        }
        steps = max(self._steps, 1)
        buildings = {f"building_{i}": {name: value / steps for name, value in sums.items()}
                     for i, sums in sorted(self._building_terms.items())}
        summary["building_reward_terms"] = buildings
        summary["reward_terms_mean"] = (
            {name: math.fsum(row[name] for row in buildings.values()) / len(buildings) for name in REWARD_TERMS}
            if buildings else {}
        )
        summary["reward_reconciliation"] = _reconciliation_report(self._reconciliation)
        self.episodes.append(summary)
        self._reset_episode()
        return summary

    def summary(self) -> dict:
        """Attempt-level summary over every closed episode (closes the running one)."""
        self.close_episode()
        abs_weighted = math.fsum(e["abs_weighted_axes_sum"] for e in self.episodes)
        abs_constraints = math.fsum(e["abs_constraint_sum"] for e in self.episodes)
        saturation = [e["saturation_fraction"] for e in self.episodes]
        return {
            "episodes": len(self.episodes),
            "steps": sum(e["steps"] for e in self.episodes),
            "effective_axis_weights": dict(self._weights) if self._weights else None,
            "constraint_dominance_ratio": (
                self._ratio(abs_constraints, abs_weighted) if self.episodes else None
            ),
            "max_episode_constraint_dominance_ratio": (
                max(e["constraint_dominance_ratio"] for e in self.episodes) if self.episodes else None
            ),
            "saturation_fraction": (math.fsum(saturation) / len(saturation)) if saturation else None,
            "episodes_detail": list(self.episodes),
            "kpi_trend": self.kpi_trend(),
            "reward_reconciliation": _reconciliation_report(self._attempt_reconciliation),
        }

    def kpi_trend(self) -> dict:
        """First versus last episode of every Layer A indicator (district) and Layer B gain."""
        if not self.episodes:
            return {}
        first, last = self.episodes[0], self.episodes[-1]
        trend = {}
        for name in THESIS_INDICATORS:
            a = (first.get("thesis_indicators") or {}).get("district", {}).get(name)
            b = (last.get("thesis_indicators") or {}).get("district", {}).get(name)
            trend[name] = {"first": a, "last": b, "change": None if a is None or b is None else b - a}
        rows_first = {r["name"]: r for r in ((first.get("citylearn_v3") or {}).get("gains") or [])}
        for row in ((last.get("citylearn_v3") or {}).get("gains") or []):
            a = (rows_first.get(row["name"]) or {}).get("gain")
            trend[f"citylearn_v3:{row['name']}"] = {"first": a, "last": row.get("gain"),
                                                     "change": None if a is None or row.get("gain") is None
                                                     else row["gain"] - a}
        return trend
