"""Three-layer KPI catalog with verifiable sources (owner 2026-11-01: «no inventes»).

Layer A: the 9 thesis indicators (3 axes x 3 dimensions, tesis Tabla 2.1; cap2 §2.2.8).
Layer B: the CityLearn v3 objective KPIs 1:1, and the structurally comparable subset
         derived with objectives._baseline_for (12/5/9) with the oriented KPI-gain of
         tools/eval/objective_analysis.py.
Layer C: one dense reward term per Layer A indicator, pending ones with weight 0.
"""
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import yaml

from uc3m.application.evaluation import kpi_contract as kc

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO/'configs/evaluation/kpis.yaml'
DAYS, STEPS = 3, 72
CORE = ('peak_average', 'ramping_average', 'one_minus_load_factor_average', 'carbon_emissions_total',
        'carbon_emissions_delta', 'ci_weighted_consumption', 'electricity_cost_total', 'electricity_cost_delta',
        'peak_billing')


@pytest.fixture(scope='module')
def payload():
    return yaml.safe_load(CATALOG.read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def catalog():
    return kc.load_kpi_catalog(CATALOG)


def _objectives():
    import sys
    sys.path.insert(0, str(REPO/'CityLearn'))
    from citylearn.v3 import objectives
    return objectives


# --- Layer B --------------------------------------------------------------------------------------------

def test_layer_b_is_citylearn_v3_one_to_one(payload):
    o = _objectives()
    axis = {'OE1': 'flexibility', 'OE2': 'co2_emissions', 'OE3': 'energy_cost'}
    expected = [(name, axis[code], 'minimize' if name not in o.HIGHER_IS_BETTER else 'maximize',
                 name in o.RATIO_TO_BASELINE_KPIS) for code, ax in o.OBJECTIVE_AXES.items() for name in ax.kpis]
    listed = [(r['name'], r['axis'], r['sense'], r['ratio_to_baseline']) for r in payload['citylearn_v3_kpis']]
    assert listed == expected


def test_comparable_set_is_derived_and_matches_the_thesis_counts():
    groups = kc.comparable_kpi_names()                    # = fresh_analysis.comparable_kpis()
    counts = {axis: len(names) for axis, (_, names) in groups.items()}
    assert counts == {'flexibility': 12, 'co2_emissions': 5, 'energy_cost': 9}   # tesis ~1972: 26
    assert {axis: scenario for axis, (scenario, _) in groups.items()} == {
        'flexibility': 'E1', 'co2_emissions': 'E2', 'energy_cost': 'E3'}
    assert not any(n.endswith('_baseline') for _, names in groups.values() for n in names)


def test_gain_rows_follow_objective_analysis_and_keep_unavailable_rows():
    report = {'axes': {'OE1': {'kpis': {
        'peak_average': {'value': 0.9, 'comparison': {'available': True, 'baseline': 1.0}},
        'grid_import_delta': {'value': 5.0, 'comparison': {'available': True, 'baseline': 0.0}},
        'grid_export_control': {'value': None, 'comparison': {'available': False, 'baseline': 3.0}}}}}}
    rows = {r['name']: r for r in kc.comparable_kpi_gain_rows(report)}
    assert len(rows) == 26
    assert rows['peak_average']['gain'] == pytest.approx(0.1)           # lower is better, |baseline| = 1
    assert rows['grid_import_delta']['gain'] == pytest.approx(-5.0/5.0)  # |baseline| < 1e-12 -> max(|value|, 1)
    assert rows['grid_export_control']['available'] is False and rows['grid_export_control']['gain'] is None
    assert set(rows['peak_average']) == {'name', 'axis', 'value', 'baseline', 'lower_is_better', 'gain',
                                         'available'}
    assert all(r['available'] is False for n, r in rows.items() if n not in report['axes']['OE1']['kpis'])


# --- Layer A --------------------------------------------------------------------------------------------

def test_layer_a_has_the_nine_thesis_indicators_with_sources(payload):
    indicators = {r['name']: r for r in payload['thesis_indicators']}
    assert set(CORE) <= set(indicators)
    for name in CORE:
        assert indicators[name]['source'].startswith(('tesis.docx.txt', "tesis.docx.txt")), name
    assert {(indicators[n]['axis'], indicators[n]['dimension']) for n in CORE} == {
        (a, d) for a in ('flexibility', 'co2_emissions', 'energy_cost') for d in (1, 2, 3)}
    pending = {n for n, r in indicators.items() if r['definition_status'] == 'pending_owner'}
    assert pending == {'PAR', 'DPR', 'dso_excess'}
    for name in pending:
        assert indicators[name]['formula'] is None or name == 'dso_excess'


def _stamps(n):
    t0 = datetime.fromisoformat('2023-01-02T00:00:00-05:00')
    return tuple((t0 + timedelta(hours=i)).isoformat() for i in range(n))


def _trace(power, price, carbon):
    n = len(power)
    return kc.PhysicalTrace(
        timestamps=_stamps(n), seconds_per_step=3600, building_ids=('B1',),
        series_by_building={'B1': {'net_power': tuple(power)}},
        district_series={'carbon_intensity': tuple(carbon), 'price': tuple(price)},
        units={'net_power': 'kW', 'carbon_intensity': 'kgCO2/kWh', 'price': 'USD/kWh'},
        currency='USD', currency_provenance='tariff:synthetic', exogenous_hash='0'*64)


PRICE = [0.12 if 10 <= h % 24 <= 14 else 0.22 for h in range(STEPS)]
CARBON = [0.4 if 10 <= h % 24 <= 14 else 0.6 for h in range(STEPS)]
PEAKY = [3.0 if h % 24 not in (18, 19) else 18.0 for h in range(STEPS)]
FLAT = [sum(PEAKY[:24])/24]*STEPS


def _report(control, baseline, payload, catalog):
    # As in a composition root: the CityLearn v3 price_signal_deviation rule is injected.
    from uc3m.adapters.citylearn.frozen_adapters import citylearn_frozen_adapters
    return kc.compute_fresh_kpis(_trace(control, PRICE, CARBON), _trace(baseline, PRICE, CARBON), catalog,
                                 thesis_indicators=payload['thesis_indicators'],
                                 extra_measures=citylearn_frozen_adapters().extra_measures)


def test_layer_a_values_come_from_the_trace(payload, catalog):
    report = _report(FLAT, PEAKY, payload, catalog)
    rows = {r['name']: r for r in report.thesis_indicators}
    values = report.values
    assert rows['peak_average']['value'] == pytest.approx(
        values['district_daily_peak']['value']/values['district_daily_peak']['baseline'])
    assert rows['flex_composite']['value'] == pytest.approx(np.mean([rows[n]['value'] for n in CORE[:3]]))
    assert rows['carbon_emissions_delta']['value'] == pytest.approx(values['co2_total']['delta'])
    assert rows['ci_weighted_consumption']['value'] == pytest.approx(sum(p*c for p, c in zip(FLAT, CARBON)))
    assert rows['electricity_cost_delta']['value'] == pytest.approx(values['energy_cost_total']['delta'])
    # The synthetic building B1 has no official rate: unavailable, never zero.
    assert rows['peak_billing']['available'] is False and rows['peak_billing']['definition_status'] == 'defined'
    assert rows['price_signal_deviation']['available'] is True
    assert len(report.comparable_kpi_gains) == 26 and not any(r['available'] for r in report.comparable_kpi_gains)
    as_dict = report.as_dict()
    assert set(as_dict['axis_gains']) == {'flexibility', 'co2_emissions', 'energy_cost'}
    assert len(as_dict['comparable_kpi_gains']) == 26
    assert len(as_dict['thesis_indicators']) == len(payload['thesis_indicators'])


def test_standard_citylearn_kpis_agree_without_export(catalog):
    import sys
    sys.path.insert(0, str(REPO/'CityLearn'))
    from citylearn.cost_function import CostFunction as cf
    power = [5 + 3*math.sin(i*2*math.pi/24) for i in range(STEPS)]
    report = kc.compute_fresh_kpis(_trace(power, [0.2]*STEPS, [0.5]*STEPS),
                                   _trace(power, [0.2]*STEPS, [0.5]*STEPS), catalog)
    values = {k: v['value'] for k, v in report.values.items()}
    assert values['district_daily_peak'] == pytest.approx(cf.peak(power, window=24)[-1])
    assert values['one_minus_load_factor'] == pytest.approx(cf.one_minus_load_factor(power, window=24)[-1])
    assert values['district_ramping'] == pytest.approx(cf.ramping(power, down_ramp=True)[-1]/(STEPS - 1))
    assert values['co2_total'] == pytest.approx(cf.carbon_emissions([p*0.5 for p in power])[-1])
    assert values['energy_cost_total'] == pytest.approx(cf.cost([p*0.2 for p in power])[-1])


# --- Layer C --------------------------------------------------------------------------------------------

def _reward():
    from citylearn.v3.reward import CityLearnV3MADRLRewardFunction
    return CityLearnV3MADRLRewardFunction({'central_agent': False, 'seconds_per_time_step': 3600},
                                          algorithm='MATD3', scenario='E1')


def test_every_layer_a_indicator_has_a_term_or_is_pending(payload):
    from citylearn.v3.reward import CITYLEARN_V3_REWARD_TERMS
    profile = _reward().profile
    weights = {**profile['flex_subweights'], **profile['carbon_subweights'], **profile['cost_subweights']}
    for key in ('flex_subweights', 'carbon_subweights', 'cost_subweights'):
        assert sum(profile[key].values()) == pytest.approx(1.0), key
    assert set(weights) == set(CITYLEARN_V3_REWARD_TERMS)
    for indicator in payload['thesis_indicators']:
        term = indicator.get('reward_term')
        if indicator['name'] in CORE or indicator['name'] in ('price_signal_deviation', 'dso_excess'):
            assert term in CITYLEARN_V3_REWARD_TERMS, indicator['name']
            status = CITYLEARN_V3_REWARD_TERMS[term][3]
            if status == 'pending_owner':
                assert weights[term] == 0.0, term
            else:
                assert weights[term] > 0.0, term


def _reward_sums(power, baseline=None):
    reward = _reward()
    sums = {}
    for t, p in enumerate(power):
        extra = {} if baseline is None else {'electrical_storage_electricity_consumption': p - baseline[t]}
        reward.calculate([{'net_electricity_consumption': p, 'electricity_pricing': PRICE[t],
                           'carbon_intensity': CARBON[t], **extra}])
        c = reward._last_component_breakdown['components'][0]
        for key, value in c.items():
            if key.startswith('bounded_'):
                sums[key[len('bounded_'):]] = sums.get(key[len('bounded_'):], 0.0) + value
        sums['flex'] = sums.get('flex', 0.0) + c['flex']
    return sums


def test_reward_terms_move_with_their_indicators(payload, catalog):
    peaky, flat = _reward_sums(PEAKY, PEAKY), _reward_sums(FLAT, PEAKY)
    rows_flat = {r['name']: r for r in _report(FLAT, PEAKY, payload, catalog).thesis_indicators}
    rows_peaky = {r['name']: r for r in _report(PEAKY, PEAKY, payload, catalog).thesis_indicators}
    pairs = {'daily_peak': 'peak_average', 'ramp': 'ramping_average', 'load_factor': 'one_minus_load_factor_average',
             'carbon_net': 'carbon_emissions_total', 'carbon_delta': 'carbon_emissions_delta',
             'carbon_ci_import': 'ci_weighted_consumption', 'cost_net': 'electricity_cost_total',
             'cost_delta': 'electricity_cost_delta'}
    for term, indicator in pairs.items():
        reward_delta = flat[term] - peaky[term]
        kpi_delta = rows_flat[indicator]['value'] - rows_peaky[indicator]['value']
        assert reward_delta*kpi_delta > 0, (term, reward_delta, kpi_delta)
    assert flat['flex'] > peaky['flex']          # flatter curve: higher flex reward, lower 1-LF
    assert rows_flat['one_minus_load_factor_average']['value'] < rows_peaky['one_minus_load_factor_average']['value']


def test_load_factor_and_peak_terms_sum_to_the_daily_kpis(catalog):
    power = [5 + 3*math.sin(i*2*math.pi/24) + (i % 5) for i in range(STEPS)]
    sums = _reward_sums(power)
    values = kc.compute_fresh_kpis(_trace(power, PRICE, CARBON), _trace(power, PRICE, CARBON), catalog).values
    assert sums['load_factor'] == pytest.approx(DAYS*values['one_minus_load_factor']['value'])
    assert sums['daily_peak'] == pytest.approx(DAYS*values['district_daily_peak']['value']/25.0)
