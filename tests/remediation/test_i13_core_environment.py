"""Native CityLearn regressions for optional wrappers and legacy RBC."""
from pathlib import Path
import sys

import numpy as np
import pytest

from uc3m.env.uc3m_env import UC3MEnv
from uc3m.env.wrappers import HARLWrapper, PettingZooWrapper

ROOT = Path.cwd()
SCHEMA = ROOT/'data/campaigns/iquitos_v5/splits/validation_2024/schema.json'


@pytest.fixture
def env(tmp_path, request):
    sys.path.append(str(ROOT/'CityLearn/scripts'))
    import citylearn_v3_training_common as common
    old = common._CSV_CACHE_DIR
    common._CSV_CACHE_DIR = tmp_path/'native_cache'
    native = UC3MEnv(SCHEMA, episode_time_steps=getattr(request, 'param', 24), seed=2024)
    try:
        yield native
    finally:
        native.close()
        common._CSV_CACHE_DIR = old


def test_harl_rejects_multiple_threads_in_single_environment(env):
    with pytest.raises(ValueError, match='single|one|1'):
        HARLWrapper(env, n_threads=4)


def test_harl_global_state_shapes_and_action_validation(env):
    wrapper = HARLWrapper(env)
    obs, shared, _ = wrapper.reset()
    global_obs = np.concatenate([obs[0, i, :d] for i, d in enumerate(env.observation_dimensions)])
    assert obs.shape == (1, env.n_agents, env.observation_dimension)
    for i in range(env.n_agents):
        np.testing.assert_array_equal(shared[0, i], global_obs)
        assert wrapper.observation_space[i].shape == (env.observation_dimension,)
    invalid = np.zeros((2, env.n_agents, env.action_dimension))
    with pytest.raises(ValueError, match='shape|thread'):
        wrapper.step(invalid)
    result = wrapper.step(np.zeros((1, env.n_agents, env.action_dimension)))
    assert len(result) == 6
    assert result[2].shape == (1, env.n_agents, 1) and result[3].shape == (1, env.n_agents)
    assert result[1].shape == (1, env.n_agents, sum(env.observation_dimensions))


def test_parallel_seed_options_and_complete_action_contract(env, monkeypatch):
    wrapper = PettingZooWrapper(env)
    captured = []
    original = env._dec.reset
    def recording_reset(*args, **kwargs):
        captured.append(kwargs.copy())
        return original(*args, **kwargs)
    monkeypatch.setattr(env._dec, 'reset', recording_reset)
    first, infos = wrapper.reset(seed=321, options={})
    assert captured[-1] == {'seed': 321, 'options': {}}
    assert set(first) == set(infos) == set(wrapper.possible_agents)
    assert wrapper.metadata['api'] == 'parallel'
    for aid in first:
        assert wrapper.observation_space(aid).shape == first[aid].shape
        assert wrapper.action_space(aid).shape == env._dec.action_space(aid).shape
    with pytest.raises(ValueError, match='agent|action'):
        wrapper.step({})
    actions = {a: np.zeros(d) for a, d in zip(env.agent_ids, env.action_dimensions)}
    for _ in range(24):
        obs, rewards, terms, truncs, infos = wrapper.step(actions)
        assert set(obs) == set(rewards) == set(terms) == set(truncs) == set(infos)
        assert terms == env.last_terminations and truncs == env.last_truncations
    assert wrapper.agents == []
    assert wrapper.step({}) == ({}, {}, {}, {}, {})


@pytest.mark.parametrize('steps', [24, 48])
def test_legacy_rbc_completes_requested_native_horizon(steps):
    from uc3m.adapters.citylearn.rbc_baseline import run_rbc_baseline
    result = run_rbc_baseline(SCHEMA, episode_time_steps=steps)
    assert result['_meta']['total_steps'] == steps
    assert result['_meta']['terminated'] or result['_meta']['truncated']
    assert any(not k.startswith('_') for k in result)
