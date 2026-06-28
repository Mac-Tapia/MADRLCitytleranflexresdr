"""
Tests para uc3m.data — interfaces de ingreso de datos (Ports & Adapters)
========================================================================
Cubre: contrato DatasetSource, LocalCsvDatasetAdapter, validación del
manifest y selección por configuración (registry).
"""
from __future__ import annotations

import json

import pytest

from uc3m.data import (
    DatasetManifest,
    DatasetSource,
    DatasetValidationError,
    LocalCsvDatasetAdapter,
    available_sources,
    build_source,
)


# ── DatasetManifest (validación de frontera) ───────────────────────────────────

class TestDatasetManifest:
    def test_valid_manifest(self):
        m = DatasetManifest(name="iquitos", source_uri="file:///x", buildings=17, hours=8760)
        assert m.buildings == 17
        assert m.to_dict()["name"] == "iquitos"

    def test_rejects_zero_buildings(self):
        with pytest.raises(DatasetValidationError):
            DatasetManifest(name="x", source_uri="file:///x", buildings=0, hours=10)

    def test_rejects_empty_name(self):
        with pytest.raises(DatasetValidationError):
            DatasetManifest(name="", source_uri="file:///x", buildings=1, hours=10)

    def test_rejects_zero_hours(self):
        with pytest.raises(DatasetValidationError):
            DatasetManifest(name="x", source_uri="file:///x", buildings=1, hours=0)


# ── LocalCsvDatasetAdapter ──────────────────────────────────────────────────────

class TestLocalCsvAdapter:
    def _make_dataset(self, tmp_path, buildings=3, end_step=23):
        schema = {
            "schema_version": 2,
            "simulation_end_time_step": end_step,
            "buildings": {f"Building_{i+1}": {} for i in range(buildings)},
        }
        (tmp_path / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
        return tmp_path

    def test_satisfies_port_protocol(self, tmp_path):
        self._make_dataset(tmp_path)
        adapter = LocalCsvDatasetAdapter(tmp_path)
        assert isinstance(adapter, DatasetSource)

    def test_fetch_returns_dir(self, tmp_path):
        self._make_dataset(tmp_path)
        adapter = LocalCsvDatasetAdapter(tmp_path)
        assert adapter.fetch() == tmp_path.resolve()

    def test_fetch_missing_schema_raises(self, tmp_path):
        adapter = LocalCsvDatasetAdapter(tmp_path)
        with pytest.raises(DatasetValidationError):
            adapter.fetch()

    def test_describe_counts_buildings(self, tmp_path):
        self._make_dataset(tmp_path, buildings=5, end_step=99)
        m = LocalCsvDatasetAdapter(tmp_path, name="mini").describe()
        assert m.buildings == 5
        assert m.hours == 100          # end_step 99 + 1
        assert m.name == "mini"
        assert len(m.content_hash) == 16

    def test_describe_hash_is_deterministic(self, tmp_path):
        self._make_dataset(tmp_path)
        a = LocalCsvDatasetAdapter(tmp_path).describe()
        b = LocalCsvDatasetAdapter(tmp_path).describe()
        assert a.content_hash == b.content_hash


# ── Registry (selección por configuración) ──────────────────────────────────────

class TestRegistry:
    def test_local_is_available(self):
        assert "local" in available_sources()

    def test_build_source_local(self, tmp_path):
        (tmp_path / "schema.json").write_text(
            json.dumps({"buildings": {"Building_1": {}}, "simulation_end_time_step": 9}),
            encoding="utf-8",
        )
        cfg = {"dataset": {"source": "local", "args": {"dataset_dir": str(tmp_path)}}}
        src = build_source(cfg)
        assert isinstance(src, DatasetSource)
        assert src.describe().buildings == 1

    def test_unknown_source_raises(self):
        with pytest.raises(KeyError):
            build_source({"dataset": {"source": "ftp", "args": {}}})
