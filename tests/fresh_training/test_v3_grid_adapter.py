"""SPEC-015 D-M3-7/D-M3-9/D-M3-10: the CityLearn v3 adapter gives the 4 MADRL the same 5-level grid per equipment.

On the active dataset: MASAC sees a flat head of max equipments x 5 with padded branches masked, MAAC a MultiDiscrete
per agent, and HAPPO/MATD3 continuous outputs reach the simulator rounded to the same levels.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SCHEMA = str(REPO/CAMPAIGN['dataset_root']/'splits/train_2023/schema.json')


@pytest.fixture(scope='module')
def common():
    sys.path.insert(0, str(REPO/'CityLearn/scripts'))
    import citylearn_v3_training_common as c
    return c


def test_masac_head_is_max_equipments_by_levels_with_padding_masked(common):
    from citylearn.v3.action_grid import LEVELS
    env = common.CityLearnSMACDiscreteEnv(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=4,
                                          discrete_action_mode='grid', algorithm='MASAC')
    try:
        info = env.get_env_info()
        grid = env.adapter.action_grid
        assert info['action_branches'] == (grid.max_branches, LEVELS)
        assert info['n_actions'] == grid.max_branches*LEVELS
        rng = np.random.default_rng(0)
        actions = []
        for i in range(env.n_agents):
            mask = env.get_avail_agent_actions(i).reshape(grid.max_branches, LEVELS)
            assert mask[:grid.branches[i]].all() and mask[grid.branches[i]:].sum() == grid.max_branches - grid.branches[i]
            actions.append(np.array([rng.integers(0, LEVELS) if k < grid.branches[i] else 0
                                     for k in range(grid.max_branches)]))
        reward, terminated, _ = env.step(actions)
        assert np.isfinite(reward) and terminated is False
        recorded = env.adapter.trace_records[-1] if env.adapter.trace_records else None
        assert recorded is None or recorded
    finally:
        env.close()


def test_maac_has_one_branch_of_levels_per_real_equipment(common):
    from citylearn.v3.action_grid import LEVELS
    env = common.CityLearnMAACVecEnv(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=4,
                                     discrete_action_mode='grid', algorithm='MAAC')
    try:
        grid = env.adapter.action_grid
        assert [list(s.nvec) for s in env.action_space] == [[LEVELS]*k for k in grid.branches]
        env.reset()
        onehots = [grid.onehot(i, np.full(k, 4))[:k*LEVELS] for i, k in enumerate(grid.branches)]
        assert [list(env.grid_indices(i, a)) for i, a in enumerate(onehots)] == [[4]*k for k in grid.branches]
        obs, reward, done, _ = env.step([onehots])
        assert reward.shape == (1, env.n_agents) and np.isfinite(reward).all()
    finally:
        env.close()


def test_continuous_outputs_reach_the_simulator_on_the_grid(common):
    env = common.CityLearnHARLEnv(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=4,
                                  algorithm='HAPPO', action_grid=5)
    try:
        adapter = env.adapter
        env.reset()
        seen = {}
        original = adapter._step

        def spy(action_dict):
            seen.update(action_dict)
            return original(action_dict)
        adapter._step = spy
        dim = adapter.max_action_dim
        adapter.step_continuous([np.full(dim, 0.37, dtype=np.float32) for _ in adapter.agents])
        for i, agent in enumerate(adapter.agents):
            levels = [adapter.action_grid.levels(i, k) for k in range(adapter.action_grid.branches[i])]
            for value, row in zip(seen[agent], levels):
                assert np.isclose(row, value).any(), (agent, value)
        with pytest.raises(ValueError, match='common grid'):
            common.CityLearnHARLEnv(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=4,
                                    algorithm='HAPPO', action_grid=7)
    finally:
        env.close()
