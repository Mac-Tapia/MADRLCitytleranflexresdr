"""Additional I13 contracts: immutable evidence, safe listings and valid paths."""
import json

import pandas as pd
import pytest

from uc3m.application.dataset.construction import DatasetBuildConfig, build_dataset, hash_directory
from uc3m.application.dataset.provenance import RawSourceManifest, contained_path
from uc3m.data.adapters.s3 import S3DatasetAdapter
from uc3m.data.contracts import DatasetValidationError
from uc3m.geography.ingest import UniversalDataIngester
from test_i13_data_security import S3Client, case_write_sandbox, fail_providers, junction


def provider_frame(year=2023):
    index = pd.date_range(f'{year}-01-01', periods=8760, freq='h', tz='UTC')
    frame = pd.DataFrame({
        'outdoor_dry_bulb_temperature': -10.0,
        'outdoor_relative_humidity': 50.0,
        'diffuse_solar_irradiance': 1.0,
        'direct_solar_irradiance': 2.0,
    }, index=index)
    return frame


@pytest.mark.parametrize('relative', ['raw/file.csv:stream', 'outputs./a.csv', 'raw/NUL.csv', 'raw/file.csv '])
def test_contained_path_rejects_windows_aliases(tmp_path, relative):
    with pytest.raises(ValueError, match='Windows'):
        contained_path(tmp_path, relative)
    assert list(tmp_path.iterdir()) == []


def test_s3_rejects_file_directory_collisions_before_download(tmp_path, monkeypatch):
    client = S3Client(['data/sub', 'data/sub/schema.json'], tmp_path)
    with case_write_sandbox(tmp_path):
        adapter = S3DatasetAdapter('bucket', 'data/', cache_dir=tmp_path)
        monkeypatch.setattr(adapter, '_make_client', lambda: client)
        with pytest.raises(DatasetValidationError, match='collid'):
            adapter.fetch()
    assert client.downloads == []
    assert list(tmp_path.iterdir()) == []


def test_s3_preserves_direct_schema_preference(tmp_path):
    dataset = tmp_path/'dataset'
    (dataset/'a').mkdir(parents=True)
    (dataset/'schema.json').write_text('{}')
    (dataset/'a'/'schema.json').write_text('{}')
    with case_write_sandbox(tmp_path):
        adapter = S3DatasetAdapter('bucket', name='dataset', cache_dir=tmp_path)
        assert adapter.fetch() == dataset


def test_s3_validates_all_pages_before_mkdir(tmp_path, monkeypatch):
    class Pages(S3Client):
        def paginate(self, **kwargs):
            yield {'Contents': [{'Key': 'data/schema.json'}]}
            yield {'Contents': [{'Key': 'data/../escape.txt'}]}
    client = Pages([], tmp_path)
    with case_write_sandbox(tmp_path):
        adapter = S3DatasetAdapter('bucket', 'data/', cache_dir=tmp_path)
        monkeypatch.setattr(adapter, '_make_client', lambda: client)
        with pytest.raises(ValueError, match='parent traversal'):
            adapter.fetch()
    assert client.downloads == []
    assert list(tmp_path.iterdir()) == []


def test_s3_rejects_nested_junction_even_with_direct_schema(tmp_path):
    dataset = tmp_path/'dataset'
    dataset.mkdir()
    (dataset/'schema.json').write_text('{}')
    outside = tmp_path/'outside'
    outside.mkdir()
    junction(dataset/'linked', outside)
    with case_write_sandbox(tmp_path):
        with pytest.raises(ValueError, match='link|junction'):
            S3DatasetAdapter('bucket', name='dataset', cache_dir=tmp_path).fetch()
    assert list(outside.iterdir()) == []


def test_build_valid_output_is_frozen_and_hashes_stable(tmp_path):
    config = DatasetBuildConfig('test', (2023,), (1,), 7, 'PEN', 'UTC')
    output = tmp_path/'data'/'campaigns'/'test'/'dataset'
    def generator(request):
        (request.output_dir/'weather.csv').write_bytes(b'temperature\r\n-10\r\n')
    manifest = build_dataset(RawSourceManifest((), 'sourcehash'), config, output,
                             project_root=tmp_path, generator=generator, targets=())
    assert manifest.files
    assert manifest.dataset_hash == hash_directory(output)[1]
    before = (output/'weather.csv').read_bytes()
    with pytest.raises(FileExistsError):
        build_dataset(RawSourceManifest((), 'sourcehash'), config, output,
                      project_root=tmp_path, generator=generator, targets=())
    assert (output/'weather.csv').read_bytes() == before


def test_weather_reanalysis_roundtrip_has_hash_and_never_measurement(tmp_path, monkeypatch):
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    monkeypatch.setattr(ingester, '_from_pvgis', lambda year: provider_frame(year))
    df = ingester.get_weather([2023])
    record = df.attrs['weather_provenance'][0]
    assert record['source'] == 'PVGIS_ERA5'
    assert record['source_type'] == 'weather_reanalysis'
    assert record['measured'] is False
    assert len(record['sha256']) == 64
    assert df.iloc[0]['outdoor_dry_bulb_temperature'] == -10
    fail_providers(ingester, monkeypatch)
    pd.testing.assert_frame_equal(df, ingester.get_weather([2023]))


def test_weather_tampered_cache_rejected_without_overwrite(tmp_path, monkeypatch):
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    monkeypatch.setattr(ingester, '_from_pvgis', lambda year: provider_frame(year))
    ingester.get_weather([2023])
    cache = tmp_path/'2023_0.0000_0.0000.parquet'
    with cache.open('ab') as stream:
        stream.write(b'!')
    tampered = cache.read_bytes()
    fail_providers(ingester, monkeypatch)
    with pytest.raises(RuntimeError, match='hash mismatch'):
        ingester.get_weather([2023])
    assert cache.read_bytes() == tampered


def test_weather_cache_identity_timezone_and_source_checked(tmp_path, monkeypatch):
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    monkeypatch.setattr(ingester, '_from_pvgis', lambda year: provider_frame(year))
    ingester.get_weather([2023])
    different = UniversalDataIngester(0, 0, tz='America/Lima', cache_dir=tmp_path)
    fail_providers(different, monkeypatch)
    with pytest.raises(RuntimeError, match='identity'):
        different.get_weather([2023])
    sidecar = next(tmp_path.glob('*.provenance.json'))
    proof = json.loads(sidecar.read_text())
    proof['source'] = 'synthetic'
    sidecar.write_text(json.dumps(proof))
    with pytest.raises(RuntimeError, match='unapproved weather source'):
        ingester.get_weather([2023])


def test_weather_skip_cache_cannot_reseal_legacy_data(tmp_path, monkeypatch):
    cache = tmp_path/'2023_0.0000_0.0000.parquet'
    pd.DataFrame({'unknown_origin': [1]}).to_parquet(cache)
    before = cache.read_bytes()
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path, skip_cache=True)
    monkeypatch.setattr(ingester, '_from_pvgis', lambda year: provider_frame(year))
    with pytest.raises(RuntimeError, match='immutable'):
        ingester.get_weather([2023])
    assert cache.read_bytes() == before
    assert not list(tmp_path.glob('*.provenance.json'))


def test_weather_missing_values_never_imputed_or_persisted(tmp_path, monkeypatch):
    incomplete = provider_frame()
    incomplete.iloc[1, 0] = float('nan')
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path)
    monkeypatch.setattr(ingester, '_from_pvgis', lambda year: incomplete)
    monkeypatch.setattr(ingester, '_from_nasa_power', lambda year: incomplete)
    with pytest.raises(RuntimeError, match='No proven weather'):
        ingester.get_weather([2023])
    assert list(tmp_path.iterdir()) == []


def test_weather_synthetic_cache_reuses_seed_and_stays_ineligible(tmp_path, monkeypatch):
    ingester = UniversalDataIngester(0, 0, cache_dir=tmp_path, allow_synthetic=True, synthetic_seed=7)
    fail_providers(ingester, monkeypatch)
    first = ingester.get_weather([2023])
    second = ingester.get_weather([2023])
    pd.testing.assert_frame_equal(first, second)
    assert second.attrs['scientific_eligible'] is False
    assert second.attrs['weather_provenance'][0]['seed'] == 7
