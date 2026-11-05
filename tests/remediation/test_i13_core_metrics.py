"""Analytical counterexamples, not measured campaign results."""
from types import SimpleNamespace as NS

import numpy as np
import pytest

from uc3m.kpis.evaluator import KPIEvaluator
from uc3m.reward.term_telemetry import RewardTelemetryRecorder


def fixture_env():
    buildings = [NS(net_electricity_consumption=np.array([1., 2.]),
                    solar_generation=np.array([1., 0.]),
                    energy_consumption=np.array([2., 2.]),
                    pricing=NS(electricity_pricing=np.array([.1, .3])),
                    carbon_intensity=NS(carbon_intensity=np.array([.5, .7])),
                    electrical_storage=None)]
    return NS(citylearn=NS(buildings=buildings), time_steps=2,
              episode_axis_means=lambda: np.ones((1, 7))*.1)


def test_auxiliary_kpis_do_not_invent_missing_comparisons_or_outages():
    k = KPIEvaluator(1).compute_episode(fixture_env())
    for field in ('energy_saved_kwh', 'cost_saved_usd', 'peak_reduction_kw',
                  'arbitrage_gain_usd', 'co2_avoided_kg', 'avg_indoor_rh',
                  'resilience_score', 'islanding_hours', 'load_not_served_kwh'):
        assert getattr(k, field) is None, field
        assert k.metric_status[field] == 'unavailable'
    assert k.scientific_eligible is False
    assert 'N/A' in k.summary_line()
    assert k.to_dict()['cost_saved_usd'] is None
    assert k.to_dict()['scientific_eligible'] is False
    assert 'cost_saved_usd' not in k.metric_values()
    comparison = KPIEvaluator.compare([k])['run_0']
    assert comparison['scientific_eligible'] is False
    assert comparison['metric_status']['cost_saved_usd'] == 'unavailable'


def test_auxiliary_uses_actual_rates_only_with_declared_currency():
    env = fixture_env()
    k = KPIEvaluator(1, price_currency='USD', baseline_consumption_kwh=0.,
                     baseline_cost_usd=0., baseline_co2_kg=0., baseline_peak_kw=1.).compute_episode(env)
    assert k.cost_total_usd == pytest.approx(.7)
    assert k.co2_total_kg == pytest.approx(1.9)
    assert k.energy_saved_kwh == -3.
    assert k.cost_saved_usd == pytest.approx(-.7)
    assert k.co2_avoided_kg == pytest.approx(-1.9)
    assert k.peak_reduction_kw == -1.
    assert k.metric_status['cost_total_usd'] == 'simulation'
    assert k.metric_status['hphi'] == 'reward_proxy'
    assert k.arbitrage_gain_usd is None


def test_auxiliary_never_labels_unknown_currency_as_usd():
    k = KPIEvaluator(1).compute_episode(fixture_env())
    assert k.cost_total_usd is None


def test_auxiliary_metadata_reports_completed_intervals_instead_of_planned_horizon():
    env = fixture_env()
    env.citylearn.time_step = 1
    k = KPIEvaluator(1).compute_episode(env)
    assert k.time_steps == 1
    assert k.co2_total_kg == pytest.approx(.5)


def test_auxiliary_modeled_rate_requires_optin_and_is_labeled():
    env = fixture_env()
    del env.citylearn.buildings[0].carbon_intensity
    k = KPIEvaluator(1, allow_modeled_estimates=True,
                     price_default_usd=.4, carbon_intensity_default=.8).compute_episode(env)
    assert k.cost_total_usd == pytest.approx(1.2)
    assert k.co2_total_kg == pytest.approx(2.4)
    assert k.metric_status['cost_total_usd'] == 'modeled'
    assert k.metric_status['co2_total_kg'] == 'modeled'
    assert k.cost_saved_usd is None and k.co2_avoided_kg is None


def test_telemetry_sums_per_building_rates_and_refuses_a_fake_district_price():
    recorder = RewardTelemetryRecorder()
    recorder._series = {
        0: dict(net=[1., 2.], baseline=[3., 4.], price=[.1, .2], carbon=[.5, .6]),
        1: dict(net=[1., 2.], baseline=[2., 3.], price=[.3, .4], carbon=[.7, .8]),
    }
    result = recorder._episode_indicators()
    district = result['district']
    assert district['electricity_cost_total'] == pytest.approx(1.6)
    assert district['electricity_cost_delta'] == pytest.approx(-1.3)
    assert district['carbon_emissions_total'] == pytest.approx(4.)
    assert district['carbon_emissions_delta'] == pytest.approx(-3.7)
    assert district['price_signal_deviation'] is None
    assert result['unavailable']['district.price_signal_deviation'] == 'heterogeneous_building_prices'
