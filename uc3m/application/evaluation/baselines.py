"""Baseline KPIs from CityLearn's Rule-Based Controller for comparison."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from citylearn.citylearn import CityLearnEnv
from citylearn.agents.rbc import BasicElectricVehicleRBC_ReferenceController


def compute_rbc_baseline(
    schema_path: Path,
    episode_time_steps: int = 8760,
) -> Dict[str, Any]:
    """Run CityLearn EV-aware RBC over the Iquitos dataset and return KPIs.

    Uses ``BasicElectricVehicleRBC_ReferenceController`` which applies
    hour-of-use rules for battery charge/discharge and max-rate EV
    charging on connection — the standard uncoordinated baseline.
    """
    env = CityLearnEnv(
        schema=str(schema_path),
        central_agent=False,
    )
    agent = BasicElectricVehicleRBC_ReferenceController(env)

    observations = env.reset()
    done = False
    step = 0

    while not done and step < episode_time_steps:
        actions = agent.predict(observations)
        observations, rewards, done, truncated, info = env.step(actions)
        step += 1

    kpis: Dict[str, Any] = {}
    eval_data = env.evaluate()
    for row in eval_data.to_dict("records"):
        name = row.get("name") or row.get("cost_function")
        if name and "value" in row:
            kpis[str(name)] = float(row["value"])

    kpis["_meta"] = {
        "agent": "BasicElectricVehicleRBC_ReferenceController",
        "schema": str(schema_path),
        "episode_time_steps": episode_time_steps,
        "total_steps": step,
    }
    return kpis
