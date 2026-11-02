"""CityLearn CostFunction under net billing (owner decision 2026-11-01: «Sí, quitarlo»).

CostFunction.carbon_emissions and CostFunction.cost no longer clip exporting steps at
zero, so the evaluate_v2 ratios (carbon_emissions_total, cost_total) credit export at
the purchase price and as displaced emissions, consistently with Building and the
v3 reward.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'CityLearn'))


def test_exporting_step_is_credited_in_cost_and_emissions():
    from citylearn.cost_function import CostFunction
    price, intensity, export = 0.2, 0.5, 5.0
    net = [3.0, -export, 2.0]
    cost = CostFunction.cost([n*price for n in net])
    emissions = CostFunction.carbon_emissions([n*intensity for n in net])
    assert cost[1] - cost[0] == pytest.approx(-export*price)
    assert emissions[1] - emissions[0] == pytest.approx(-export*intensity)
    assert cost[-1] == pytest.approx(sum(net)*price)
    assert emissions[-1] == pytest.approx(sum(net)*intensity)


def test_dynamics_building_baselines_are_not_clipped():
    source = (REPO/'CityLearn/citylearn/building.py').read_text(encoding='utf-8')
    for name in ('net_electricity_consumption_emission_without_storage_and_partial_load_and_pv',
                 'net_electricity_consumption_emission_without_storage_and_partial_load'):
        body = source.split(f'def {name}(self)')[1].split('@property')[0]
        assert 'clip(min=0)' not in body, name
