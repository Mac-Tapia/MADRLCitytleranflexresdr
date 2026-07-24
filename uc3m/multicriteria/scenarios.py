"""Scenario configurations for the empirical MADRL selection methodology."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    description: str
    n_agents: Tuple[int, ...]
    forecast_noise_pct: Tuple[float, ...] = (0.0,)
    train_year: str = "year1"
    test_year: str = "year1"
    measures: Tuple[str, ...] = ()
    notes: str = ""

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


BASE_SCENARIO = ScenarioConfig(
    name="base",
    description="Nominal conditions for technical performance and constraint compliance.",
    n_agents=(10,),
    forecast_noise_pct=(0.0,),
    measures=(
        "total_operating_cost",
        "co2_avoided",
        "flexibility_activated",
        "mean_cumulative_reward",
        "violation_rate_pct",
        "mean_violation_severity",
    ),
    notes="CityLearn Iquitos district uses 17 buildings in production runs; "
    "methodology example uses N=10 as the nominal reference.",
)

SCALABILITY_SCENARIO = ScenarioConfig(
    name="scalability",
    description="Reward degradation and training-time growth vs agent count.",
    n_agents=(5, 20, 50),
    measures=(
        "reward_degradation_N50_minus_N5",
        "training_time_growth_slope",
    ),
    notes="N=50 requires a synthetic/upsampled district schema; not runnable on "
    "the default 17-building Iquitos dataset without data expansion.",
)

ROBUSTNESS_SCENARIO = ScenarioConfig(
    name="robustness",
    description="Degradation under demand/price/CO2 forecast noise.",
    n_agents=(10,),
    forecast_noise_pct=(0.0, 10.0, 20.0),
    measures=("forecast_noise_degradation_0_vs_20",),
)

GENERALIZATION_SCENARIO = ScenarioConfig(
    name="generalization",
    description="Train on year 1, evaluate on year 2 (unseen).",
    n_agents=(10,),
    train_year="year1",
    test_year="year2",
    measures=("train_test_gap",),
    notes="Requires multi-year schema coverage (Iquitos 2023-2025 supports year splits).",
)

SCENARIO_CATALOG: Mapping[str, ScenarioConfig] = {
    BASE_SCENARIO.name: BASE_SCENARIO,
    SCALABILITY_SCENARIO.name: SCALABILITY_SCENARIO,
    ROBUSTNESS_SCENARIO.name: ROBUSTNESS_SCENARIO,
    GENERALIZATION_SCENARIO.name: GENERALIZATION_SCENARIO,
}


@dataclass(frozen=True)
class EmpiricalProtocol:
    """Shared experimental budget for fair algorithm comparison."""

    algorithms: Tuple[str, ...] = ("HAPPO", "MAAC", "MASAC", "MATD3")
    n_seeds: int = 12
    equal_step_budget: bool = True
    step_budget: int | None = None
    optimizer: str = "Adam"
    hidden_sizes: Tuple[int, ...] = (256, 256)
    scenarios: Tuple[str, ...] = tuple(SCENARIO_CATALOG.keys())
    significance_alpha: float = 0.05
    extras: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


DEFAULT_PROTOCOL = EmpiricalProtocol()


def list_scenarios() -> Sequence[Dict[str, object]]:
    return [cfg.as_dict() for cfg in SCENARIO_CATALOG.values()]
