"""Six-dimension evaluation criteria for MADRL algorithm selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

ALGORITHMS: Tuple[str, ...] = ("HAPPO", "MAAC", "MASAC", "MATD3")

# Saaty / TOPSIS criterion ids (section 3.1 of the methodology).
CRITERION_IDS: Tuple[str, ...] = ("C1", "C2", "C3", "C4", "C5", "C6")


@dataclass(frozen=True)
class SelectionCriterion:
    """One aggregated decision criterion (benefit or cost)."""

    id: str
    name: str
    dimension: str
    kind: str  # "benefit" | "cost"
    unit: str
    default_weight: float
    higher_is_better: bool


CRITERION_SPECS: Mapping[str, SelectionCriterion] = {
    "C1": SelectionCriterion(
        id="C1",
        name="total_operating_cost",
        dimension="technical_performance",
        kind="cost",
        unit="EUR",
        default_weight=0.25,
        higher_is_better=False,
    ),
    "C2": SelectionCriterion(
        id="C2",
        name="co2_avoided",
        dimension="technical_performance",
        kind="benefit",
        unit="kgCO2",
        default_weight=0.25,
        higher_is_better=True,
    ),
    "C3": SelectionCriterion(
        id="C3",
        name="flexibility_activated",
        dimension="technical_performance",
        kind="benefit",
        unit="kWh",
        default_weight=0.15,
        higher_is_better=True,
    ),
    "C4": SelectionCriterion(
        id="C4",
        name="inter_seed_variance",
        dimension="training_stability",
        kind="cost",
        unit="reward^2",
        default_weight=0.10,
        higher_is_better=False,
    ),
    "C5": SelectionCriterion(
        id="C5",
        name="steps_to_90pct_asymptotic",
        dimension="sample_compute_efficiency",
        kind="cost",
        unit="steps",
        default_weight=0.10,
        higher_is_better=False,
    ),
    "C6": SelectionCriterion(
        id="C6",
        name="train_test_gap",
        dimension="robustness_generalization",
        kind="cost",
        unit="reward",
        default_weight=0.15,
        higher_is_better=False,
    ),
}

DEFAULT_CRITERION_WEIGHTS: Mapping[str, float] = {
    cid: spec.default_weight for cid, spec in CRITERION_SPECS.items()
}


@dataclass(frozen=True)
class MetricAggregate:
    """Mean ± std aggregation over seeds (or replicate runs)."""

    name: str
    mean: float
    std: float
    n: int
    unit: str = ""
    values: Tuple[float, ...] = field(default_factory=tuple)

    def as_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["mean_pm_std"] = mean_std_report(self.mean, self.std)
        return payload


def mean_std_report(mean: float, std: float, *, digits: int = 4) -> str:
    """Format ``mean ± std`` for tables."""

    return f"{mean:.{digits}g} ± {std:.{digits}g}"


def aggregate_seed_values(
    name: str,
    values: Sequence[float],
    *,
    unit: str = "",
) -> MetricAggregate:
    """Aggregate a seed series as mean ± sample std (ddof=1 when n>1)."""

    arr = np.asarray([float(v) for v in values if np.isfinite(float(v))], dtype=float)
    if arr.size == 0:
        return MetricAggregate(name=name, mean=float("nan"), std=float("nan"), n=0, unit=unit)
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    return MetricAggregate(
        name=name,
        mean=mean,
        std=std,
        n=int(arr.size),
        unit=unit,
        values=tuple(float(x) for x in arr),
    )


def total_operating_cost(
    prices: Sequence[float],
    energy_by_agent: Sequence[Sequence[float]],
) -> float:
    """C = sum_t sum_i p_t * e_{i,t}."""

    price = np.asarray(prices, dtype=float)
    energy = np.asarray(energy_by_agent, dtype=float)
    if energy.ndim != 2:
        raise ValueError("energy_by_agent must be shaped (n_agents, T) or (T, n_agents)")
    if energy.shape[1] == price.shape[0]:
        # (n_agents, T)
        return float(np.sum(price[None, :] * energy))
    if energy.shape[0] == price.shape[0]:
        # (T, n_agents)
        return float(np.sum(price[:, None] * energy))
    raise ValueError("price length must match the time axis of energy_by_agent")


def co2_avoided(co2_baseline: float, co2_policy: float) -> float:
    """ΔCO₂ = CO2_baseline - CO2_policy (kg). Higher is better."""

    return float(co2_baseline) - float(co2_policy)


def flexibility_activated(
    energy: Sequence[Sequence[float]],
    energy_ref: Sequence[Sequence[float]],
) -> float:
    """F = sum_t ||e_{i,t} - e_{i,t}^{ref}|| (L1 over agents, sum over time)."""

    e = np.asarray(energy, dtype=float)
    r = np.asarray(energy_ref, dtype=float)
    if e.shape != r.shape:
        raise ValueError("energy and energy_ref must share the same shape")
    return float(np.sum(np.abs(e - r)))


def mean_cumulative_reward(seed_returns: Sequence[float]) -> MetricAggregate:
    """R̄ over seeds S."""

    return aggregate_seed_values("mean_cumulative_reward", seed_returns, unit="reward")


def violation_rate(n_violation_steps: int, n_total_steps: int) -> float:
    """% of comfort/operation violation steps."""

    total = max(int(n_total_steps), 0)
    if total <= 0:
        return float("nan")
    return 100.0 * float(n_violation_steps) / float(total)


def mean_violation_severity(excesses: Sequence[float]) -> float:
    """Mean excess over the limit when a violation occurs."""

    arr = np.asarray([float(x) for x in excesses if np.isfinite(float(x))], dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.mean(arr))


def inter_seed_variance(seed_mean_rewards: Sequence[float]) -> float:
    """σ²(R̄_s) over seeds (population variance for the criterion)."""

    arr = np.asarray(seed_mean_rewards, dtype=float)
    if arr.size == 0:
        return float("nan")
    if arr.size == 1:
        return 0.0
    return float(np.var(arr, ddof=0))


def reward_drop_count(
    episode_rewards: Sequence[float],
    *,
    drop_fraction: float = 0.10,
) -> int:
    """Count episodes with drop > X% from the running maximum."""

    if not episode_rewards:
        return 0
    running_max = float("-inf")
    drops = 0
    threshold = float(drop_fraction)
    for value in episode_rewards:
        r = float(value)
        if not np.isfinite(r):
            continue
        if running_max == float("-inf"):
            running_max = r
            continue
        if running_max > 0 and (running_max - r) / abs(running_max) > threshold:
            drops += 1
        elif running_max <= 0 and (running_max - r) > threshold * max(abs(running_max), 1.0):
            drops += 1
        running_max = max(running_max, r)
    return int(drops)


def steps_to_fraction_of_asymptotic(
    step_rewards: Sequence[float],
    *,
    fraction: float = 0.90,
    asymptotic_window: int = 10,
) -> float:
    """First step index where reward reaches ``fraction`` of asymptotic mean."""

    arr = np.asarray(step_rewards, dtype=float)
    if arr.size == 0:
        return float("nan")
    window = max(1, min(int(asymptotic_window), int(arr.size)))
    asymptotic = float(np.mean(arr[-window:]))
    target = fraction * asymptotic
    # If rewards increase toward a less-negative / higher asymptote.
    if asymptotic >= arr[0]:
        hits = np.where(arr >= target)[0]
    else:
        hits = np.where(arr <= target)[0]
    if hits.size == 0:
        return float(arr.size)
    return float(hits[0])


def compute_time_per_1000_steps(elapsed_seconds: float, n_steps: int) -> float:
    """Seconds of wall time per 1000 environment steps."""

    steps = max(int(n_steps), 1)
    return 1000.0 * float(elapsed_seconds) / float(steps)


def reward_degradation(reward_n_large: float, reward_n_small: float) -> float:
    """R̄(N_large) - R̄(N_small). Negative usually means loss at scale."""

    return float(reward_n_large) - float(reward_n_small)


def training_time_growth_slope(
    agent_counts: Sequence[int],
    train_times: Sequence[float],
) -> float:
    """Slope of training time vs number of agents (least squares)."""

    x = np.asarray(agent_counts, dtype=float)
    y = np.asarray(train_times, dtype=float)
    if x.size != y.size or x.size < 2:
        return float("nan")
    slope, _intercept = np.polyfit(x, y, 1)
    return float(slope)


def train_test_gap(reward_train: float, reward_test: float) -> float:
    """R̄_train - R̄_test (cost criterion; larger gap is worse)."""

    return float(reward_train) - float(reward_test)


def forecast_noise_degradation(reward_clean: float, reward_noisy: float) -> float:
    """R̄(noise=0%) - R̄(noise=20%)."""

    return float(reward_clean) - float(reward_noisy)


def compute_dimension_metrics(
    *,
    seed_returns: Sequence[float],
    episode_rewards: Optional[Sequence[float]] = None,
    step_rewards: Optional[Sequence[float]] = None,
    prices: Optional[Sequence[float]] = None,
    energy_by_agent: Optional[Sequence[Sequence[float]]] = None,
    energy_ref: Optional[Sequence[Sequence[float]]] = None,
    co2_baseline: Optional[float] = None,
    co2_policy: Optional[float] = None,
    n_violation_steps: int = 0,
    n_total_steps: int = 0,
    violation_excesses: Optional[Sequence[float]] = None,
    elapsed_seconds: Optional[float] = None,
    n_env_steps: Optional[int] = None,
    reward_by_n_agents: Optional[Mapping[int, float]] = None,
    time_by_n_agents: Optional[Mapping[int, float]] = None,
    reward_train: Optional[float] = None,
    reward_test: Optional[float] = None,
    reward_noise_0: Optional[float] = None,
    reward_noise_20: Optional[float] = None,
    drop_fraction: float = 0.10,
) -> Dict[str, object]:
    """Compute all six methodology dimensions from available run traces."""

    out: Dict[str, object] = {
        "technical_performance": {},
        "constraint_compliance": {},
        "training_stability": {},
        "sample_compute_efficiency": {},
        "scalability": {},
        "robustness_generalization": {},
    }

    tech = out["technical_performance"]
    assert isinstance(tech, dict)
    if prices is not None and energy_by_agent is not None:
        tech["total_operating_cost"] = total_operating_cost(prices, energy_by_agent)
    if co2_baseline is not None and co2_policy is not None:
        tech["co2_avoided"] = co2_avoided(co2_baseline, co2_policy)
    if energy_by_agent is not None and energy_ref is not None:
        tech["flexibility_activated"] = flexibility_activated(energy_by_agent, energy_ref)
    tech["mean_cumulative_reward"] = mean_cumulative_reward(seed_returns).as_dict()

    out["constraint_compliance"] = {
        "violation_rate_pct": violation_rate(n_violation_steps, n_total_steps),
        "mean_violation_severity": mean_violation_severity(violation_excesses or ()),
    }

    stab = out["training_stability"]
    assert isinstance(stab, dict)
    stab["inter_seed_variance"] = inter_seed_variance(seed_returns)
    stab["reward_drop_count"] = reward_drop_count(
        episode_rewards or (),
        drop_fraction=drop_fraction,
    )
    stab["seed_returns"] = mean_cumulative_reward(seed_returns).as_dict()

    eff = out["sample_compute_efficiency"]
    assert isinstance(eff, dict)
    if step_rewards is not None:
        eff["steps_to_90pct_asymptotic"] = steps_to_fraction_of_asymptotic(step_rewards)
    if elapsed_seconds is not None and n_env_steps is not None:
        eff["seconds_per_1000_steps"] = compute_time_per_1000_steps(
            elapsed_seconds, n_env_steps
        )

    scale = out["scalability"]
    assert isinstance(scale, dict)
    if reward_by_n_agents and 5 in reward_by_n_agents and 50 in reward_by_n_agents:
        scale["reward_degradation_N50_minus_N5"] = reward_degradation(
            reward_by_n_agents[50], reward_by_n_agents[5]
        )
    if time_by_n_agents and len(time_by_n_agents) >= 2:
        ns = sorted(time_by_n_agents)
        scale["training_time_growth_slope"] = training_time_growth_slope(
            ns, [time_by_n_agents[n] for n in ns]
        )

    rob = out["robustness_generalization"]
    assert isinstance(rob, dict)
    if reward_train is not None and reward_test is not None:
        rob["train_test_gap"] = train_test_gap(reward_train, reward_test)
    if reward_noise_0 is not None and reward_noise_20 is not None:
        rob["forecast_noise_degradation_0_vs_20"] = forecast_noise_degradation(
            reward_noise_0, reward_noise_20
        )

    return out


def criteria_manifest() -> Dict[str, object]:
    """Serializable description of C1–C6 for reports / notebooks."""

    return {
        "algorithms": list(ALGORITHMS),
        "criteria": {cid: asdict(spec) for cid, spec in CRITERION_SPECS.items()},
        "default_weights": dict(DEFAULT_CRITERION_WEIGHTS),
        "reporting": "Always report mean ± std over >=10 seeds when available.",
    }
