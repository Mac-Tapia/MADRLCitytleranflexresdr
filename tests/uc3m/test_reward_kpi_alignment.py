"""Audit 2026-11-01 (items 2, 5): the v3 reward reads the treatment weights and is
aligned with the confirmatory KPIs.

- Axis weights come from the scenario catalog named by UC3M_SCENARIO_CATALOG
  (single source configs/objective_policies.yaml, or a generated sensitivity
  catalog); the embedded legacy table is only a fallback and must agree with
  the catalog.
- No dead team mixing: the reward returns local terms and the Dec-POMDP
  wrapper's team_mean makes the game common-payoff.
- Peak is convex and ramp linear on the district net power; CO2 and cost are
  linear in building net consumption x intensity/price, without offsets (net
  billing since 2026-11-01, see test_reward_net_billing.py).
- EV and BESS are constraint penalties only (never positive energy incentives)
  and stay outside the weighted three-axis vector.
- Every term is recorded raw, normalized, bounded, weighted and in the local reward.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from citylearn.v3.reward import (
    CITYLEARN_V3_AXIS_REWARD_WEIGHTS,
    CityLearnV3MADRLRewardFunction,
    scenario_catalog_axis_weights,
)

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO/'configs/scenarios.yaml'


def _reward(scenario='E1', **kwargs):
    return CityLearnV3MADRLRewardFunction({'central_agent': False}, algorithm='MATD3', scenario=scenario, **kwargs)


def _obs(net, price=0.17, carbon=0.5, **extra):
    return dict({'net_electricity_consumption': net, 'electricity_pricing': price, 'carbon_intensity': carbon},
                **extra)


def _charger(soc, required, hours, charged=0.0):
    return {'connected': True, 'battery_soc': soc, 'previous_battery_soc': soc, 'battery_capacity': 40.0,
            'min_capacity': 4.0, 'last_charged_kwh': charged, 'required_soc': required,
            'hours_until_departure': hours, 'max_charging_power': 7.0, 'max_discharging_power': 7.0}


# --- item 2: effective weights --------------------------------------------------------------------

def test_reward_reads_weights_from_the_catalog(monkeypatch):
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(CATALOG))
    reward = _reward('E2')
    assert reward.axis_weights == pytest.approx({'flex': 0.25, 'carbon': 0.60, 'cost': 0.15}, abs=1e-12)
    source = reward.metadata['axis_weights_source']
    assert source['kind'] == 'scenario_catalog' and source['objective_policy_id'] == 'E2'
    from uc3m.application.training.fresh_campaign import catalog_sha256
    assert source['sha256'] == catalog_sha256(CATALOG)


def test_reward_reads_derived_sensitivity_weights(monkeypatch, tmp_path):
    from uc3m.application.training.fresh_campaign import write_derived_scenario_catalog
    derived = write_derived_scenario_catalog(CATALOG, 'E1', (0.55, 0.16875, 0.28125), 'p055', tmp_path/'cat')
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(derived['path']))
    reward = _reward('E1')
    assert reward.axis_weights == pytest.approx({'flex': 0.55, 'carbon': 0.16875, 'cost': 0.28125}, abs=1e-12)
    assert reward.metadata['axis_weights_source']['sha256'] == derived['sha256']
    # The scenario manager accepts the derived (non-canonical) policy instead of rejecting it.
    from citylearn.scenario_manager import ScenarioManager
    config = ScenarioManager().select_scenario('E1')
    assert config.reward_weights == pytest.approx({'flex': 0.55, 'carbon': 0.16875, 'cost': 0.28125})


def test_embedded_table_is_only_a_fallback_and_agrees_with_the_catalog(monkeypatch):
    monkeypatch.delenv('UC3M_SCENARIO_CATALOG', raising=False)
    for scenario in ('E1', 'E2', 'E3'):
        weights, _ = scenario_catalog_axis_weights(scenario, CATALOG)
        assert weights == pytest.approx(CITYLEARN_V3_AXIS_REWARD_WEIGHTS[scenario], abs=1e-12)
        assert _reward(scenario).metadata['axis_weights_source']['kind'] == 'embedded_legacy_table'


# --- item 5a: no dead mixing ----------------------------------------------------------------------

def test_reward_returns_local_terms_and_declares_common_payoff():
    reward = _reward()
    observations = [_obs(30.0), _obs(5.0)]
    values = reward.calculate(observations)
    components = reward._last_component_breakdown['components']
    assert values == pytest.approx([c['local_reward'] for c in components], abs=1e-12)
    assert values[0] != pytest.approx(values[1])   # no internal 0.7/0.3 mixing
    assert 'team_reward_ratio' not in reward.profile
    assert reward._last_component_breakdown['aggregation'].startswith('local')
    with pytest.raises(ValueError):
        _reward(profile={'team_reward_ratio': 0.7})


# --- item 5b: KPI-aligned forms -------------------------------------------------------------------

def _component(reward, observations, index=0, previous=None):
    if previous is not None:
        reward.calculate(previous)
    reward.calculate(observations)
    return reward._last_component_breakdown['components'][index]


def test_co2_and_cost_are_linear_in_import_without_offsets():
    zero_intensity = _component(_reward(), [_obs(10.0, price=0.0, carbon=0.0)])
    assert zero_intensity['carbon'] == 0.0 and zero_intensity['cost'] == 0.0
    single = _component(_reward(), [_obs(4.0)])
    double = _component(_reward(), [_obs(8.0)])
    assert double['carbon'] == pytest.approx(2*single['carbon'])
    assert double['cost'] == pytest.approx(2*single['cost'])
    assert single['raw_carbon_net'] == pytest.approx(4.0*0.5) and single['raw_cost_net'] == pytest.approx(4.0*0.17)
    exported = _component(_reward(), [_obs(-6.0)])
    # Net billing (owner decision 2026-11-01): the net terms credit export, see test_reward_net_billing.py.
    assert exported['bounded_carbon_net'] == pytest.approx(-single['bounded_carbon_net']*6.0/4.0)
    assert exported['bounded_cost_net'] == pytest.approx(-single['bounded_cost_net']*6.0/4.0)


def test_peak_is_convex_and_ramp_linear_on_district_net_power():
    def flex_at(power):
        return -_component(_reward(), [_obs(power)])['flex']
    assert flex_at(20.0) >= 2*flex_at(10.0) - 1e-12      # peak increment linear, never concave
    ramp_small = _component(_reward(), [_obs(10.0)], previous=[_obs(5.0)])['norm_ramp']
    ramp_large = _component(_reward(), [_obs(15.0)], previous=[_obs(5.0)])['norm_ramp']
    assert ramp_large == pytest.approx(4*ramp_small)   # cap2 §2.2.8: quadratic ramp
    # A building's export offsets another's import in the coincident district power.
    balanced = _reward().calculate([_obs(10.0), _obs(-10.0)])
    breakdown = _reward()
    breakdown.calculate([_obs(0.0), _obs(0.0)])
    reward = _reward()
    reward.calculate([_obs(10.0), _obs(-10.0)])
    assert reward._last_component_breakdown['components'][0]['flex'] == pytest.approx(
        breakdown._last_component_breakdown['components'][0]['flex'])
    assert balanced[0] < balanced[1]   # only the importing building pays CO2 and cost


def test_import_is_not_counted_in_the_flexibility_axis():
    a = _component(_reward(), [_obs(10.0, electrical_storage_soc=0.9), _obs(-10.0)])
    b = _component(_reward(), [_obs(10.0, electrical_storage_soc=0.1), _obs(-10.0)])
    assert a['flex'] == pytest.approx(b['flex'])


# --- item 5c: EV / BESS constraints only ----------------------------------------------------------

def test_ev_term_is_a_penalty_only():
    satisfied = _component(_reward(), [_obs(-5.0, electric_vehicles_chargers_dict={
        'c1': _charger(0.80, 0.80, 0.0, charged=3.0)})])
    assert satisfied['ev'] == 0.0     # no energy incentive for charging from self-production
    deficit = _component(_reward(), [_obs(5.0, electric_vehicles_chargers_dict={
        'c1': _charger(0.30, 0.80, 0.0)})])
    assert deficit['ev'] < 0.0
    violation = _component(_reward(), [_obs(5.0, charging_constraint_violation_kwh=50.0,
                                            electric_vehicles_chargers_dict={'c1': _charger(0.8, 0.8, 3.0)})])
    assert violation['ev'] == pytest.approx(-0.25) and violation['sat_ev_violation'] == 1.0


def test_constraint_terms_stay_outside_the_weighted_vector():
    reward = _reward()
    reward.calculate([_obs(5.0, electrical_storage_soc=0.2)])
    component = _component(reward, [_obs(5.0, electrical_storage_soc=0.8, electric_vehicles_chargers_dict={
        'c1': _charger(0.30, 0.80, 1.0)})])
    weighted = component['weighted_flex'] + component['weighted_carbon'] + component['weighted_cost']
    assert component['local_reward'] == pytest.approx(weighted + component['ev'] + component['bess_cycle'])
    for axis in ('flex', 'carbon', 'cost'):
        assert component[f'weighted_{axis}'] == pytest.approx(reward.axis_weights[axis]*component[axis])
    assert component['bess_cycle'] < 0 and component['ev'] < 0


# --- item 5d: breakdown before/after normalization, weighting and aggregation ----------------------

def test_breakdown_records_every_stage_and_saturation():
    reward = _reward()
    component = _component(reward, [_obs(2000.0)])
    for term in ('daily_peak', 'ramp', 'load_factor', 'carbon_net', 'carbon_delta', 'carbon_ci_import',
                 'cost_net', 'cost_delta', 'ev_violation', 'bess_cycle'):
        for stage in ('norm', 'bounded', 'sat'):
            assert f'{stage}_{term}' in component, f'{stage}_{term}'
    assert component['norm_carbon_net'] > component['bounded_carbon_net'] and component['sat_carbon_net'] == 1.0
    assert component['sat_daily_peak'] == 1.0
    assert all(math.isfinite(v) for v in component.values())
    district = reward._last_component_breakdown['district']
    assert district['net_power_kw'] == pytest.approx(2000.0)
    assert reward._last_component_breakdown['team_reward'] == pytest.approx(component['local_reward'])
