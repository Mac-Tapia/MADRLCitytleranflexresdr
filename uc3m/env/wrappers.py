"""
Wrappers de compatibilidad para UC3MEnv
========================================
  • HARLWrapper   — adapta UC3MEnv a la interfaz vectorizada HARL
  • PettingZooWrapper — adapta UC3MEnv a PettingZoo AEC API

Uso típico:
    env   = UC3MEnv.from_iquitos(harl_mode=True)
    harl  = HARLWrapper(env, n_threads=4)
    # ó
    pz    = PettingZooWrapper(env)
    pz.reset(); pz.step({"agent_0": act})
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Any

from uc3m.env.uc3m_env import UC3MEnv


class HARLWrapper:
    """
    Wrapper que expone UC3MEnv como un entorno vectorizado compatible
    con el runner de HARL (share_obs + obs separados).

    HARL espera:
      obs        : list[ndarray(n_threads, obs_dim)]    por agente
      share_obs  : list[ndarray(n_threads, share_obs_dim)] por agente
      rewards    : ndarray(n_threads, n_agents)
      dones      : ndarray(n_threads, n_agents)
      infos      : list[dict]
    """

    def __init__(self, env: UC3MEnv, n_threads: int = 1):
        self.env       = env
        self.n_threads = n_threads
        self.n_agents  = env.n_agents

    def reset(self):
        obs_list = self.env.reset()
        if not isinstance(obs_list, list):
            obs_list = list(obs_list.values())

        # Expandir a (n_threads, obs_dim)
        obs       = [np.expand_dims(o, 0).repeat(self.n_threads, 0) for o in obs_list]
        share_obs = obs   # CTDE: agentes comparten observaciones globales

        return obs, share_obs, [{}] * self.n_threads

    def step(self, actions):
        """
        actions: list[ndarray(n_threads, act_dim)] por agente
        """
        # Extraer primera thread para env single-thread
        acts_list = [a[0] for a in actions]
        obs_list, rews, done, info = self.env.step(acts_list)
        if not isinstance(obs_list, list):
            obs_list = list(obs_list.values())
        if isinstance(rews, dict):
            rews_list = [rews[aid] for aid in self.env.agent_ids]
        else:
            rews_list = list(rews)

        obs       = [np.expand_dims(o, 0) for o in obs_list]
        share_obs = obs
        rewards   = np.array([[rews_list[i]] for i in range(self.n_agents)])   # (n_agents, 1)
        dones     = np.array([[done]] * self.n_agents)
        infos     = [info]

        return obs, share_obs, rewards, dones, infos

    @property
    def observation_space(self):
        """Espacio de observación CityLearn para compatibilidad."""
        return self.env.citylearn.observation_space

    @property
    def action_space(self):
        return self.env.citylearn.action_space


class PettingZooWrapper:
    """
    Wrapper que expone UC3MEnv como un entorno PettingZoo AEC
    (Agent Environment Cycle API).

    Cumple con la interfaz estándar requerida por MARLlib / PettingZoo v1.24+.
    """

    metadata = {"name": "uc3m_env_v1", "is_parallelizable": True}

    def __init__(self, env: UC3MEnv):
        self.env = env
        self.possible_agents = list(env.agent_ids)
        self.agents          = list(env.agent_ids)
        self._observations: Dict[str, np.ndarray] = {}
        self._rewards:      Dict[str, float]       = {}
        self._dones:        Dict[str, bool]        = {}
        self._infos:        Dict[str, Any]         = {}
        self._agent_idx: int = 0

    # ── AEC API ────────────────────────────────────────────────────────────

    def reset(self, seed=None, options=None):
        self.agents    = list(self.possible_agents)
        obs_list = self.env.reset()
        if not isinstance(obs_list, list):
            obs_list = list(obs_list.values())

        for i, aid in enumerate(self.agents):
            self._observations[aid] = obs_list[i]
            self._rewards[aid]      = 0.0
            self._dones[aid]        = False
            self._infos[aid]        = {}

        self._agent_idx = 0
        return self._observations.copy(), self._infos.copy()

    def step(self, actions: Dict[str, np.ndarray]):
        """Ejecuta un paso completo (todas las acciones simultáneas)."""
        acts_list = [actions.get(aid, np.zeros(self.env.action_dimension))
                     for aid in self.agents]
        obs_list, rews, done, info = self.env.step(acts_list)
        if not isinstance(obs_list, list):
            obs_list = list(obs_list.values())
        if not isinstance(rews, dict):
            rews_dict = {aid: rews[i] for i, aid in enumerate(self.agents)}
        else:
            rews_dict = rews

        for i, aid in enumerate(self.agents):
            self._observations[aid] = obs_list[i]
            self._rewards[aid]      = rews_dict.get(aid, 0.0)
            self._dones[aid]        = bool(done)
            self._infos[aid]        = info

        if done:
            self.agents = []

        return (
            self._observations.copy(),
            self._rewards.copy(),
            {aid: bool(done) for aid in self.agents or self.possible_agents},
            {aid: False for aid in self.possible_agents},
            self._infos.copy(),
        )

    def observe(self, agent: str) -> np.ndarray:
        return self._observations.get(agent, np.zeros(self.env.observation_dimension or 1))

    @property
    def observation_spaces(self) -> Dict[str, Any]:
        import gym.spaces as gs
        dim = self.env.observation_dimension or 128
        sp  = gs.Box(low=-np.inf, high=np.inf, shape=(dim,), dtype=np.float32)
        return {aid: sp for aid in self.possible_agents}

    @property
    def action_spaces(self) -> Dict[str, Any]:
        import gym.spaces as gs
        dim = self.env.action_dimension
        sp  = gs.Box(low=-1.0, high=1.0, shape=(dim,), dtype=np.float32)
        return {aid: sp for aid in self.possible_agents}

    def render(self): self.env.render()
    def close(self):  self.env.close()

    def __repr__(self) -> str:
        return f"PettingZooWrapper({self.env})"
