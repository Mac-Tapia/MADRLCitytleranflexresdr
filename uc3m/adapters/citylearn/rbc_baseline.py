"""CityLearn RBC baseline adapter — isolates CityLearn imports from the domain."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict

from citylearn.citylearn import CityLearnEnv
from citylearn.agents.rbc import BasicElectricVehicleRBC_ReferenceController


def run_rbc_baseline(
    schema_path: Path,
    episode_time_steps: int = 8760,
) -> Dict[str, Any]:
    """Run CityLearn EV-aware RBC over the given schema and return KPIs.

    Uses ``BasicElectricVehicleRBC_ReferenceController`` which applies
    hour-of-use rules for battery charge/discharge and max-rate EV
    charging on connection — the standard uncoordinated baseline.
    """
    if type(episode_time_steps) is not int or episode_time_steps < 1:
        raise ValueError('episode_time_steps must be a positive integer')
    env = CityLearnEnv(
        schema=str(schema_path),
        central_agent=False,
        episode_time_steps=episode_time_steps,
        random_episode_split=False,
        rolling_episode_split=False,
    )
    try:
        agent = BasicElectricVehicleRBC_ReferenceController(env)

        observations, _ = env.reset()
        done = False
        truncated = False
        step = 0

        while not (done or truncated) and step < episode_time_steps:
            actions = agent.predict(observations)
            observations, rewards, done, truncated, info = env.step(actions)
            step += 1

        kpis: Dict[str, Any] = {}
        eval_data = env.evaluate()
        for row in eval_data.to_dict("records"):
            if str(row.get('level', '')).casefold() != 'district':
                continue
            name = row.get('cost_function')
            if name and 'value' in row:
                name = str(name)
                if name in kpis:
                    raise ValueError(f'duplicate district KPI: {name}')
                value = row['value']
                kpis[name] = float(value) if value is not None and math.isfinite(float(value)) else None

        kpis["_meta"] = {
            "agent": "BasicElectricVehicleRBC_ReferenceController",
            "schema": str(schema_path),
            "kpi_level": "district",
            "episode_time_steps": episode_time_steps,
            "total_steps": step,
            "terminated": bool(done),
            "truncated": bool(truncated),
        }
        return kpis
    finally:
        env.close()
