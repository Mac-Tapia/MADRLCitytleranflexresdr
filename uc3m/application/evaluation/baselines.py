"""Baseline KPIs from a rule-based controller for comparison against MADRL."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

BaselineRunner = Callable[[Path, int], Dict[str, Any]]


def compute_rbc_baseline(
    schema_path: Path,
    runner: BaselineRunner,
    episode_time_steps: int = 8760,
) -> Dict[str, Any]:
    """Run the injected RBC runner (e.g. ``uc3m.adapters.citylearn.rbc_baseline.run_rbc_baseline``)."""
    kpis = runner(Path(schema_path), int(episode_time_steps))
    if "_meta" not in kpis:
        raise ValueError("baseline runner must return a '_meta' provenance entry")
    return kpis
