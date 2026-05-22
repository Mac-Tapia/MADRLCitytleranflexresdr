"""Fixtures compartidas para el suite de tests UC3M."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Asegurar que el root del proyecto esté en sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA_PATH = (
    ROOT / "CityLearn" / "data" / "datasets"
    / "citylearn_iquitos_2023_2025" / "schema.json"
)

DATASET_DIR = SCHEMA_PATH.parent


@pytest.fixture(scope="session")
def schema_path() -> Path:
    return SCHEMA_PATH


@pytest.fixture(scope="session")
def dataset_dir() -> Path:
    return DATASET_DIR


@pytest.fixture(scope="session")
def iquitos_climate():
    from uc3m.env.bact import IQUITOS_CLIMATE
    return IQUITOS_CLIMATE


@pytest.fixture(scope="module")
def uc3m_env(iquitos_climate):
    """UC3MEnv liviano con harl_mode=False para tests de integración."""
    if not SCHEMA_PATH.exists():
        pytest.skip("schema.json no encontrado — ejecutar generate_iquitos_dataset.py primero")
    from uc3m.env.uc3m_env import UC3MEnv
    env = UC3MEnv(
        schema_path=str(SCHEMA_PATH),
        climate=iquitos_climate,
        harl_mode=False,
    )
    yield env
    env.close()


@pytest.fixture(scope="module")
def uc3m_env_harl(iquitos_climate):
    """UC3MEnv en harl_mode=True para tests HARL."""
    if not SCHEMA_PATH.exists():
        pytest.skip("schema.json no encontrado")
    from uc3m.env.uc3m_env import UC3MEnv
    env = UC3MEnv(
        schema_path=str(SCHEMA_PATH),
        climate=iquitos_climate,
        harl_mode=True,
    )
    yield env
    env.close()
