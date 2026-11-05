"""Single-environment HARL adapter and PettingZoo Parallel API adapter.

HARLWrapper wraps one real rollout thread. Parallel training needs a real
vector-environment owner, not repeated observations.
"""
from __future__ import annotations

import numpy as np
from gymnasium.spaces import Box
from pettingzoo import ParallelEnv

from uc3m.env.uc3m_env import UC3MEnv


def _ordered(env, values):
    return [values[a] for a in env.agent_ids] if isinstance(values, dict) else list(values)


class HARLWrapper:
    """A vector API with exactly one real CityLearn rollout environment.

    Pass directly as runner.envs; do not wrap again in DummyVecEnv. Actor
    observations/actions are zero-padded to uniform dimensions; only declared
    live action coordinates reach CityLearn. The critic gets concatenated local
    observations. This encoding alone does not prove a Markov state.
    """
    def __init__(self, env: UC3MEnv, n_threads: int = 1):
        if type(n_threads) is not int or n_threads != 1:
            raise ValueError('single environment: n_threads must be 1')
        self.env, self.n_threads, self.num_envs, self.n_agents = env, 1, 1, env.n_agents
        self.observation_lengths = tuple(env.observation_dimensions)
        self.action_lengths = tuple(env.action_dimensions)
        self._obs_dim, self._act_dim = max(self.observation_lengths), max(self.action_lengths)
        self.observation_space = [Box(-np.inf, np.inf, shape=(self._obs_dim,), dtype=np.float32)
                                  for _ in env.agent_ids]
        state_dim = sum(self.observation_lengths)
        self.share_observation_space = [Box(-np.inf, np.inf, shape=(state_dim,), dtype=np.float32)
                                        for _ in env.agent_ids]
        self.action_space = []
        for agent, dim in zip(env.agent_ids, self.action_lengths):
            actual = env._dec.action_space(agent)
            low, high = np.zeros(self._act_dim, np.float32), np.zeros(self._act_dim, np.float32)
            low[:dim], high[:dim] = actual.low, actual.high
            self.action_space.append(Box(low, high, dtype=np.float32))

    def _observations(self, values):
        local = [np.asarray(o, dtype=np.float32).reshape(-1) for o in _ordered(self.env, values)]
        if tuple(len(o) for o in local) != self.observation_lengths:
            raise ValueError('observation shape changed after environment construction')
        obs = np.zeros((1, self.n_agents, self._obs_dim), dtype=np.float32)
        for i, value in enumerate(local):
            obs[0, i, :len(value)] = value
        state = np.concatenate(local)
        shared = np.broadcast_to(state, (1, self.n_agents, len(state))).copy()
        return obs, shared

    @staticmethod
    def _available():
        return np.asarray([None], dtype=object)  # continuous actions, HARL vector convention

    def reset(self, seed=None, options=None):
        obs, shared = self._observations(self.env.reset(seed=seed, options=options))
        return obs, shared, self._available()

    def step(self, actions):
        actions = np.asarray(actions)
        if actions.shape != (1, self.n_agents, self._act_dim) or not np.isfinite(actions).all():
            raise ValueError(f'action shape must be (1, {self.n_agents}, {self._act_dim}) with finite values')
        values, rewards, done, raw_infos = self.env.step(
            [actions[0, i, :dim] for i, dim in enumerate(self.action_lengths)])
        obs, shared = self._observations(values)
        dones = np.asarray([[self.env.last_terminations[a] or self.env.last_truncations[a]
                             for a in self.env.agent_ids]], dtype=bool)
        infos = [[dict(info, observation_length=self.observation_lengths[i],
                       action_length=self.action_lengths[i],
                       bad_transition=bool(self.env.last_truncations[self.env.agent_ids[i]]))
                  for i, info in enumerate(_ordered(self.env, raw_infos))]]
        if done and np.all(dones):
            # Match HARL's vector environment: preserve terminal evidence and
            # return fresh observations so the runner can continue next episode.
            infos[0][0].update(original_obs=obs[0].copy(), original_state=shared[0].copy(),
                               original_avail_actions=None)
            obs, shared, _ = self.reset()
        rewards = np.asarray(_ordered(self.env, rewards), dtype=np.float32).reshape(1, self.n_agents, 1)
        return obs, shared, rewards, dones, infos, self._available()

    def close(self):
        self.env.close()


class PettingZooWrapper(ParallelEnv):
    """Simultaneous actions, forwarding seed/options and actual ending causes."""
    metadata = {'name': 'uc3m_env_v1', 'api': 'parallel', 'is_parallelizable': True}

    def __init__(self, env: UC3MEnv):
        self.env = env
        self.possible_agents = list(env.agent_ids)
        self.agents = list(self.possible_agents)
        self._observations = {}
        self.observation_spaces = {
            a: Box(-np.inf, np.inf, shape=(d,), dtype=np.float64)
            for a, d in zip(env.agent_ids, env.observation_dimensions)}
        self.action_spaces = {a: env._dec.action_space(a) for a in env.agent_ids}

    def reset(self, seed=None, options=None):
        values = self.env.reset(seed=seed, options=options)
        self.agents = list(self.possible_agents)
        self._observations = dict(zip(self.agents, _ordered(self.env, values)))
        return self._observations.copy(), {a: {} for a in self.agents}

    def step(self, actions):
        if not self.agents:
            return {}, {}, {}, {}, {}
        if set(actions) != set(self.agents):
            raise ValueError('actions must contain exactly the active agents')
        current = list(self.agents)
        values, rewards, done, infos = self.env.step(actions)
        self._observations = dict(zip(current, _ordered(self.env, values)))
        reward_dict = dict(zip(current, _ordered(self.env, rewards)))
        info_dict = dict(zip(current, _ordered(self.env, infos)))
        terms = {a: self.env.last_terminations[a] for a in current}
        truncs = {a: self.env.last_truncations[a] for a in current}
        if done:
            self.agents = []
        return self._observations.copy(), reward_dict, terms, truncs, info_dict

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def observe(self, agent):
        return self._observations[agent]

    def state(self):
        return np.concatenate([self._observations[a] for a in self.possible_agents])

    def render(self):
        return self.env._dec.render()

    def close(self):
        self.env.close()
