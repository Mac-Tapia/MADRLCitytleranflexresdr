"""Real 17-building simulator contract, not a substitute for learner training."""
import importlib
import sys
from pathlib import Path

import numpy as np
import pytest


@pytest.mark.parametrize('algorithm', ['HAPPO', 'MASAC', 'MATD3', 'MAAC'])
@pytest.mark.parametrize('scenario,weights', [
    ('E1', {'flex': .60, 'carbon': .15, 'cost': .25}),
    ('E2', {'flex': .25, 'carbon': .60, 'cost': .15}),
    ('E3', {'flex': .15, 'carbon': .25, 'cost': .60}),
])
def test_real_simulator_step_has_finite_reward_and_canonical_policy(monkeypatch, algorithm, scenario, weights):
    root = Path(__file__).resolve().parents[3]
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(root/'configs/scenarios.yaml'))
    sys.path.insert(0, str(root/'CityLearn/scripts'))
    common = importlib.import_module('citylearn_v3_training_common')
    adapter = common.CityLearnV3BackendAdapter(
        schema_path=str(root/'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'),
        scenario=scenario, algorithm=algorithm, episode_time_steps=4)
    try:
        adapter.reset()
        assert adapter.n_agents == 17
        assert adapter.reward_metadata['axis_weights'] == weights
        result = (adapter.step_discrete([0]*adapter.n_agents) if algorithm in {'MASAC', 'MAAC'}
                  else adapter.step_continuous([np.zeros(adapter.max_action_dim)]*adapter.n_agents))
        rewards = result[1]
        assert np.all(np.isfinite(list(rewards.values()) if isinstance(rewards, dict) else rewards))
    finally:
        adapter.close()
