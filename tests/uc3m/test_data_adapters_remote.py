"""
Tests para los adaptadores remotos de ingreso de datos (HTTP/ZIP y S3)
=======================================================================
No usan red real:
  - HTTP: se sirve un .zip creado en ``tmp_path`` mediante una URL ``file://``.
  - S3: se simula la ausencia de boto3 para verificar el error claro.
"""
from __future__ import annotations

import json
import sys
import zipfile

import pytest

from uc3m.data import (
    DatasetSource,
    DatasetValidationError,
    RemoteHttpDatasetAdapter,
    S3DatasetAdapter,
    available_sources,
    build_source,
)


# ── Registry ────────────────────────────────────────────────────────────────────

class TestRemoteRegistry:
    def test_http_and_s3_registered(self):
        sources = available_sources()
        assert "http" in sources
        assert "https" in sources
        assert "s3" in sources

    def test_build_source_http_returns_port(self, tmp_path):
        cfg = {"dataset": {"source": "http", "args": {"url": "http://x/ds.zip"}}}
        src = build_source(cfg)
        assert isinstance(src, RemoteHttpDatasetAdapter)
        assert isinstance(src, DatasetSource)

    def test_build_source_s3_returns_port(self):
        cfg = {"dataset": {"source": "s3", "args": {"bucket": "b", "prefix": "p"}}}
        src = build_source(cfg)
        assert isinstance(src, S3DatasetAdapter)
        assert isinstance(src, DatasetSource)


# ── RemoteHttpDatasetAdapter (zip local vía file://) ────────────────────────────

def _make_zip_with_schema(tmp_path, buildings=4, end_step=49, inner_dir="iquitos_mini"):
    """Crea un .zip que contiene <inner_dir>/schema.json y devuelve su path."""
    schema = {
        "schema_version": 2,
        "simulation_end_time_step": end_step,
        "buildings": {f"Building_{i+1}": {} for i in range(buildings)},
    }
    zip_path = tmp_path / "dataset_source.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(f"{inner_dir}/schema.json", json.dumps(schema))
        zf.writestr(f"{inner_dir}/Building_1.csv", "a,b\n1,2\n")
    return zip_path


class TestRemoteHttpAdapter:
    def test_fetch_and_describe_from_file_url(self, tmp_path):
        zip_path = _make_zip_with_schema(tmp_path, buildings=4, end_step=49)
        cache = tmp_path / "cache"
        adapter = RemoteHttpDatasetAdapter(
            zip_path.as_uri(), name="iquitos_mini", cache_dir=cache
        )

        dataset_dir = adapter.fetch()
        assert (dataset_dir / "schema.json").is_file()

        manifest = adapter.describe()
        assert manifest.buildings == 4
        assert manifest.hours == 50  # end_step 49 + 1
        assert manifest.source_uri == zip_path.as_uri()
        assert manifest.extra.get("http_url") == zip_path.as_uri()

    def test_schema_path_points_to_schema(self, tmp_path):
        zip_path = _make_zip_with_schema(tmp_path)
        adapter = RemoteHttpDatasetAdapter(
            zip_path.as_uri(), name="ds", cache_dir=tmp_path / "cache"
        )
        assert adapter.schema_path().name == "schema.json"
        assert adapter.schema_path().is_file()

    def test_is_idempotent_no_redownload(self, tmp_path):
        zip_path = _make_zip_with_schema(tmp_path)
        cache = tmp_path / "cache"
        adapter = RemoteHttpDatasetAdapter(zip_path.as_uri(), name="ds", cache_dir=cache)
        first = adapter.fetch()

        # Borrar el zip de origen: si no es idempotente, una 2ª llamada fallaría.
        zip_path.unlink()
        second = adapter.fetch()
        assert first == second

    def test_bad_url_raises_clear_error(self, tmp_path):
        adapter = RemoteHttpDatasetAdapter(
            "file:///nonexistent/path/does_not_exist.zip",
            name="missing",
            cache_dir=tmp_path / "cache",
        )
        with pytest.raises(DatasetValidationError):
            adapter.fetch()


# ── S3DatasetAdapter (sin boto3) ────────────────────────────────────────────────

class TestS3Adapter:
    def test_missing_boto3_raises_clear_error(self, tmp_path, monkeypatch):
        # Simula boto3 no instalado: ``import boto3`` lanzará ImportError.
        monkeypatch.setitem(sys.modules, "boto3", None)
        adapter = S3DatasetAdapter(
            bucket="my-bucket", prefix="datasets/iquitos",
            cache_dir=tmp_path / "cache",
        )
        with pytest.raises(DatasetValidationError) as exc:
            adapter.fetch()
        assert "boto3" in str(exc.value)

    def test_requires_bucket(self, tmp_path):
        with pytest.raises(DatasetValidationError):
            S3DatasetAdapter(bucket="", cache_dir=tmp_path / "cache")

    def test_uri_format(self, tmp_path):
        adapter = S3DatasetAdapter(
            bucket="b", prefix="p/q", cache_dir=tmp_path / "cache"
        )
        assert adapter.uri == "s3://b/p/q"
