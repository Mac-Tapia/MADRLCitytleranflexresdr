"""Smoke tests for the CityLearn v3 Iquitos dataset schema.

These tests validate structural integrity of the canonical dataset
(`CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`) without
depending on a CityLearn v3 runtime install. They complement the
`uc3m` test suite (which covers the UC3M framework layer) by covering the
CityLearn v3 dataset/schema layer referenced in `docs/workflow_manifest.json`.
"""
from __future__ import annotations

from pathlib import Path


def test_schema_file_exists(schema_path: Path) -> None:
    assert schema_path.is_file(), f"Missing schema at {schema_path}"


def test_schema_has_buildings(schema: dict) -> None:
    buildings = schema.get("buildings")
    assert isinstance(buildings, dict)
    assert len(buildings) == 17, "Expected 17 buildings per workflow_manifest.json"


def test_schema_building_csvs_exist(schema: dict, dataset_dir: Path) -> None:
    buildings = schema.get("buildings", {})
    missing = []
    for name, cfg in buildings.items():
        energy_simulation = cfg.get("energy_simulation")
        if energy_simulation and not (dataset_dir / energy_simulation).is_file():
            missing.append((name, energy_simulation))
    assert not missing, f"Missing referenced building CSV files: {missing}"


def test_schema_observations_and_actions_present(schema: dict) -> None:
    assert "observations" in schema
    assert "actions" in schema
