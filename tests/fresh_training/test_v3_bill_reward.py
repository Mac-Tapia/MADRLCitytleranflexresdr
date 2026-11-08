"""SPEC-016 D-V6-8 / SPEC-015 D04: the reward pays the bill, energy plus the demand charge of the 18:00-23:00 block.

The energy part already enters through ``cost_net`` (the bill energy rate equals ``pricing_<b>.csv``). The demand
part is ``cost_peak_billing``: in a block hour, demand rate x max(0, P - peak of the month so far in the block),
whose monthly sum equals demand rate x block peak of the month (oracle ``bill_tariff.incremental_bill_cost``).
Owner decision 2026-11-07: the cost axis is split in thirds (cost_net, cost_delta, cost_peak_billing).

The peak of the month lives in one tracker of the v3 layer (``citylearn.v3.bill``), read by the reward and by the
observation of each agent, so the reward is Markovian in what the agent observes (FR-016.10).
"""
import csv
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import yaml

from uc3m.application.dataset.bill_tariff import incremental_bill_cost

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
ROOT = REPO/CAMPAIGN['dataset_root']
SPLIT = ROOT/'splits/train_2023'
FIELDS = ('bill_month_block_peak_kw', 'bill_in_peak_block', 'bill_demand_usd_kw_month')
STEPS = 30          # 00:00 to 06:00 of day 2: two 18:00-23:00 blocks of day 1 are inside


def _reward():
    from citylearn.v3.reward import CityLearnV3MADRLRewardFunction
    return CityLearnV3MADRLRewardFunction({'central_agent': False, 'seconds_per_time_step': 3600},
                                          algorithm='MATD3', scenario='E3')


@pytest.fixture(scope='module')
def schema_dir(tmp_path_factory):
    """The train split with its bill tariff files, as the builder writes them (rows of 2023)."""
    target = tmp_path_factory.mktemp('bill')/'train_2023'
    schema = json.loads((SPLIT/'schema.json').read_text(encoding='utf-8'))
    if all('bill_tariff' in b for b in schema['buildings'].values()):
        shutil.copytree(SPLIT, target)
        return target
    shutil.copytree(SPLIT, target)
    for key, building in schema['buildings'].items():
        name = f'bill_tariff_{key}.csv'
        with open(ROOT/'dataset'/name, newline='', encoding='utf-8') as stream:
            rows = list(csv.reader(stream))
        with open(target/name, 'w', newline='', encoding='utf-8') as stream:
            csv.writer(stream, lineterminator='\n').writerows(rows[:8761])
        building['bill_tariff'] = name
    (target/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    return target


def test_the_cost_axis_is_split_in_thirds_and_the_demand_term_is_defined():
    from citylearn.v3.reward import CITYLEARN_V3_REWARD_TERMS
    weights = _reward().profile['cost_subweights']
    assert weights['cost_net'] == weights['cost_delta'] == weights['cost_peak_billing'] == pytest.approx(1/3)
    assert weights['cost_price_signal'] == 0.0
    assert CITYLEARN_V3_REWARD_TERMS['cost_peak_billing'][3] == 'defined'


def test_the_demand_term_follows_the_bill_oracle_and_resets_each_month():
    reward = _reward()
    power = [5.0, 8.0, 6.0, 12.0, 3.0]
    block = [1, 1, 1, 1, 1]
    month = [1, 1, 1, 2, 2]
    rate, peak, last = 13.0, 0.0, None
    total = {}
    for p, b, m in zip(power, block, month):
        if m != last:
            peak, last = 0.0, m
        _, new_peak = incremental_bill_cost(p, energy_usd_kwh=0.0, demand_usd_kw_month=rate,
                                            peak_so_far_kw=peak, in_block=bool(b))
        expected = rate*max(0.0, p - peak) if b else 0.0
        reward.calculate([{'net_electricity_consumption': p, 'electricity_pricing': 0.1, 'carbon_intensity': 0.4,
                           'bill_demand_usd_kw_month': rate, 'bill_in_peak_block': b,
                           'bill_month_block_peak_kw': peak}])
        component = reward._last_component_breakdown['components'][0]
        assert component['raw_cost_peak_billing'] == pytest.approx(expected)
        increment = max(0.0, p - peak) if b else 0.0                # P-V6-24: kW over the month peak / 25 kW
        assert component['norm_cost_peak_billing'] == pytest.approx(increment/reward.profile['peak_reference_kw'])
        total[m] = total.get(m, 0.0) + component['raw_cost_peak_billing']
        peak = new_peak
    assert total == {1: pytest.approx(13.0*8.0), 2: pytest.approx(13.0*12.0)}   # rate x block peak of the month


def test_without_a_bill_tariff_the_demand_term_is_not_applicable_and_the_old_weights_hold():
    """A schema without bill tariffs (v5, BAEDA): cost_net and cost_delta keep 1/2 each, never a silent zero third."""
    reward = _reward()
    reward.calculate([{'net_electricity_consumption': 10.0, 'electricity_pricing': 0.2, 'carbon_intensity': 0.4}])
    component = reward._last_component_breakdown['components'][0]
    assert component['cost_peak_billing_applicable'] is False
    expected = -(0.5*component['bounded_cost_net'] + 0.5*component['bounded_cost_delta'])
    assert component['cost'] == pytest.approx(expected)


def test_a_partial_bill_tariff_declaration_is_an_error(schema_dir, tmp_path):
    from citylearn.v3.environment import make_citylearn_v3_env
    target = tmp_path/'partial'
    shutil.copytree(schema_dir, target)
    schema = json.loads((target/'schema.json').read_text(encoding='utf-8'))
    schema['buildings']['Building_2'].pop('bill_tariff')
    (target/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    with pytest.raises(ValueError, match='bill_tariff'):
        make_citylearn_v3_env(schema_path=target/'schema.json', scenario='E3', seed=0, episode_time_steps=4)


@pytest.fixture(scope='module')
def rollout(schema_dir):
    from citylearn.v3.environment import make_citylearn_v3_env
    env = make_citylearn_v3_env(schema_path=schema_dir/'schema.json', scenario='E3', seed=0,
                                episode_time_steps=STEPS + 2)
    observations, _ = env.reset()
    base = env.env
    while hasattr(base, 'env') and not hasattr(base, 'buildings'):
        base = base.env
    history = [observations]
    breakdowns, nets = [], []
    zero = {a: np.zeros(env.action_space(a).shape, dtype=np.float32) for a in env.possible_agents}
    assert base.time_step == 0
    for t in range(STEPS):
        observations, *_ = env.step(zero)
        history.append(observations)
        breakdowns.append(base.reward_function._last_component_breakdown['components'])
        nets.append([float(b.net_electricity_consumption[t]) for b in base.buildings])
    yield env, base, history, breakdowns, nets
    env.close()


def test_every_agent_observes_the_bill_state(rollout):
    env, *_ = rollout
    for agent in env.possible_agents:
        names = env.observation_names(agent)
        assert all(f in names for f in FIELDS), agent
        assert len(names) == env.observation_space(agent).shape[0]


def test_reward_and_observation_share_the_month_peak_of_the_tariff_file(rollout, schema_dir):
    env, base, history, breakdowns, nets = rollout
    agent, index = 'Building_6', env.possible_agents.index('Building_6')
    with open(schema_dir/'bill_tariff_Building_6.csv', newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    names = env.observation_names(agent)
    normalized = env.observation_space(agent).high.max() <= 1.0 + 1e-6
    peak = 0.0
    for t in range(STEPS):
        row = rows[t]
        block = int(row['peak_block'])
        rate = float(row['demand_usd_kw_month'])
        before = dict(zip(names, history[t][agent]))
        assert before['bill_in_peak_block'] == pytest.approx(block)
        if not normalized:
            assert before['bill_month_block_peak_kw'] == pytest.approx(peak, abs=1e-4)
            assert before['bill_demand_usd_kw_month'] == pytest.approx(rate, rel=1e-6)
        p = nets[t][index]
        _, new_peak = incremental_bill_cost(p, energy_usd_kwh=0.0, demand_usd_kw_month=rate, peak_so_far_kw=peak,
                                            in_block=bool(block))
        component = breakdowns[t][index]
        assert component['cost_peak_billing_applicable'] is True
        assert component['raw_cost_peak_billing'] == pytest.approx(rate*max(0.0, p - peak) if block else 0.0,
                                                                   abs=1e-6)
        peak = new_peak
    assert peak > 0.0                                   # the 18:00-23:00 block of day 1 set a peak


def test_the_schema_references_every_bill_tariff_so_the_split_copies_it(tmp_path):
    """FR-016.7: the tariff lives in the dataset; the split only copies files the schema references."""
    from uc3m.application.dataset import bill_tariff as bt
    from uc3m.application.dataset.splits import _csv_references
    schema = {'buildings': {'Building_1': {}, 'Building_2': {}}}
    written = {1: tmp_path/'bill_tariff_Building_1.csv', 2: tmp_path/'bill_tariff_Building_2.csv'}
    bt.declare_bill_tariff_files(schema, written)
    assert schema['buildings']['Building_2']['bill_tariff'] == 'bill_tariff_Building_2.csv'
    assert set(_csv_references(schema)) == {'bill_tariff_Building_1.csv', 'bill_tariff_Building_2.csv'}
    with pytest.raises(ValueError, match='Building_3'):
        bt.declare_bill_tariff_files(schema, {3: tmp_path/'bill_tariff_Building_3.csv'})
    source = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')
    assert 'declare_bill_tariff_files(' in source
