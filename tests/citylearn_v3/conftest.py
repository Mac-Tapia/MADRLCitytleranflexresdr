"""Fixtures compartidas para tests del dataset/schema CityLearn v3 (Iquitos)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

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
def schema(schema_path: Path) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)
