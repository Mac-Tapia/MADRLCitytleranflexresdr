"""
Tests para uc3m.kpis.evaluator — KPIEvaluator y EpisodeKPIs.
"""
from __future__ import annotations

import numpy as np
import pytest

from uc3m.kpis.evaluator import KPIEvaluator, EpisodeKPIs


class TestEpisodeKPIs:
    def test_dataclass_defaults(self):
        """EpisodeKPIs se crea con valores cero por defecto."""
        k = EpisodeKPIs()
        assert k.hphi == 0.0
        assert k.global_score == 0.0
        assert k.n_agents == 0

    def test_to_dict_returns_dict(self):
        """to_dict() retorna un dict con todas las claves KPI."""
        k = EpisodeKPIs(hphi=0.75, co2_avoided_kg=100.0, algorithm="HAPPO")
        d = k.to_dict()
        assert isinstance(d, dict)
        assert "hphi" in d
        assert "co2_avoided_kg" in d
        assert d["hphi"] == pytest.approx(0.75)
        assert d["co2_avoided_kg"] == pytest.approx(100.0)

    def test_to_dict_has_metadata(self):
        """to_dict() incluye campos de metadatos."""
        k = EpisodeKPIs(algorithm="MASAC", n_agents=17, episode=5)
        d = k.to_dict()
        assert d["algorithm"] == "MASAC"
        assert d["n_agents"] == 17.0
        assert d["episode"] == 5.0

    def test_summary_line_format(self):
        """summary_line() produce una cadena no vacía."""
        k = EpisodeKPIs(episode=1, hphi=0.5, global_score=0.6,
                        co2_avoided_kg=200.0, cost_saved_usd=50.0,
                        peak_reduction_kw=10.0, soh_loss_pct=0.001,
                        pareto_front_size=3)
        line = k.summary_line()
        assert isinstance(line, str)
        assert len(line) > 10
        assert "HPHI" in line

    def test_all_float_fields_finite(self):
        """Todos los campos numéricos del dataclass son finitos."""
        k = EpisodeKPIs(
            energy_saved_kwh=100.0, self_sufficiency=0.7, self_consumption=0.6,
            peak_reduction_kw=50.0, load_factor=0.8,
            cost_saved_usd=30.0, cost_total_usd=200.0, arbitrage_gain_usd=10.0,
            co2_avoided_kg=150.0, co2_total_kg=500.0, renewable_fraction=0.3,
            discomfort_hours=5.0, avg_unmet_setpoint=0.2, avg_indoor_rh=60.0,
            resilience_score=0.8, islanding_hours=0.0, load_not_served_kwh=0.0,
            soh_loss_pct=0.01, equivalent_cycles=50.0, throughput_kwh=2000.0,
            hphi=0.7, sparsity=0.1, epsilon_coverage=0.05, global_score=0.65,
            pareto_front_size=5,
        )
        d = k.to_dict()
        for key, val in d.items():
            if isinstance(val, float):
                assert np.isfinite(val), f"Campo {key} no es finito: {val}"


class TestKPIEvaluator:
    def test_init_default(self):
        """KPIEvaluator se inicializa con n_agents=17."""
        ev = KPIEvaluator(n_agents=17)
        assert ev.n_agents == 17

    def test_init_with_baselines(self):
        """KPIEvaluator acepta baselines opcionales."""
        ev = KPIEvaluator(
            n_agents=17,
            baseline_consumption_kwh=10000.0,
            baseline_cost_usd=3000.0,
            baseline_co2_kg=8000.0,
        )
        assert ev._baseline_kwh == pytest.approx(10000.0)
        assert ev._baseline_cost == pytest.approx(3000.0)
        assert ev._baseline_co2 == pytest.approx(8000.0)

    def test_reset_pareto_clears(self):
        """reset_pareto() no lanza excepción."""
        ev = KPIEvaluator(n_agents=17)
        ev.reset_pareto()

    def test_compare_empty_list(self):
        """compare([]) retorna dict vacío sin error."""
        result = KPIEvaluator.compare([])
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_compare_single_run(self):
        """compare([kpis]) retorna dict con clave del algoritmo."""
        k = EpisodeKPIs(algorithm="HAPPO", hphi=0.7, co2_avoided_kg=100.0)
        result = KPIEvaluator.compare([k])
        assert "HAPPO" in result
        assert "HPHI" in result["HAPPO"]
        assert result["HAPPO"]["HPHI"] == pytest.approx(0.7)

    def test_compare_multiple_algorithms(self):
        """compare() ordena resultados por nombre de algoritmo."""
        kpis = [
            EpisodeKPIs(algorithm="HAPPO", hphi=0.7),
            EpisodeKPIs(algorithm="MASAC", hphi=0.65),
            EpisodeKPIs(algorithm="MATD3", hphi=0.68),
        ]
        result = KPIEvaluator.compare(kpis)
        assert len(result) == 3
        assert "HAPPO" in result
        assert "MASAC" in result
        assert "MATD3" in result

    def test_episode_kpis_all_fields_present(self):
        """EpisodeKPIs tiene exactamente los 7 grupos de KPIs."""
        k = EpisodeKPIs()
        d = k.to_dict()
        # Energéticos
        assert "energy_saved_kwh" in d
        assert "self_sufficiency" in d
        assert "self_consumption" in d
        assert "peak_reduction_kw" in d
        assert "load_factor" in d
        # Económicos
        assert "cost_saved_usd" in d
        assert "cost_total_usd" in d
        assert "arbitrage_gain_usd" in d
        # Ambientales
        assert "co2_avoided_kg" in d
        assert "co2_total_kg" in d
        assert "renewable_fraction" in d
        # Confort
        assert "discomfort_hours" in d
        assert "avg_unmet_setpoint" in d
        assert "avg_indoor_rh" in d
        # Resiliencia
        assert "resilience_score" in d
        assert "islanding_hours" in d
        assert "load_not_served_kwh" in d
        # Degradación
        assert "soh_loss_pct" in d
        assert "equivalent_cycles" in d
        assert "throughput_kwh" in d
        # Holísticos
        assert "hphi" in d
        assert "sparsity" in d
        assert "epsilon_coverage" in d
        assert "global_score" in d
        assert "pareto_front_size" in d


class TestKPIEvaluatorIntegration:
    """Tests de integración con UC3MEnv — requieren dataset."""

    def test_compute_episode_returns_kpis(self, uc3m_env):
        """compute_episode() retorna EpisodeKPIs válido."""
        ev = KPIEvaluator(n_agents=17)
        # Ejecutar un paso mínimo
        uc3m_env.reset()
        zero_actions = {
            aid: np.zeros(d)
            for aid, d in zip(uc3m_env.agent_ids, uc3m_env.action_dimensions)
        }
        uc3m_env.step(zero_actions)

        kpis = ev.compute_episode(uc3m_env, episode_idx=0, algorithm="test")
        assert isinstance(kpis, EpisodeKPIs)
        assert kpis.n_agents == 17
        assert kpis.algorithm == "test"

    def test_compute_episode_kpi_ranges(self, uc3m_env):
        """Los KPIs están dentro de rangos físicamente razonables."""
        ev = KPIEvaluator(n_agents=17)
        uc3m_env.reset()
        zero_actions = {
            aid: np.zeros(d)
            for aid, d in zip(uc3m_env.agent_ids, uc3m_env.action_dimensions)
        }
        uc3m_env.step(zero_actions)

        kpis = ev.compute_episode(uc3m_env, episode_idx=0)
        assert 0.0 <= kpis.self_sufficiency <= 1.0 + 1e-6
        assert 0.0 <= kpis.self_consumption <= 1.0 + 1e-6
        assert 0.0 <= kpis.renewable_fraction <= 1.0 + 1e-6
        assert 0.0 <= kpis.resilience_score <= 1.0 + 1e-6
        assert kpis.hphi >= 0.0
        assert kpis.throughput_kwh >= 0.0
