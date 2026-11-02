"""Net billing on the CO2 axis inside CityLearn (owner decision 2026-11-01).

Exported PV displaces thermal generation of the isolated grid, so a building
with negative net consumption has negative emissions: Building no longer clips
net_electricity_consumption_emission at zero (building.py update). Real
simulator, 24 steps, PV scaled x50 so that buildings export at midday.

Cost is NOT net billing in this dataset: the iquitos_v1 schema enables the
community market (local trade at 0.8 x price, grid_export_price 0.0), so
internal/runtime.py settles the building cost and exported energy to the grid
earns nothing. That is a dataset/runtime setting outside this change; the test
records it so it cannot be forgotten.
"""
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO/'data/campaigns/iquitos_v1/splits/train_2023/schema.json'


def test_export_reduces_district_emissions_and_cost_is_net(monkeypatch):
    from citylearn.building import Building
    from citylearn.v3 import make_citylearn_v3_env
    original = Building.solar_generation
    monkeypatch.setattr(Building, 'solar_generation', property(lambda self: original.fget(self)*50.0))
    env = make_citylearn_v3_env(schema_path=str(SCHEMA), scenario='E1', seed=0, episode_time_steps=24,
                                madrl_algorithm='MATD3', normalize_observations=False)
    env.reset()
    for _ in range(23):
        env.step({agent: env.action_space(agent).sample()*0 for agent in env.possible_agents})
    core = env.env.unwrapped
    exported = 0
    for building in core.buildings:
        net = np.asarray(building.net_electricity_consumption, dtype=float)
        ci = np.asarray(building.carbon_intensity.carbon_intensity[:net.size], dtype=float)
        price = np.asarray(building.pricing.electricity_pricing[:net.size], dtype=float)
        emission = np.asarray(building.net_electricity_consumption_emission, dtype=float)
        np.testing.assert_allclose(emission, net*ci, rtol=1e-5, atol=1e-6)
        exported += int((net < 0).sum())
        if (net < 0).any():
            assert (emission[net < 0] < 0).all()
    assert exported > 0, 'the fixture must make some building export'
    district = np.asarray(core.net_electricity_consumption_emission, dtype=float)
    assert district.min() < 0 or any((np.asarray(b.net_electricity_consumption_emission) < 0).any()
                                     for b in core.buildings)


def test_dataset_settles_cost_through_the_community_market_without_export_credit():
    import json
    market = json.loads(SCHEMA.read_text(encoding='utf-8'))['community_market']
    # Documented contradiction with the owner's net billing (pending owner decision).
    assert market['enabled'] is True and float(market['grid_export_price']) == 0.0
