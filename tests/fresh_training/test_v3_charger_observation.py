"""SPEC-016 D-V6-49: charger observations aggregated per vehicle class in the CityLearn v3 layer.

Each socket stays its own action, but an agent observes, per vehicle class of its building, the share of sockets
occupied, the mean SOC connected, the pending energy, the next departure and the share incoming, instead of seven
values per socket. The same for the 4 MADRL (every backend adapter goes through the v3 Dec-POMDP).
"""
from pathlib import Path

import numpy as np
import pytest
import yaml

from citylearn.v3.environment import make_citylearn_v3_env

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SCHEMA = REPO/CAMPAIGN['dataset_root']/'splits/train_2023/schema.json'
FEATURES = ('occupied_fraction', 'soc_mean', 'pending_kwh', 'next_departure_h', 'incoming_fraction')


@pytest.fixture(scope='module')
def env():
    environment = make_citylearn_v3_env(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=48)
    yield environment
    environment.close()


def test_every_agent_observes_its_classes_not_each_socket(env):
    sizes = [env.observation_space(a).shape[0] for a in env.possible_agents]
    assert max(sizes) <= 40, sizes                                   # 355 with one observation per socket
    names = env.observation_names('Building_6')
    assert not any('socket' in n for n in names)
    for kind in ('moto', 'mototaxi', 'pickup'):
        assert all(f'ev_{kind}_{f}' in names for f in FEATURES)
    actions = env.action_space('Building_6').shape[0]
    b6 = next(b for b in env.env.buildings if b.name == 'Building_6')
    assert actions >= len(b6.electric_vehicle_chargers)              # every socket is still an action


def test_aggregates_match_the_chargers_of_the_building(env):
    observations, _ = env.reset()
    zero = {a: np.zeros(env.action_space(a).shape, dtype=np.float32) for a in env.possible_agents}
    for _ in range(10):                                              # into the morning arrivals
        observations, *_ = env.step(zero)
    names = env.observation_names('Building_6')
    values = dict(zip(names, observations['Building_6']))
    b6 = next(b for b in env.env.buildings if b.name == 'Building_6')
    sockets = [c for c in b6.electric_vehicle_chargers if '_moto_' in c.charger_id]
    t = b6.time_step
    connected = [c for c in sockets if c.charger_simulation.electric_vehicle_charger_state[t] == 1]
    expected = len(connected)/len(sockets)
    normalized = env.observation_space('Building_6').high.max() <= 1.0 + 1e-6
    assert values['ev_moto_occupied_fraction'] == pytest.approx(expected, abs=1e-5)
    if connected and not normalized:
        socs = [float(c.connected_electric_vehicle.battery.soc[t]) for c in connected]
        assert values['ev_moto_soc_mean'] == pytest.approx(np.mean(socs), abs=1e-4)


def test_the_operational_gate_runs_the_4_backends_on_the_aggregated_observation():
    from citylearn.v3.backend_contract import operational_gate
    result = operational_gate(SCHEMA, steps=1, seed=0)
    assert result.passed, result.failures
    assert set(result.backends) >= {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
