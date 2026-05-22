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
