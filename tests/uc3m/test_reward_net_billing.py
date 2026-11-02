"""Net billing across the three axes, one reward module (owner decision 2026-11-01).

Owner: PV surplus is stored in the BESS or supplied to the public grid, never
wasted; exported energy is credited at the purchase price. The three axes see
the export consistently, in the reward and in the evaluation KPI:

- cost = building net consumption x price (export credited);
- CO2 = building net consumption x carbon intensity (export displaces thermal
  generation, negative contribution);
- flexibility on the bidirectional district net power: peak |P|, ramp |dP|,
  load factor 1 - mean|P|/max|P| (KPI only; the reward has no per-step LF term).

Whether to store or export is then decided by the weighted E1/E2/E3 compromise,
without fixed rules. The class lives in citylearn.v3.reward; the old dotted path
citylearn.reward_function.CityLearnV3MADRLRewardFunction is a lazy alias.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CITYLEARN = REPO/'CityLearn'
NEW_PATH = 'citylearn.v3.reward.CityLearnV3MADRLRewardFunction'
OLD_PATH = 'citylearn.reward_function.CityLearnV3MADRLRewardFunction'


def _resolve(dotted):
    module, name = dotted.rsplit('.', 1)
    return getattr(importlib.import_module(module), name)


# --- module location --------------------------------------------------------------------------------

def test_old_and_new_dotted_paths_are_one_class():
    new, old = _resolve(NEW_PATH), _resolve(OLD_PATH)
    assert new is old and new.__module__ == 'citylearn.v3.reward'
    from citylearn.reward_function import scenario_catalog_axis_weights as old_helper
    from citylearn.v3.reward import scenario_catalog_axis_weights as new_helper
    assert old_helper is new_helper


def test_single_implementation_and_canonical_paths():
    legacy = (CITYLEARN/'citylearn/reward_function.py').read_text(encoding='utf-8')
    assert 'class CityLearnV3MADRLRewardFunction' not in legacy
    assert 'def scenario_catalog_axis_weights' not in legacy
    assert 'class CityLearnV3MADRLRewardFunction' in (CITYLEARN/'citylearn/v3/reward.py').read_text(encoding='utf-8')
    from citylearn.v3.config import CityLearnV3ExperimentConfig
    assert CityLearnV3ExperimentConfig().reward_function == NEW_PATH
    environment = (CITYLEARN/'citylearn/v3/environment.py').read_text(encoding='utf-8')
    assert NEW_PATH in environment and OLD_PATH not in environment
    for algorithm in ('happo', 'masac', 'matd3', 'maac'):
        script = (CITYLEARN/'scripts'/f'train_citylearn_v3_{algorithm}.py').read_text(encoding='utf-8')
        assert OLD_PATH not in script


# --- reward: export credit on every axis ------------------------------------------------------------

def _reward():
    from citylearn.v3.reward import CityLearnV3MADRLRewardFunction
    return CityLearnV3MADRLRewardFunction({'central_agent': False}, algorithm='MATD3', scenario='E1')


def _obs(net, price=0.17, carbon=0.5):
    return {'net_electricity_consumption': net, 'electricity_pricing': price, 'carbon_intensity': carbon}


def test_export_is_credited_on_cost_and_co2():
    reward = _reward()
    reward.calculate([_obs(-6.0)])
    component = reward._last_component_breakdown['components'][0]
    assert component['raw_cost_net'] == pytest.approx(-6.0*0.17)
    assert component['raw_carbon_net'] == pytest.approx(-6.0*0.5)
    assert component['cost'] > 0 and component['carbon'] > 0     # credits, not penalties
    importing = _reward()
    importing.calculate([_obs(6.0)])
    mirror = importing._last_component_breakdown['components'][0]
    for term in ('bounded_cost_net', 'bounded_carbon_net'):
        assert component[term] == pytest.approx(-mirror[term])
    # The CI-weighted consumption counts import only (tesis D-VD.2 Dim3).
    assert component['raw_carbon_ci_import'] == 0.0 and mirror['raw_carbon_ci_import'] == pytest.approx(3.0)


def test_injection_peak_is_penalized_like_an_import_peak():
    def flex(power):
        reward = _reward()
        reward.calculate([_obs(power)])
        return reward._last_component_breakdown['components'][0]['flex']
    assert flex(-20.0) == pytest.approx(flex(20.0)) and flex(-20.0) < 0


def test_saturation_is_symmetric():
    reward = _reward()
    reward.calculate([_obs(-5000.0)])
    component = reward._last_component_breakdown['components'][0]
    bound = reward.profile['term_bound']
    assert component['norm_cost_net'] < -bound and component['bounded_cost_net'] == -bound
    assert component['sat_cost_net'] == 1.0


# --- store versus export: reward and KPI agree in sign on each axis ----------------------------------
# One building, 24 h: load 10 kWh/h; PV 30 kWh/h in hours 10-14 (surplus 20 kWh/h).
# Midday price/intensity 0.12 / 0.4, otherwise 0.22 / 0.6.
# export: surplus to the grid.  store: lossless BESS absorbs 100 kWh midday and
# supplies the night hours 0-4 and 19-23.
MIDDAY = range(10, 15)
NIGHT = list(range(0, 5)) + list(range(19, 24))
PRICE = [0.12 if h in MIDDAY else 0.22 for h in range(24)]
CARBON = [0.4 if h in MIDDAY else 0.6 for h in range(24)]
EXPORT = [-20.0 if h in MIDDAY else 10.0 for h in range(24)]
STORE = [0.0 if (h in MIDDAY or h in NIGHT) else 10.0 for h in range(24)]


def _reward_axis_sums(net):
    reward = _reward()
    totals = {'flex': 0.0, 'carbon': 0.0, 'cost': 0.0}
    for hour, value in enumerate(net):
        reward.calculate([_obs(value, PRICE[hour], CARBON[hour])])
        component = reward._last_component_breakdown['components'][0]
        for axis in totals:
            totals[axis] += component[axis]
    return totals


def _kpis(net):
    from uc3m.application.evaluation import kpi_contract as kc
    t0 = datetime.fromisoformat('2023-01-02T00:00:00-05:00')
    trace = kc.PhysicalTrace(
        timestamps=tuple((t0 + timedelta(hours=i)).isoformat() for i in range(24)), seconds_per_step=3600,
        building_ids=('B1',), series_by_building={'B1': {'net_power': tuple(net)}},
        district_series={'carbon_intensity': tuple(CARBON), 'price': tuple(PRICE)},
        units={'net_power': 'kW', 'carbon_intensity': 'kgCO2/kWh', 'price': 'USD/kWh'},
        currency='USD', currency_provenance='tariff:synthetic', exogenous_hash='0'*64)
    catalog = kc.load_kpi_catalog(REPO/'configs/evaluation/kpis.yaml')
    report = kc.compute_fresh_kpis(trace, trace, catalog)
    return {name: report.values[name]['value'] for name in report.values}


def test_store_versus_export_moves_the_three_axes_consistently():
    assert sum(EXPORT) == pytest.approx(sum(STORE))   # lossless: same net energy over the day
    reward_store, reward_export = _reward_axis_sums(STORE), _reward_axis_sums(EXPORT)
    kpi_store, kpi_export = _kpis(STORE), _kpis(EXPORT)
    # Hand-computed KPI values (net billing).
    assert kpi_export['energy_cost_total'] == pytest.approx(19*10*0.22 - 5*20*0.12)
    assert kpi_store['energy_cost_total'] == pytest.approx(9*10*0.22)
    assert kpi_export['co2_total'] == pytest.approx(19*10*0.6 - 5*20*0.4)
    assert kpi_store['co2_total'] == pytest.approx(9*10*0.6)
    assert kpi_export['district_daily_peak'] == pytest.approx(20.0)   # injection peak |P|
    assert kpi_store['district_daily_peak'] == pytest.approx(10.0)
    # Storing is better on each axis here: higher reward term, lower KPI (minimized).
    pairs = {'cost': ['energy_cost_total'], 'carbon': ['co2_total'],
             'flex': ['district_daily_peak', 'district_ramping']}
    for axis, kpis in pairs.items():
        reward_gain = reward_store[axis] - reward_export[axis]
        assert reward_gain > 0, axis
        for name in kpis:
            assert kpi_store[name] - kpi_export[name] < 0, name
    # The load-factor primary has no per-step reward term; on this trace it moves the
    # other way (flattening to zero lowers mean|P|/max|P|): reported, not hidden.
    assert kpi_store['one_minus_load_factor'] > kpi_export['one_minus_load_factor']
