"""Baseline KPIs from CityLearn's Rule-Based Controller for comparison."""
from pathlib import Path
from typing import Dict


def compute_rbc_baseline(schema_path: Path, episode_time_steps: int = 8760) -> Dict[str, float]:
    """Run CityLearn RBC over the same dataset and return KPIs.

    Requires CityLearn environment; deferred to campaign execution.
    """
    raise NotImplementedError(
        "RBC baseline computation requires CityLearn runtime. "
        "Run from the campaign environment with the Iquitos dataset."
    )
