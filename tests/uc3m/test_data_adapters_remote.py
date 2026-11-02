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


# ── P12/A26: identidad de contenido, cuotas y caché segura ─────────────────────

import hashlib  # noqa: E402
import stat  # noqa: E402

from uc3m.data import LocalCsvDatasetAdapter  # noqa: E402


def _zip(path, members):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in members.items():
            zf.writestr(name, payload)
    return path


def _schema_zip(path, csv_payload="a,b\n1,2\n"):
    schema = json.dumps({"schema_version": 2, "simulation_end_time_step": 9, "buildings": {"Building_1": {}}})
    return _zip(path, {"ds/schema.json": schema, "ds/Building_1.csv": csv_payload})


class TestContentIdentity:
    def test_csv_change_with_same_schema_changes_content_hash(self, tmp_path):
        (tmp_path / "schema.json").write_text(json.dumps({"buildings": {"Building_1": {}}}), encoding="utf-8")
        (tmp_path / "Building_1.csv").write_text("a\n1\n", encoding="utf-8")
        before = LocalCsvDatasetAdapter(tmp_path).describe().content_hash
        (tmp_path / "Building_1.csv").write_text("a\n2\n", encoding="utf-8")
        after = LocalCsvDatasetAdapter(tmp_path).describe().content_hash
        assert before != after

    def test_content_hash_is_full_sha256(self, tmp_path):
        (tmp_path / "schema.json").write_text(json.dumps({"buildings": {"Building_1": {}}}), encoding="utf-8")
        content_hash = LocalCsvDatasetAdapter(tmp_path).describe().content_hash
        assert len(content_hash) == 64 and int(content_hash, 16) >= 0


class TestRemoteCacheAndLimits:
    def test_cache_by_name_does_not_reuse_different_content(self, tmp_path):
        cache = tmp_path / "cache"
        first = _schema_zip(tmp_path / "one.zip", "a,b\n1,2\n")
        RemoteHttpDatasetAdapter(first.as_uri(), name="ds", cache_dir=cache).fetch()
        second = _schema_zip(tmp_path / "two.zip", "a,b\n9,9\n")
        dataset_dir = RemoteHttpDatasetAdapter(second.as_uri(), name="ds", cache_dir=cache).fetch()
        assert (dataset_dir / "Building_1.csv").read_text(encoding="utf-8") == "a,b\n9,9\n"

    def test_expected_digest_mismatch_rejected(self, tmp_path):
        source = _schema_zip(tmp_path / "ds.zip")
        adapter = RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=tmp_path / "cache",
                                           expected_sha256="0" * 64)
        with pytest.raises(DatasetValidationError, match="sha256"):
            adapter.fetch()

    def test_expected_digest_allows_offline_reuse(self, tmp_path):
        source = _schema_zip(tmp_path / "ds.zip")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        cache = tmp_path / "cache"
        first = RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=cache, expected_sha256=digest).fetch()
        source.unlink()
        again = RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=cache, expected_sha256=digest).fetch()
        assert first == again

    @pytest.mark.parametrize("member", ["../evil.txt", "/abs.txt", "C:/evil.txt", "ds/../../evil.txt"])
    def test_member_escaping_extraction_root_rejected(self, tmp_path, member):
        source = _zip(tmp_path / "ds.zip", {"ds/schema.json": "{}", member: "x"})
        cache = tmp_path / "cache"
        with pytest.raises(DatasetValidationError):
            RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=cache).fetch()
        assert not (tmp_path / "evil.txt").exists() and not (cache / "evil.txt").exists()

    def test_symlink_member_rejected(self, tmp_path):
        source = tmp_path / "ds.zip"
        with zipfile.ZipFile(source, "w") as zf:
            zf.writestr("ds/schema.json", "{}")
            info = zipfile.ZipInfo("ds/link")
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, "/etc/passwd")
        with pytest.raises(DatasetValidationError, match="link"):
            RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=tmp_path / "cache").fetch()

    def test_truncated_archive_rejected(self, tmp_path):
        source = _schema_zip(tmp_path / "ds.zip", "a,b\n" + "1,2\n" * 5000)
        payload = source.read_bytes()
        source.write_bytes(payload[: len(payload) // 2])
        with pytest.raises(DatasetValidationError):
            RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=tmp_path / "cache").fetch()

    def test_download_larger_than_quota_rejected(self, tmp_path):
        source = _schema_zip(tmp_path / "ds.zip", "a,b\n" + "1,2\n" * 5000)
        adapter = RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=tmp_path / "cache",
                                           max_download_bytes=100)
        with pytest.raises(DatasetValidationError, match="download"):
            adapter.fetch()

    def test_expansion_larger_than_quota_rejected(self, tmp_path):
        source = _zip(tmp_path / "ds.zip", {"ds/schema.json": "{}", "ds/big.csv": "0" * 2_000_000})
        assert source.stat().st_size < 50_000  # highly compressible
        adapter = RemoteHttpDatasetAdapter(source.as_uri(), name="ds", cache_dir=tmp_path / "cache",
                                           max_extracted_bytes=1_000_000)
        with pytest.raises(DatasetValidationError, match="expan"):
            adapter.fetch()
        assert not any((tmp_path / "cache").rglob("big.csv"))

    def test_download_uses_an_explicit_timeout(self, tmp_path, monkeypatch):
        import urllib.request
        seen = {}

        def fake_urlopen(url, timeout=None):
            seen["timeout"] = timeout
            raise TimeoutError("slow")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        adapter = RemoteHttpDatasetAdapter("https://example.invalid/ds.zip", name="ds",
                                           cache_dir=tmp_path / "cache", timeout_seconds=7)
        with pytest.raises(DatasetValidationError):
            adapter.fetch()
        assert seen["timeout"] == 7

    @pytest.mark.parametrize("name", ["../escape", "a/b", "C:x", ""])
    def test_cache_name_cannot_escape(self, tmp_path, name):
        with pytest.raises(DatasetValidationError):
            RemoteHttpDatasetAdapter("https://x/ds.zip", name=name or "..", cache_dir=tmp_path / "cache")
