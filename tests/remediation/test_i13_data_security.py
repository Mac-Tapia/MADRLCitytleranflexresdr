"""I13-A regressions: real temporary FS, provider failures injected, no network."""
import json
import os
from pathlib import Path
import subprocess
from contextlib import contextmanager
from contextvars import ContextVar
import sys

import pandas as pd
import pytest

from uc3m.application.dataset.provenance import audit_raw_sources, RawSourceManifest, contained_path
from uc3m.application.dataset.construction import DatasetBuildConfig, build_dataset, hash_directory
from uc3m.data.adapters.s3 import S3DatasetAdapter
from uc3m.data.contracts import DatasetValidationError
from uc3m.geography.ingest import UniversalDataIngester


class SandboxWriteViolation(RuntimeError):
    """A fixture boundary failure must never satisfy expected adapter errors."""


_WRITE_ROOT = ContextVar('i13_data_write_root', default=None)
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


def _require_sandbox_path(path):
    root = _WRITE_ROOT.get()
    if root is None:
        return
    if isinstance(path, int):
        raise SandboxWriteViolation('unverifiable writable file descriptor')
    try:
        candidate = Path(os.fsdecode(path)).resolve()
        candidate.relative_to(root)
    except (TypeError, ValueError, OSError) as exc:
        raise SandboxWriteViolation(f'write outside case sandbox: {path!r}') from exc


def _write_audit(event, args):
    if _WRITE_ROOT.get() is None:
        return
    if event == 'open':
        path, mode, flags = args
        writable = any(c in (mode or '') for c in 'wax+') or bool(flags & _WRITE_FLAGS)
        if writable:
            _require_sandbox_path(path)
    elif event == 'os.mkdir':
        path, mode, dir_fd = args
        if dir_fd not in (None, -1):
            raise SandboxWriteViolation('dir_fd mkdir is not permitted')
        _require_sandbox_path(path)
    elif event in {'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink',
                   'os.truncate', 'os.chmod', 'os.chown', 'os.utime',
                   'os.system', 'subprocess.Popen'}:
        raise SandboxWriteViolation(f'operation not needed by adapter: {event}')


sys.addaudithook(_write_audit)


@contextmanager
def case_write_sandbox(case_root):
    root = Path(case_root).resolve()
    token = _WRITE_ROOT.set(root)
    try:
        yield
    finally:
        _WRITE_ROOT.reset(token)


def junction(link, target):
    """Create a real Windows junction; failure is a test failure, never a skip."""
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], check=True, capture_output=True)
    else:
        link.symlink_to(target, target_is_directory=True)


class S3Client:
    def __init__(self, keys, safety_root):
        self.keys = keys
        self.downloads = []
        self.safety_root = safety_root.resolve()

    def get_paginator(self, name):
        return self

    def paginate(self, **kwargs):
        yield {'Contents': [{'Key': key} for key in self.keys]}

    def download_file(self, bucket, key, dest):
        self.downloads.append(dest)
        # This second barrier also applies when the fake is called independently.
        with case_write_sandbox(self.safety_root):
            _require_sandbox_path(dest)
            Path(dest).write_text('{}', encoding='utf-8')


@pytest.mark.parametrize('name', ['../escape', '/escape', 'C:/escape', r'C:\escape', r'\\host\share', '.', 'a/../b'])
def test_s3_rejects_unsafe_name_without_client(tmp_path, name):
    with case_write_sandbox(tmp_path):
        with pytest.raises((ValueError, DatasetValidationError)):
            S3DatasetAdapter('bucket', name=name, cache_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('key', ['data/../outside.txt', 'other/schema.json', 'data//absolute', 'data/C:/outside', 'data/\\host\\share', 'data/./../outside'])
def test_s3_rejects_invalid_key_before_any_write(tmp_path, monkeypatch, key):
    client = S3Client(['data/schema.json', key], tmp_path)
    with case_write_sandbox(tmp_path):
        adapter = S3DatasetAdapter('bucket', 'data/', name='dataset', cache_dir=tmp_path)
        monkeypatch.setattr(adapter, '_make_client', lambda: client)
        with pytest.raises((ValueError, DatasetValidationError)):
            adapter.fetch()
    assert client.downloads == []
    assert list(tmp_path.iterdir()) == []


def test_s3_valid_dataset_and_cached_schema_without_client(tmp_path, monkeypatch):
    client = S3Client(['data/sub/schema.json'], tmp_path)
    with case_write_sandbox(tmp_path):
        adapter = S3DatasetAdapter('bucket', 'data/', name='dataset', cache_dir=tmp_path)
        monkeypatch.setattr(adapter, '_make_client', lambda: client)
        assert adapter.fetch() == tmp_path/'dataset'/'sub'
        monkeypatch.setattr(adapter, '_make_client', lambda: pytest.fail('cache must not request client'))
        assert adapter.fetch() == tmp_path/'dataset'/'sub'


def test_s3_rejects_cached_schema_under_junction(tmp_path):
    root = tmp_path/'cache'
    target = tmp_path/'outside'
    root.mkdir()
    target.mkdir()
    (target/'schema.json').write_text('{}')
    junction(root/'dataset', target)
    with case_write_sandbox(tmp_path):
        with pytest.raises((ValueError, DatasetValidationError)):
            S3DatasetAdapter('bucket', name='dataset', cache_dir=root).fetch()
    assert (target/'schema.json').read_text() == '{}'


@pytest.mark.parametrize('relative', ['./outputs/a.csv', 'OUTPUTS/a.csv', './data/dataset_audit/a.csv', 'DATA/AUDITS/a.csv', 'CITYLEARN/data/DATASETS/a.csv', './.cache/a.csv'])
def test_audit_rejects_normalized_prior_output_aliases(tmp_path, relative):
    path = tmp_path/relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('test')
    with pytest.raises(ValueError, match='not raw sources'):
        audit_raw_sources([{'path': relative, 'source_type': 'measured_billing'}], root=tmp_path)


def test_audit_keeps_valid_identity(tmp_path):
    (tmp_path/'billing.csv').write_text('real')
    manifest = audit_raw_sources([{'path': 'billing.csv', 'source_type': 'measured_billing'}], root=tmp_path)
    assert manifest.sources[0].path == 'billing.csv'
    assert manifest.sources[0].measured


def test_build_rejects_junction_before_generator_or_write(tmp_path):
    project = tmp_path/'project'
    (project/'data').mkdir(parents=True)
    outside = tmp_path/'outside'
    outside.mkdir()
    junction(project/'data'/'campaigns', outside)
    config = DatasetBuildConfig('test', (2023,), (1,), 1, 'PEN', 'UTC')
    with pytest.raises(ValueError, match='link|junction'):
        build_dataset(RawSourceManifest((), 'hash'), config, project/'data'/'campaigns'/'new',
                      project_root=project, generator=lambda request: pytest.fail('must not generate'), targets=())
    assert list(outside.iterdir()) == []


def test_hash_directory_rejects_linked_directory(tmp_path):
    root = tmp_path/'root'
    root.mkdir()
    outside = tmp_path/'outside'
    outside.mkdir()
    (outside/'secret.csv').write_text('private')
    junction(root/'linked', outside)
    with pytest.raises(ValueError, match='link|junction'):
        hash_directory(root)


def test_contained_path_rejects_linked_root_ancestor(tmp_path):
    outside = tmp_path/'outside'
    (outside/'nested').mkdir(parents=True)
    junction(tmp_path/'link', outside)
    with pytest.raises(ValueError, match='link|junction'):
        contained_path(tmp_path/'link'/'nested', 'file.csv')


def fail_providers(ingester, monkeypatch):
    def unavailable(year):
        raise OSError('injected provider unavailable')
    monkeypatch.setattr(ingester, '_from_pvgis', unavailable)
    monkeypatch.setattr(ingester, '_from_nasa_power', unavailable)


def test_weather_provider_failure_is_closed_by_default(tmp_path, monkeypatch):
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    fail_providers(ingester, monkeypatch)
    with pytest.raises(RuntimeError, match='weather|meteorolog'):
        ingester.get_weather([2023])
    assert list(tmp_path.iterdir()) == []


def test_weather_legacy_cache_preserved_and_untrusted(tmp_path, monkeypatch):
    cache = tmp_path/'2023_0.0000_0.0000.parquet'
    pd.DataFrame({'temperature': [30]}).to_parquet(cache)
    before = cache.read_bytes()
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    fail_providers(ingester, monkeypatch)
    with pytest.raises(RuntimeError, match='provenance|procedencia'):
        ingester.get_weather([2023])
    assert cache.read_bytes() == before


def test_weather_synthetic_requires_seed(tmp_path):
    with pytest.raises(ValueError, match='seed|semilla'):
        UniversalDataIngester(0, 0, cache_dir=tmp_path, allow_synthetic=True)


def test_weather_explicit_synthetic_has_separate_persisted_provenance(tmp_path, monkeypatch):
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path, allow_synthetic=True, synthetic_seed=123)
    fail_providers(ingester, monkeypatch)
    df = ingester.get_weather([2023])
    provenance = df.attrs['weather_provenance']
    assert provenance[0]['source'] == 'synthetic'
    assert provenance[0]['scientific_eligible'] is False
    assert provenance[0]['seed'] == 123
    assert not (tmp_path/'2023_0.0000_0.0000.parquet').exists()
    sidecars = list(tmp_path.rglob('*.provenance.json'))
    assert len(sidecars) == 1
    assert json.loads(sidecars[0].read_text())['scientific_eligible'] is False
    again = UniversalDataIngester(0, 0, cache_dir=tmp_path/'other', allow_synthetic=True, synthetic_seed=123)
    fail_providers(again, monkeypatch)
    pd.testing.assert_frame_equal(df, again.get_weather([2023]))


def test_nasa_negative_temperature_preserved_and_sentinel_missing(tmp_path, monkeypatch):
    import requests
    keys = [f'20230101{h:02d}' for h in range(24)]
    raw = {name: {k: 1.0 for k in keys} for name in ['T2M', 'RH2M', 'ALLSKY_SFC_SW_DWN', 'ALLSKY_SFC_SW_DIFF', 'ALLSKY_SFC_SW_DNI', 'WS10M']}
    raw['T2M'][keys[0]] = -10.0
    raw['T2M'][keys[1]] = -999.0
    raw['ALLSKY_SFC_SW_DIFF'][keys[0]] = -1.0
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'properties': {'parameter': raw}}
    monkeypatch.setattr(requests, 'get', lambda *a, **k: Response())
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    monkeypatch.setattr(ingester, '_is_leap', lambda y: False)
    # NASA normally returns a whole year; repeat fixture to that size.
    for values in raw.values():
        template = list(values.values())
        values.clear()
        values.update({f'{i:08d}': template[i % 24] for i in range(8760)})
    df = ingester._from_nasa_power(2023)
    assert df.iloc[0]['outdoor_dry_bulb_temperature'] == -10.0
    assert pd.isna(df.iloc[1]['outdoor_dry_bulb_temperature'])
    assert df.iloc[0]['diffuse_solar_irradiance'] == 0.0
