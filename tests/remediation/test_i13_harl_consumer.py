"""The actual HARL warmup/buffers consume the optional native CityLearn wrapper."""
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from test_i13_core_environment import env as _native_env
from uc3m.env.wrappers import HARLWrapper

env = _native_env


@pytest.mark.parametrize('env', [2], indirect=True)
def test_actual_harl_warmup_and_buffers_accept_vector_contract(env):
    sys.path.insert(0, str(Path.cwd()/'external/HARL'))
    from harl.runners.on_policy_base_runner import OnPolicyBaseRunner
    from harl.common.buffers.on_policy_actor_buffer import OnPolicyActorBuffer
    from harl.common.buffers.on_policy_critic_buffer_ep import OnPolicyCriticBufferEP
    wrapper = HARLWrapper(env)
    args = dict(episode_length=2, n_rollout_threads=1, hidden_sizes=[8], recurrent_n=1,
                gamma=.99, gae_lambda=.95, use_gae=True, use_proper_time_limits=True)
    actors = [OnPolicyActorBuffer(args, wrapper.observation_space[i], wrapper.action_space[i])
              for i in range(env.n_agents)]
    critic = OnPolicyCriticBufferEP(args, wrapper.share_observation_space[0])
    holder = SimpleNamespace(envs=wrapper, num_agents=env.n_agents, actor_buffer=actors,
                             critic_buffer=critic, state_type='EP')
    OnPolicyBaseRunner.warmup(holder)
    actions = np.zeros((1, env.n_agents, env.action_dimension), dtype=np.float32)
    obs, shared, rewards, dones, infos, available = wrapper.step(actions)
    assert obs.shape == (1, env.n_agents, env.observation_dimension)
    assert shared.shape == (1, env.n_agents, sum(env.observation_dimensions))
    assert rewards.shape == (1, env.n_agents, 1) and dones.shape == (1, env.n_agents)
    assert available.shape == (1,) and available[0] is None
    assert len(infos) == 1 and len(infos[0]) == env.n_agents
    for i, actor in enumerate(actors):
        actor.insert(obs[:, i], np.zeros((1, 1, 8)), actions[:, i],
                     np.zeros_like(actions[:, i]), np.ones((1, 1)))
        np.testing.assert_allclose(actor.obs[1], obs[:, i], rtol=1e-6, atol=1e-6)
    critic.insert(shared[:, 0], np.zeros((1, 1, 8)), np.zeros((1, 1)),
                  rewards.mean(axis=1), np.ones((1, 1)), np.ones((1, 1)))
    np.testing.assert_allclose(critic.share_obs[1], shared[:, 0], rtol=1e-6, atol=1e-6)
    _, _, _, endings, terminal_infos, _ = wrapper.step(actions)
    assert endings.all()
    assert 'original_obs' in terminal_infos[0][0]
    _, _, _, next_endings, _, _ = wrapper.step(actions)
    assert not next_endings.any()
