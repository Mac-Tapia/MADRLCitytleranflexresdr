"""
Tests de integración para uc3m.env.uc3m_env — UC3MEnv.
"""
from __future__ import annotations

import numpy as np

from uc3m.env.bact import IQUITOS_CLIMATE


class TestUC3MEnvUnit:
    """Tests unitarios que no requieren CityLearn ni el dataset."""

    def test_bact_dim_constant(self):
        """BACTTensor.dim == 29 (KA + KC + KB)."""
        from uc3m.env.bact import KA, KC, KB
        assert KA + KC + KB == 29

    def test_reward_axes_creation(self):
        """RewardAxes se crea sin error con lambdas por defecto."""
        from uc3m.reward.axes import RewardAxes
        ax = RewardAxes()
        assert ax is not None

    def test_default_lambdas_simplex(self):
        """DEFAULT_LAMBDAS suma a 1 (simplex)."""
        from uc3m.reward.axes import DEFAULT_LAMBDAS
        assert abs(DEFAULT_LAMBDAS.sum() - 1.0) < 1e-9

    def test_iquitos_climate_correct_location(self):
        """IQUITOS_CLIMATE tiene coordenadas válidas."""
        c = IQUITOS_CLIMATE
        assert -10 < c.lat < 0        # Amazonas sur
        assert -80 < c.lon < -65      # longitud oeste Perú
        assert c.alt_m > 0

    def test_climate_vector_array_length(self):
        """to_array() del clima de Iquitos produce KC=8 elementos."""
        from uc3m.env.bact import KC
        arr = IQUITOS_CLIMATE.to_array()
        assert len(arr) == KC


class TestUC3MEnvIntegration:
    """Tests de integración — requieren dataset y CityLearn."""

    def test_env_creates(self, uc3m_env):
        """UC3MEnv (harl_mode=False) se instancia sin error."""
        assert uc3m_env is not None

    def test_n_agents_17(self, uc3m_env):
        """El dataset de Iquitos tiene 17 agentes."""
        assert uc3m_env.n_agents == 17

    def test_n_buildings_equals_n_agents(self, uc3m_env):
        """n_buildings == n_agents."""
        assert uc3m_env.n_buildings == uc3m_env.n_agents

    def test_action_dimensions_length(self, uc3m_env):
        """action_dimensions es una lista de longitud n_agents."""
        dims = uc3m_env.action_dimensions
        assert len(dims) == uc3m_env.n_agents

    def test_action_dimensions_all_positive(self, uc3m_env):
        """Cada agente tiene al menos 1 dimensión de acción."""
        for d in uc3m_env.action_dimensions:
            assert d >= 1

    def test_action_dimension_max(self, uc3m_env):
        """action_dimension es el máximo de action_dimensions."""
        assert uc3m_env.action_dimension == max(uc3m_env.action_dimensions)

    def test_reset_returns_correct_type_dict(self, uc3m_env):
        """reset() con harl_mode=False devuelve dict."""
        obs = uc3m_env.reset()
        assert isinstance(obs, dict)

    def test_reset_returns_17_keys(self, uc3m_env):
        """reset() devuelve observación para los 17 agentes."""
        obs = uc3m_env.reset()
        assert len(obs) == 17

    def test_observation_shape_after_reset(self, uc3m_env):
        """Cada observación es un ndarray 1D con longitud > 29 (BACT + obs CityLearn).
        Los edificios con distinto número de cargadores EV tienen obs heterogéneas."""
        obs = uc3m_env.reset()
        obs_dim = uc3m_env.observation_dimension   # máximo entre agentes
        assert obs_dim is not None and obs_dim > 29
        for v in obs.values():
            arr = np.asarray(v)
            assert arr.ndim == 1
            assert len(arr) > 29          # al menos BACT (29) + algo de CityLearn
            assert len(arr) <= obs_dim    # ningún agente supera el máximo

    def test_observation_no_nan(self, uc3m_env):
        """Las observaciones iniciales no contienen NaN ni Inf."""
        obs = uc3m_env.reset()
        for v in obs.values():
            arr = np.asarray(v, dtype=float)
            assert not np.any(np.isnan(arr)), "NaN en observación"
            assert not np.any(np.isinf(arr)), "Inf en observación"

    def test_step_with_zero_actions(self, uc3m_env):
        """step() con acciones cero no lanza excepción."""
        uc3m_env.reset()
        zero_actions = {
            aid: np.zeros(d)
            for aid, d in zip(uc3m_env.agent_ids, uc3m_env.action_dimensions)
        }
        obs, rewards, done, info = uc3m_env.step(zero_actions)
        assert obs is not None
        assert len(rewards) == 17

    def test_rewards_are_finite(self, uc3m_env):
        """Las recompensas del primer paso son finitas."""
        uc3m_env.reset()
        zero_actions = {
            aid: np.zeros(d)
            for aid, d in zip(uc3m_env.agent_ids, uc3m_env.action_dimensions)
        }
        _, rewards, _, _ = uc3m_env.step(zero_actions)
        for r in (rewards.values() if isinstance(rewards, dict) else rewards):
            assert np.isfinite(float(r)), f"Recompensa no finita: {r}"

    def test_time_steps_positive(self, uc3m_env):
        """time_steps > 0 después de reset."""
        uc3m_env.reset()
        assert uc3m_env.time_steps > 0

    def test_citylearn_property(self, uc3m_env):
        """La propiedad .citylearn devuelve el env interno."""
        cl = uc3m_env.citylearn
        assert cl is not None
        assert hasattr(cl, "buildings")


class TestUC3MEnvHARL:
    """Tests específicos para harl_mode=True."""

    def test_env_harl_creates(self, uc3m_env_harl):
        """UC3MEnv en harl_mode=True se instancia."""
        assert uc3m_env_harl is not None
        assert uc3m_env_harl.harl_mode is True

    def test_reset_returns_list(self, uc3m_env_harl):
        """reset() con harl_mode=True devuelve lista."""
        obs = uc3m_env_harl.reset()
        assert isinstance(obs, list)

    def test_reset_list_length_17(self, uc3m_env_harl):
        """reset() en HARL devuelve lista de 17 elementos."""
        obs = uc3m_env_harl.reset()
        assert len(obs) == 17

    def test_step_with_list_actions(self, uc3m_env_harl):
        """step() acepta lista de acciones en harl_mode=True."""
        uc3m_env_harl.reset()
        actions = [
            np.zeros(d)
            for d in uc3m_env_harl.action_dimensions
        ]
        obs, rewards, done, info = uc3m_env_harl.step(actions)
        assert isinstance(obs, list)
        assert isinstance(rewards, list)
        assert len(rewards) == 17
