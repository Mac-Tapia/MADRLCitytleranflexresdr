"""SPEC-016 FR-016.11: the CityLearn v3 tuple of the active campaign holds link by link.

term of the reward -> axis -> KPI of the catalog; axis -> primary KPI measured; action -> equipment of the building;
observation read by the reward -> O_i. Falsified inputs make each check fail (the contract is not vacuous).
"""
import json
from pathlib import Path

import pytest
import yaml

from uc3m.application.evaluation import tuple_contract as tc

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SCHEMA = REPO/CAMPAIGN['dataset_root']/'splits/train_2023/schema.json'
CATALOG = yaml.safe_load((REPO/'configs/evaluation/kpis.yaml').read_text(encoding='utf-8'))
POLICIES = yaml.safe_load((REPO/'configs/objective_policies.yaml').read_text(encoding='utf-8'))


def _reward():
    from citylearn.v3.reward import CITYLEARN_V3_REWARD_TERMS, CityLearnV3MADRLRewardFunction
    reward = CityLearnV3MADRLRewardFunction({'central_agent': False, 'seconds_per_time_step': 3600},
                                            algorithm='MATD3', scenario='E1')
    p = reward.profile
    return CITYLEARN_V3_REWARD_TERMS, {**p['flex_subweights'], **p['carbon_subweights'], **p['cost_subweights']}


def test_every_reward_term_has_an_axis_and_a_kpi_that_names_it_back():
    terms, weights = _reward()
    assert tc.term_violations(terms, weights, CATALOG) == []


def test_a_term_without_kpi_or_a_weighted_pending_term_breaks_the_contract():
    terms, weights = _reward()
    fake = dict(terms, cost_ghost=('cost', 'no_such_kpi', 'falsified', 'defined'))
    assert any('cost_ghost' in v and 'not a thesis indicator' in v
               for v in tc.term_violations(fake, {**weights, 'cost_ghost': 0.1}, CATALOG))
    assert any('dso_excess' in v for v in tc.term_violations(terms, {**weights, 'dso_excess': 0.2}, CATALOG))
    orphan = {k: v for k, v in terms.items() if k != 'cost_peak_billing'}
    assert any('cost_peak_billing' in v for v in tc.term_violations(orphan, weights, CATALOG))


def test_every_axis_has_a_measured_primary_kpi_and_the_scenarios_weight_those_axes():
    assert tc.axis_violations(CATALOG, POLICIES) == []
    broken = dict(CATALOG, axes={**CATALOG['axes'], 'energy_cost': []})
    assert any('energy_cost' in v for v in tc.axis_violations(broken, POLICIES))
    skewed = {'policies': {'E9': {'weights': {'flexibility': 1.0}}}}
    assert any('E9' in v for v in tc.axis_violations(CATALOG, skewed))


def test_actions_and_observations_are_checked_against_the_building():
    assert tc.action_violations('B', ['electrical_storage', 'electric_vehicle_storage_c1'], chargers=['c1'],
                                has_storage=True, has_cooling=False) == []
    found = tc.action_violations('B', ['washing_machine_1', 'electric_vehicle_storage_c9'], chargers=['c1'],
                                 has_storage=True, has_cooling=True, deferred={})
    assert any('washing_machine_1' in v for v in found) and any('c9' in v for v in found)
    assert any('BESS has no action' in v for v in found) and any('air conditioning' in v for v in found)
    assert any('c1 has no action' in v for v in found)
    assert tc.observation_violations('B', ['hour'], billed=True)
    # D-V6-51: the air conditioning without action is accepted only through the declared deferral.
    assert tc.DEFERRED_ACTIONS == {'cooling_device': 'D-V6-51'}
    assert tc.action_violations('B', ['electrical_storage'], chargers=[], has_storage=True, has_cooling=True) == []
    assert any('without air conditioning' in v for v in tc.action_violations(
        'B', ['electrical_storage', 'cooling_device'], chargers=[], has_storage=True, has_cooling=False))


@pytest.fixture(scope='module')
def active():
    from citylearn.v3.environment import make_citylearn_v3_env
    env = make_citylearn_v3_env(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=4)
    core = env.env
    while not hasattr(core, 'buildings'):
        core = core.env
    yield env, core, json.loads(SCHEMA.read_text(encoding='utf-8'))
    env.close()


def test_every_action_of_the_active_dataset_is_an_equipment_of_its_building(active):
    env, core, schema = active
    violations = []
    for building, names in zip(core.buildings, core.action_names):
        declared = schema['buildings'][building.name]
        cooling = declared.get('cooling_device') or {}
        has_cooling = float((cooling.get('attributes') or {}).get('nominal_power') or 0.0) > 0.0 or \
            bool(cooling.get('autosize'))
        storage = declared.get('electrical_storage') or {}
        has_storage = float((storage.get('attributes') or {}).get('capacity') or 0.0) > 0.0
        violations += tc.action_violations(building.name, names,
                                           chargers=[c.charger_id for c in building.electric_vehicle_chargers or []],
                                           has_storage=has_storage, has_cooling=has_cooling)
    assert violations == []


def test_every_observation_the_reward_reads_is_in_each_agents_observation(active):
    env, core, schema = active
    billed = schema.get('dataset_version', 'v6') == 'v6' or any('bill_tariff' in b for b in schema['buildings'].values())
    violations = []
    for agent in env.possible_agents:
        violations += tc.observation_violations(agent, env.observation_names(agent), billed=billed)
    assert violations == []
