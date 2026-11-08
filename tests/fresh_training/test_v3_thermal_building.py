"""SPEC-016 D-V6-52/53, FR-016.4: the air conditioning is an action of the v3 layer, with ISO 13790 5R1C dynamics.

citylearn.v3.thermal.ISO13790Building takes the cooling action as the fraction of the device's nominal electric
power; the delivered cooling (latent first, then sensible) drives the 5R1C model that sets the indoor temperature.
"""
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SPLIT = REPO/CAMPAIGN['dataset_root']/'splits/train_2023'
STEPS = 14                                     # from midnight into the afternoon of 1 January


def _thermal_schema(target: Path) -> Path:
    shutil.copytree(SPLIT, target)
    schema = json.loads((target/'schema.json').read_text(encoding='utf-8'))
    schema['actions']['cooling_device'] = {'active': True}
    for building in schema['buildings'].values():
        if building.get('type') == 'citylearn.v3.thermal.ISO13790Building':
            continue
        building['type'] = 'citylearn.v3.thermal.ISO13790Building'
        building['dynamics'] = {'type': 'citylearn.v3.thermal.ISO13790Dynamics', 'attributes': {
            'floor_area_m2': 2000.0, 'envelope_w_m2k': 1.5, 'solar_aperture_fraction': 0.05,
            'ventilation_m3_s': 0.5, 'mass_class': 'medium', 'set_point': 24.0, 'pressure_kpa': 100.0,
            'electric_gain_fraction': 0.2}}
    (target/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    return target/'schema.json'


def _run(schema, cooling):
    from citylearn.v3.environment import make_citylearn_v3_env
    env = make_citylearn_v3_env(schema_path=schema, scenario='E1', seed=0, episode_time_steps=STEPS + 2)
    try:
        env.reset()
        core = env.env
        while not hasattr(core, 'buildings'):
            core = core.env
        actions = {}
        for agent, names in zip(env.possible_agents, core.action_names):
            a = np.zeros(env.action_space(agent).shape, dtype=np.float32)
            a[names.index('cooling_device')] = cooling
            actions[agent] = a
        for _ in range(STEPS):
            env.step(actions)
        b6 = next(b for b in core.buildings if b.name == 'Building_6')
        t = b6.time_step
        return (list(core.action_names), float(b6.indoor_dry_bulb_temperature[t - 1]),
                float(np.sum(b6.cooling_electricity_consumption[:t])))
    finally:
        env.close()


@pytest.fixture(scope='module')
def schema(tmp_path_factory):
    return _thermal_schema(tmp_path_factory.mktemp('thermal')/'train_2023')


def test_every_agent_has_its_air_conditioning_action(schema):
    names, *_ = _run(schema, 0.0)
    assert all('cooling_device' in row for row in names)


def test_cooling_lowers_the_indoor_temperature_and_costs_electricity(schema):
    _, warm, off_kwh = _run(schema, 0.0)
    _, cool, on_kwh = _run(schema, 1.0)
    assert off_kwh == pytest.approx(0.0, abs=1e-6)
    assert on_kwh > 0.0
    assert cool < warm - 1.0


def test_the_dynamics_follow_the_iso_step_of_the_v3_module(schema):
    from citylearn.v3 import thermal as th
    p = th.iso13790_parameters(floor_area_m2=2000.0, envelope_w_m2k=1.5, solar_aperture_fraction=0.05,
                               ventilation_w_k=th.ventilation_conductance_w_k(0.5), mass_class='medium')
    dynamics = th.ISO13790Dynamics(floor_area_m2=2000.0, envelope_w_m2k=1.5, solar_aperture_fraction=0.05,
                                   ventilation_m3_s=0.5, mass_class='medium', set_point=24.0, pressure_kpa=100.0)
    assert dynamics.params == p and dynamics.theta_m == 24.0
    dynamics.theta_m = 30.0
    dynamics.reset()
    assert dynamics.theta_m == 24.0


def test_the_reward_penalises_discomfort_only_when_occupied():
    from citylearn.v3.reward import CityLearnV3MADRLRewardFunction
    reward = CityLearnV3MADRLRewardFunction({'central_agent': False, 'seconds_per_time_step': 3600},
                                            algorithm='MATD3', scenario='E1')
    base = {'net_electricity_consumption': 10.0, 'electricity_pricing': 0.1, 'carbon_intensity': 0.4,
            'indoor_dry_bulb_temperature_cooling_set_point': 24.0, 'comfort_band': 2.0}
    rows = {}
    for label, extra in {'hot_occupied': {'indoor_dry_bulb_temperature': 28.0, 'occupant_count': 50.0},
                         'hot_empty': {'indoor_dry_bulb_temperature': 28.0, 'occupant_count': 0.0},
                         'comfortable': {'indoor_dry_bulb_temperature': 25.5, 'occupant_count': 50.0}}.items():
        reward.reset()
        reward.calculate([{**base, **extra}])
        rows[label] = reward._last_component_breakdown['components'][0]
    assert rows['hot_occupied']['raw_comfort_excess_c'] == pytest.approx(2.0)          # 28 - (24 + 2)
    assert rows['hot_occupied']['comfort'] == pytest.approx(-reward.profile['comfort_weight']*1.0)
    assert rows['hot_empty']['comfort'] == 0.0 and rows['hot_empty']['comfort_applicable'] is False
    assert rows['comfortable']['comfort'] == 0.0
    assert rows['hot_occupied']['local_reward'] < rows['comfortable']['local_reward']
