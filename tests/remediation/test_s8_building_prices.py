"""S8 of the dataset substitution gate: no building is priced with another building's tariff.

iquitos_v3 has 17 tariffs, so a first-building shortcut stops being harmless there.
"""
import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from uc3m.adapters.citylearn.frozen_adapters import _price_signal_deviation
from uc3m.adapters.citylearn.policy_inference import _physical_trace
from uc3m.reward import term_telemetry as tt

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO/'data/campaigns/iquitos_v3'
SPLIT = 'train_2023'


def _env():
    from citylearn.citylearn import CityLearnEnv
    env = CityLearnEnv(str(CAMPAIGN/'splits'/SPLIT/'schema.json'))
    env.reset()
    env.step([[0.0 for _ in names] for names in env.action_names])
    return env


def _file_price(building, step):
    schema = json.loads((CAMPAIGN/'splits'/SPLIT/'schema.json').read_text(encoding='utf-8'))
    path = CAMPAIGN/'splits'/SPLIT/schema['buildings'][building]['pricing']
    with open(path, newline='', encoding='utf-8') as stream:
        return float(list(csv.DictReader(stream))[step]['electricity_pricing'])


def test_campaign_really_has_different_tariffs():
    assert _file_price('Building_1', 0) != _file_price('Building_17', 0)


def test_observation_price_is_the_building_own_tariff():
    env = _env()
    for building in env.buildings:
        assert float(building.observations(normalize=False)['electricity_pricing']) == \
            pytest.approx(_file_price(building.name, env.time_step))


def test_trace_keeps_each_tariff_and_invents_no_district_price():
    env = _env()
    trace, _, _ = _physical_trace(env, 1, CAMPAIGN, SPLIT)
    assert 'price' not in trace.district_series
    for building in env.buildings:
        assert trace.series_by_building[building.name]['price'][0] == pytest.approx(_file_price(building.name, 0))


def test_trace_refuses_different_carbon_series():
    env = _env()
    env.buildings[-1].carbon_intensity.carbon_intensity = env.buildings[-1].carbon_intensity.carbon_intensity*2
    with pytest.raises(ValueError, match='carbon'):
        _physical_trace(env, 1, CAMPAIGN, SPLIT)


def _trace(price_a, price_b, district_price=None):
    series = {name: {'net_power': [1.0, 2.0, 3.0], 'price': price}
              for name, price in (('B1', price_a), ('B2', price_b))}
    district = {} if district_price is None else {'price': district_price}
    return SimpleNamespace(timestamps=('a', 'b', 'c'), building_ids=('B1', 'B2'), series_by_building=series,
                           district_series=district)


def test_price_response_is_unavailable_with_several_tariffs():
    assert _price_signal_deviation(_trace([0.1, 0.2, 0.3], [0.2, 0.3, 0.4])) is None


def test_price_response_uses_the_single_tariff_when_shared():
    shared = [0.1, 0.2, 0.3]
    assert _price_signal_deviation(_trace(shared, shared, district_price=shared)) is not None


def _component(**drop):
    component = {'net': 1.0, 'baseline_net': 1.0, 'price': 0.1, 'carbon_intensity': 0.5}
    return {k: v for k, v in component.items() if k not in drop}


@pytest.mark.parametrize('missing', ['price', 'carbon_intensity', 'net'])
def test_telemetry_does_not_turn_a_missing_signal_into_zero(missing):
    with pytest.raises(ValueError, match=missing):
        tt.exogenous_signals(_component(**{missing: True}))


def test_telemetry_reads_present_signals():
    assert tt.exogenous_signals(_component()) == {'net': 1.0, 'baseline': 1.0, 'price': 0.1, 'carbon': 0.5}
