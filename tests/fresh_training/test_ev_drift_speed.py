"""The indexed EV drift step reproduces the original O(EVs x chargers) loop exactly, and fast.

simulate_unconnected_ev_soc was 91% of a native micro-training (1850 EVs x 185
chargers scanned per step, ~18 s/step). Only chargers whose current or next EV
id is the vehicle can act on it, so indexing them per vehicle, in the original
charger order, must give the same state of charge, the same RNG draws and the
same step results.
"""
import copy
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pytest
import yaml

from citylearn.citylearn import CityLearnEnv
from citylearn.internal.runtime import CityLearnRuntimeService

REPO = Path(__file__).resolve().parents[2]
# A simulator speed test, not a campaign test: the fleet is built here on the active split, with the
# 1850 EVs and 185 chargers that made the original loop 91% of a step.
SPLIT = REPO/yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))['dataset_root']/'splits/train_2023'
EVS, CHARGERS = 1850, 185
STEPS = 4


def reference_unconnected_ev_soc(self):
    """Verbatim copy of the original loop (CityLearn d8942804), used only as the oracle."""
    env = self.env
    random_state = getattr(env, '_ev_drift_random_state', None)
    if random_state is None:
        episode_index = int(getattr(getattr(env, 'episode_tracker', None), 'episode', 0))
        random_state = np.random.RandomState(int(env.random_seed) + episode_index)
        env._ev_drift_random_state = random_state
    t = env.time_step
    if t + 1 >= env.episode_tracker.episode_time_steps:
        return
    for ev in env.electric_vehicles:
        ev_id = ev.name
        found_in_charger = False
        for building in env.buildings:
            for charger in building.electric_vehicle_chargers or []:
                sim = charger.charger_simulation
                curr_id = sim.electric_vehicle_id[t] if t < len(sim.electric_vehicle_id) else ''
                next_id = sim.electric_vehicle_id[t + 1] if t + 1 < len(sim.electric_vehicle_id) else ''
                curr_state = sim.electric_vehicle_charger_state[t] if t < len(sim.electric_vehicle_charger_state) else np.nan
                next_state = (sim.electric_vehicle_charger_state[t + 1]
                              if t + 1 < len(sim.electric_vehicle_charger_state) else np.nan)
                if isinstance(curr_id, str) and curr_id == ev_id and curr_state == 1:
                    found_in_charger = True
                    break
                is_connecting = isinstance(next_id, str) and next_id == ev_id and next_state == 1 and curr_state != 1
                is_incoming = isinstance(curr_id, str) and curr_id == ev_id and curr_state == 2
                if is_connecting:
                    found_in_charger = True
                    if is_incoming:
                        soc = (sim.electric_vehicle_estimated_soc_arrival[t]
                               if t < len(sim.electric_vehicle_estimated_soc_arrival) else np.nan)
                    else:
                        soc = (sim.electric_vehicle_estimated_soc_arrival[t + 1]
                               if t + 1 < len(sim.electric_vehicle_estimated_soc_arrival) else np.nan)
                    if 0 <= soc <= 1:
                        ev.battery.force_set_soc(soc)
                    break
            if found_in_charger:
                break
        if not found_in_charger and t > 0:
            last_soc = ev.battery.soc[t - 1]
            drift_std = self._ev_unconnected_drift_std(env.seconds_per_time_step)
            variability = np.clip(random_state.normal(1.0, drift_std), 0.6, 1.4)
            ev.battery.force_set_soc(np.clip(last_soc*variability, 0.0, 1.0))


@pytest.fixture(scope='module')
def fleet_schema(tmp_path_factory):
    # Every charger serves one vehicle of its own on the sessions of a real charger file; the other nine
    # vehicles of each ten are never connected, so they drift. Chargers go round robin over the buildings.
    # The oracle is CityLearn's CSV arrival and drift; the endogenous mode of the active dataset (D-V6-41) keeps
    # the SOC instead and has its own test (test_write_ev_v6.py).
    out = tmp_path_factory.mktemp('ev_drift')/'split'
    shutil.copytree(SPLIT, out, ignore=shutil.ignore_patterns('charger_*.csv'))
    schema = json.loads((out/'schema.json').read_text(encoding='utf-8'))
    assert schema.pop('electric_vehicle_arrival_soc') == 'endogenous'
    charger = next(iter(schema['buildings']['Building_1']['chargers'].values()))
    rows = [line.split(',') for line in (SPLIT/charger['charger_simulation']).read_text(encoding='utf-8').splitlines()]
    column = rows[0].index('electric_vehicle_id')
    vehicle = next(row[column] for row in rows[1:] if row[column] != 'NONE')
    schema['electric_vehicles_def'] = {f'EV_{i:04d}': copy.deepcopy(schema['electric_vehicles_def'][vehicle])
                                       for i in range(EVS)}
    buildings = list(schema['buildings'].values())
    for building in buildings:
        building['chargers'] = {}
    for i in range(CHARGERS):
        ev = f'EV_{i*(EVS//CHARGERS):04d}'
        lines = [','.join(ev if k == column and n and cell != 'NONE' else cell for k, cell in enumerate(row))
                 for n, row in enumerate(rows)]
        (out/f'charger_{i:03d}.csv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        buildings[i % len(buildings)]['chargers'][f'charger_{i:03d}'] = dict(copy.deepcopy(charger),
                                                                             charger_simulation=f'charger_{i:03d}.csv')
    (out/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    return out/'schema.json'


def _run(monkeypatch, schema, implementation):
    if implementation is not None:
        monkeypatch.setattr(CityLearnRuntimeService, 'simulate_unconnected_ev_soc', implementation)
    env = CityLearnEnv(str(schema), random_seed=901)
    env.reset()
    started = time.perf_counter()
    rewards = []
    for _ in range(STEPS):
        result = env.step([[0.0]*len(space.low) for space in env.action_space])
        rewards.append(np.asarray(result[1], dtype=float))
    elapsed = time.perf_counter() - started
    socs = {ev.name: np.asarray(ev.battery.soc[:STEPS + 1], dtype=float) for ev in env.electric_vehicles}
    power = np.asarray([b.net_electricity_consumption[:STEPS] for b in env.buildings], dtype=float)
    monkeypatch.undo()
    return socs, power, rewards, elapsed


def test_indexed_drift_matches_reference_and_is_faster(monkeypatch, fleet_schema):
    ref_socs, ref_power, ref_rewards, ref_time = _run(monkeypatch, fleet_schema, reference_unconnected_ev_soc)
    socs, power, rewards, new_time = _run(monkeypatch, fleet_schema, None)
    assert set(socs) == set(ref_socs) and len(socs) == EVS
    for name, values in ref_socs.items():
        np.testing.assert_array_equal(socs[name], values, err_msg=name)
    np.testing.assert_array_equal(power, ref_power)
    for got, expected in zip(rewards, ref_rewards):
        np.testing.assert_array_equal(got, expected)
    assert new_time < ref_time/5, (new_time, ref_time)
