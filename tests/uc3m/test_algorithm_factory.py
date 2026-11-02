"""
Tests para uc3m.algorithms.factory — AlgorithmFactory.
"""
from __future__ import annotations

import pytest

from uc3m.algorithms.factory import AlgorithmFactory, _ALL_ALGOS


class TestAlgorithmRegistry:
    def test_all_algos_nonempty(self):
        """_ALL_ALGOS debe tener al menos 18 algoritmos."""
        assert len(_ALL_ALGOS) >= 18

    def test_harl_algos_present(self):
        """Los 5 algoritmos HARL deben estar registrados."""
        harl = {"HAPPO", "HATRPO", "HATD3", "HASAC", "MAA2C"}
        assert harl.issubset(_ALL_ALGOS)

    def test_offpolicy_algos_present(self):
        """Los 3 algoritmos off-policy deben estar registrados."""
        offpolicy = {"MASAC", "MATD3", "MAAC"}
        assert offpolicy.issubset(_ALL_ALGOS)

    def test_marllib_algos_present(self):
        """Algoritmos MARLlib clave deben estar registrados."""
        marllib_key = {"MAPPO", "QMIX", "IPPO", "MADDPG"}
        assert marllib_key.issubset(_ALL_ALGOS)

    def test_list_algorithms(self):
        """list_algorithms() retorna dict con al menos 3 backends."""
        algos = AlgorithmFactory.list_algorithms()
        assert isinstance(algos, dict)
        assert len(algos) >= 3

    def test_happo_in_harl_backend(self):
        algos = AlgorithmFactory.list_algorithms()
        harl_names = algos.get("HARL", [])
        assert "HAPPO" in harl_names

    def test_masac_in_offpolicy_backend(self):
        algos = AlgorithmFactory.list_algorithms()
        offpolicy_names = algos.get("off-policy", [])
        assert "MASAC" in offpolicy_names


class TestAlgorithmFactoryCreate:
    def test_unknown_algorithm_raises(self, uc3m_env):
        """AlgorithmFactory.create() con algoritmo desconocido → ValueError."""
        with pytest.raises((ValueError, KeyError, NotImplementedError)):
            AlgorithmFactory.create(
                algorithm="NONEXISTENT_ALGO",
                env=uc3m_env,
                cfg={},
                checkpoint_dir=None,
            )

    def test_happo_creates_without_error(self, uc3m_env_harl, tmp_path):
        """HAPPO (HARL) se instancia sin error."""
        try:
            algo = AlgorithmFactory.create(
                algorithm="HAPPO",
                env=uc3m_env_harl,
                cfg={"lr_actor": 1e-4, "lr_critic": 1e-4},
                checkpoint_dir=tmp_path,
            )
            assert algo is not None
        except (ImportError, ModuleNotFoundError):
            pytest.skip("HARL no disponible")
        except Exception as e:
            # Puede fallar si HARL necesita configuración específica
            if "harl" in str(e).lower() or "import" in str(e).lower():
                pytest.skip(f"HARL no configurado: {e}")
            raise

    def test_masac_creates_without_error(self, uc3m_env, tmp_path):
        """MASAC (off-policy) se instancia sin error."""
        try:
            algo = AlgorithmFactory.create(
                algorithm="MASAC",
                env=uc3m_env,
                cfg={"lr_actor": 3e-4, "lr_critic": 3e-4, "buffer_size": 1000},
                checkpoint_dir=tmp_path,
            )
            assert algo is not None
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Off-policy backend no disponible")
        except Exception as e:
            if "import" in str(e).lower():
                pytest.skip(f"Backend no configurado: {e}")
            raise


class _TinyEnv:
    """Two agents, one action each; enough to drive a placeholder loop."""
    n_agents = 2
    action_dimension = 1
    observation_dimension = 3
    time_steps = 4
    harl_mode = True

    def reset(self):
        return [[0.0]*3]*2

    def step(self, actions):
        return [[0.0]*3]*2, [0.0, 0.0], False, {}


class TestNoPlaceholderLearning:
    """P02/A15: a missing backend never trains with random actions or announces a model."""

    @pytest.mark.parametrize("algorithm", ["HAPPO", "MASAC", "MAPPO"])
    def test_missing_backend_fails_instead_of_random_learning(self, algorithm, tmp_path):
        from uc3m.algorithms.factory import BackendUnavailable
        algo = AlgorithmFactory.create(algorithm, _TinyEnv(), cfg={}, checkpoint_dir=tmp_path)
        # MARLlib may be importable, but its adapter never trains: it must fail as well.
        if getattr(algo, "_trainer", None) is not None:
            pytest.fail(f"{algorithm}: unexpected native backend in this environment")
        with pytest.raises(BackendUnavailable):
            algo.learn(total_timesteps=3)

    @pytest.mark.parametrize("algorithm", ["HAPPO", "MASAC"])
    def test_explicit_smoke_is_never_eligible_for_promotion(self, algorithm, tmp_path):
        algo = AlgorithmFactory.create(algorithm, _TinyEnv(), cfg={"smoke": True}, checkpoint_dir=tmp_path)
        result = algo.learn(total_timesteps=3)
        assert result["smoke"] is True
        assert result["promotion_eligible"] is False
        assert result["learned"] is False

    @pytest.mark.parametrize("algorithm", ["HAPPO", "MASAC", "MAPPO"])
    def test_save_without_model_does_not_announce_a_checkpoint(self, algorithm, tmp_path):
        from uc3m.algorithms.factory import BackendUnavailable
        algo = AlgorithmFactory.create(algorithm, _TinyEnv(), cfg={"smoke": True}, checkpoint_dir=tmp_path)
        with pytest.raises(BackendUnavailable):
            algo.save(tmp_path/"model_final")
        assert not (tmp_path/"model_final").exists()
