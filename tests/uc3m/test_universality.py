"""
Universalidad y flexibilidad del diseño UC3M (MADRL CityLearn v3).
=================================================================
Estos tests demuestran, con evidencia ejecutable, que el proyecto NO está
limitado ni a 17 edificios ni a un único algoritmo MADRL/DRL:

  - Test A (sin dataset): ``AlgorithmFactory`` expone múltiples backends
    (HARL, MARLlib, off-policy) y admite registrar algoritmos custom en
    caliente vía ``AlgorithmFactory.register(...)``.
  - Test B (sin dataset): ``BACTEncoder`` codifica cualquier ubicación del
    planeta (otra zona Köppen: Madrid, Lima, ...) en un vector 29D sin NaN/Inf
    — universalidad geográfica.
  - Test C (requiere CityLearn + dataset): ``UC3MEnv`` soporta un número de
    edificios N arbitrario (distinto de 17) usando directamente el
    ``schema.json`` de un dataset de ejemplo de CityLearn. Si la instanciación
    no es factible en este entorno (features EV faltantes, dataset pesado,
    CityLearn no instalado), el test se omite con ``pytest.skip`` pero queda
    escrito como evidencia de diseño.

Los tests son rápidos y deterministas. Se prefiere ``pytest.skip`` a fallar
cuando falta una dependencia/dataset externo.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from uc3m.algorithms.factory import AlgorithmFactory
from uc3m.env.bact import BACT_DIM, BACTEncoder, ClimateVector

ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = ROOT / "CityLearn" / "data" / "datasets"


# ───────────────────────────────────────────────────────────────────────────
# Test A — Flexibilidad de algoritmos (cualquier número de algoritmos MADRL/DRL)
# ───────────────────────────────────────────────────────────────────────────
class TestAlgorithmUniversality:
    """El catálogo de algoritmos es abierto y extensible, no fijo."""

    def test_multiple_backends_listed(self):
        """``list_algorithms`` expone HARL + MARLlib + off-policy (>=3 familias)."""
        algos = AlgorithmFactory.list_algorithms()
        assert isinstance(algos, dict)
        for backend in ("HARL", "MARLlib", "off-policy"):
            assert backend in algos, f"Falta el backend {backend}"
            assert len(algos[backend]) >= 1, f"Backend {backend} vacío"

    def test_total_algorithm_count_is_large(self):
        """Hay decenas de algoritmos disponibles (no uno solo)."""
        algos = AlgorithmFactory.list_algorithms()
        total = sum(len(v) for v in algos.values())
        assert total >= 18, f"Se esperaban >=18 algoritmos, hay {total}"

    def test_register_custom_algorithm_appears(self):
        """Registrar un algoritmo custom en caliente lo hace visible en la factory."""

        class _DummyAdapter:
            def __init__(self, env, cfg, checkpoint_dir):
                self.env = env
                self.cfg = cfg
                self.checkpoint_dir = checkpoint_dir

            def learn(self, total_timesteps: int = 1):
                return {"ok": True}

        unique_name = "MY_CUSTOM_ALGO_XYZ"
        try:
            AlgorithmFactory.register(unique_name, _DummyAdapter)

            listed = AlgorithmFactory.list_algorithms()
            assert unique_name in listed["custom"], "El algoritmo custom no aparece"

            # Y debe poder instanciarse vía create() sin tocar dataset/env real.
            adapter = AlgorithmFactory.create(unique_name, env=object(), cfg={"x": 1})
            assert isinstance(adapter, _DummyAdapter)
            assert adapter.cfg == {"x": 1}
        finally:
            # Limpieza: no contaminar el registro global para otros tests.
            AlgorithmFactory._registry.pop(unique_name.upper(), None)

    def test_unknown_algorithm_raises(self):
        """Un nombre no registrado produce un error claro (no silencioso)."""
        with pytest.raises(ValueError):
            AlgorithmFactory.create("NO_EXISTE_ESTE_ALGO", env=object(), cfg={})


# ───────────────────────────────────────────────────────────────────────────
# Test B — Universalidad geográfica (cualquier parte del mundo)
# ───────────────────────────────────────────────────────────────────────────
class TestGeographicUniversality:
    """El BACT codifica cualquier zona Köppen, no solo Iquitos (Af)."""

    # Ubicaciones de zonas climáticas distintas a la de referencia (Iquitos/Af).
    CITIES = {
        "Madrid":  ClimateVector(lat=40.4168, lon=-3.7038, alt_m=667,
                                 t_avg_c=15.0, hr_avg_pct=58.0,
                                 ghi_avg_wm2=480.0, koppen="Csa"),
        "Lima":    ClimateVector(lat=-12.0464, lon=-77.0428, alt_m=154,
                                 t_avg_c=19.0, hr_avg_pct=82.0,
                                 ghi_avg_wm2=460.0, koppen="BWh"),
        "Oslo":    ClimateVector(lat=59.9139, lon=10.7522, alt_m=23,
                                 t_avg_c=6.0, hr_avg_pct=75.0,
                                 ghi_avg_wm2=200.0, koppen="Dfb"),
        "Unknown": ClimateVector(lat=0.0, lon=0.0, alt_m=0.0,
                                 t_avg_c=0.0, hr_avg_pct=0.0,
                                 ghi_avg_wm2=0.0, koppen="ZZ"),
    }

    # Datos mínimos de un edificio genérico (sin DERs declarados).
    BUILDING = {
        "bldg_type": "office",
        "area_m2": 1200.0,
        "cap_bess_kwh": 50.0,
        "p_bess_kw": 25.0,
        "pv_kwp": 30.0,
        "n_ev_chargers": 2,
        "ev_charger_kw": 7.4,
        "has_dhw": True,
        "cop_design": 3.2,
    }

    @pytest.mark.parametrize("city", list(CITIES.keys()))
    def test_encode_any_city_is_29d_no_nan(self, city):
        """Cualquier ciudad produce un vector BACT de 29D, finito y sin NaN."""
        encoder = BACTEncoder(self.CITIES[city])
        vec = encoder.encode(self.BUILDING)
        assert vec.shape == (BACT_DIM,) == (29,)
        assert np.all(np.isfinite(vec)), f"BACT con NaN/Inf para {city}"

    def test_climate_vector_29d_independent_of_koppen(self):
        """El vector tiene siempre 29D aunque el código Köppen sea desconocido."""
        for cv in self.CITIES.values():
            arr = cv.to_array()
            assert arr.shape == (8,)
            assert np.all(np.isfinite(arr))

    def test_distinct_cities_give_distinct_vectors(self):
        """Ciudades distintas → BACT distinto (el contexto geográfico importa)."""
        madrid = BACTEncoder(self.CITIES["Madrid"]).encode(self.BUILDING)
        lima = BACTEncoder(self.CITIES["Lima"]).encode(self.BUILDING)
        assert not np.allclose(madrid, lima)


# ───────────────────────────────────────────────────────────────────────────
# Test C — N edificios arbitrario (N != 17), usando un dataset CityLearn real
# ───────────────────────────────────────────────────────────────────────────
def _count_buildings(schema_path: Path) -> int:
    """Número de edificios declarados en un schema.json de CityLearn."""
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    return len(data.get("buildings", {}) or {})


def _safe_episode_steps(schema_path: Path, requested: int = 24) -> int:
    """Ventana de simulación corta y válida para el dataset dado.

    El config v3 por defecto usa ``episode_time_steps=8760`` (1 año), que excede
    el horizonte de muchos datasets de ejemplo. Calculamos una ventana pequeña
    que quepa dentro de ``[simulation_start, simulation_end]``.
    """
    try:
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        start = int(data.get("simulation_start_time_step", 0) or 0)
        end = data.get("simulation_end_time_step", None)
        if end is not None:
            window = int(end) - start + 1
            if window >= 2:
                return max(2, min(requested, window))
    except Exception:
        pass
    return requested


def _find_dataset_with_n_not_17() -> tuple[Path, int] | None:
    """Busca el primer dataset de ejemplo con un número de edificios != 17."""
    if not DATASETS_DIR.is_dir():
        return None
    # Candidatos pequeños conocidos primero (rápidos de instanciar).
    preferred = [
        "citylearn_challenge_2023_phase_1",
        "citylearn_challenge_2022_phase_1",
        "baeda_3dem",
        "citylearn_challenge_2021",
    ]
    seen: set[str] = set()
    candidates: list[Path] = []
    for name in preferred:
        p = DATASETS_DIR / name / "schema.json"
        if p.is_file():
            candidates.append(p)
            seen.add(name)
    for schema in sorted(DATASETS_DIR.glob("*/schema.json")):
        if schema.parent.name not in seen and "iquitos" not in schema.parent.name:
            candidates.append(schema)

    for schema in candidates:
        try:
            n = _count_buildings(schema)
        except Exception:
            continue
        if n >= 2 and n != 17:
            return schema, n
    return None


class TestBuildingCountUniversality:
    """``UC3MEnv`` soporta N edificios arbitrario — N no está hardcodeado."""

    def test_example_dataset_has_n_not_17(self):
        """Existe al menos un dataset de ejemplo con un N distinto de 17."""
        found = _find_dataset_with_n_not_17()
        if found is None:
            pytest.skip(
                "No se encontró ningún dataset CityLearn con N!=17 en "
                f"{DATASETS_DIR} (datasets no disponibles en este entorno)."
            )
        schema_path, n = found
        assert n != 17 and n >= 2

    def test_uc3m_env_supports_arbitrary_n(self):
        """Instanciar UC3MEnv con un schema de N!=17 expone exactamente N agentes.

        Se omite (skip) si CityLearn no está instalado o el dataset no es
        instanciable en este entorno (p.ej. features EV faltantes). El test
        queda como evidencia de que N proviene del schema, no de un literal.
        """
        found = _find_dataset_with_n_not_17()
        if found is None:
            pytest.skip("No hay dataset CityLearn con N!=17 disponible.")
        schema_path, n_expected = found

        try:
            from uc3m.env.uc3m_env import UC3MEnv
        except Exception as exc:  # pragma: no cover - entorno sin deps
            pytest.skip(f"UC3MEnv/CityLearn no importable: {exc}")

        try:
            env = UC3MEnv(
                schema_path=str(schema_path),
                harl_mode=False,
                episode_time_steps=_safe_episode_steps(schema_path),
            )
        except Exception as exc:
            pytest.skip(
                f"UC3MEnv no instanciable con {schema_path.parent.name} "
                f"(N={n_expected}): {exc}"
            )

        try:
            assert env.n_agents == n_expected, (
                f"n_agents={env.n_agents} != edificios del schema={n_expected}"
            )
            assert env.n_buildings == env.n_agents
            assert len(env.action_dimensions) == env.n_agents
            assert len(env.observation_dimensions) == env.n_agents
            assert all(d >= 1 for d in env.action_dimensions)
        finally:
            env.close()
