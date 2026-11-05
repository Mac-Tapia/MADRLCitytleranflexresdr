"""T3: self-contained splits, no future fields and a normalizer frozen on train.

Contract tests build a fresh synthetic 26 304-hour dataset under tmp_path. The
integration test reads only the new campaign dataset; it fails (never skips)
when that dataset is absent.
"""
import csv
import json
from pathlib import Path

import pytest

from uc3m.application.dataset import splits as sp

REPO = Path(__file__).resolve().parents[2]
ROWS = 26304


def _dataset(root: Path, *, heldout_offset=0.0):
    root.mkdir(parents=True)
    with open(root/'weather.csv', 'w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['outdoor_dry_bulb_temperature', 'outdoor_dry_bulb_temperature_predicted_1'])
        for i in range(ROWS):
            value = float(i) + (heldout_offset if i >= 8760 else 0.0)
            writer.writerow([value, value + 1])
    with open(root/'Building_1.csv', 'w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['month', 'hour', 'non_shiftable_load'])
        for i in range(ROWS):
            writer.writerow([1, i % 24 + 1, float(i % 7)])
    schema = {'root_directory': None, 'central_agent': False, 'simulation_start_time_step': 0,
              'simulation_end_time_step': ROWS - 1, 'seconds_per_time_step': 3600,
              'observations': {'hour': {'active': True}, 'outdoor_dry_bulb_temperature': {'active': True},
                               'outdoor_dry_bulb_temperature_predicted_1': {'active': True}},
              'buildings': {'Building_1': {'include': True, 'energy_simulation': 'Building_1.csv',
                                           'weather': 'weather.csv'}}}
    (root/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    return root


def _rows(path):
    with open(path, newline='') as stream:
        return list(csv.reader(stream))


def test_split_lengths_8760_8784_8760(tmp_path):
    manifest = sp.materialize_splits(_dataset(tmp_path/'dataset'), tmp_path/'splits', campaign_id='fresh_test_v1')
    assert [(s.split_id, s.rows) for s in manifest.splits] == [
        ('train_2023', 8760), ('validation_2024', 8784), ('test_2025', 8760)]
    validation = _rows(tmp_path/'splits/validation_2024/weather.csv')
    assert len(validation) == 8784 + 1 and validation[1][0] == '8760.0'  # first 2024 hour
    assert manifest.splits[1].start == '2024-01-01T00:00:00-05:00'
    assert manifest.splits[2].end == '2025-12-31T23:00:00-05:00'


def test_split_schema_self_contained(tmp_path):
    sp.materialize_splits(_dataset(tmp_path/'dataset'), tmp_path/'splits', campaign_id='fresh_test_v1')
    for split in ('train_2023', 'validation_2024', 'test_2025'):
        folder = tmp_path/'splits'/split
        schema = json.loads((folder/'schema.json').read_text(encoding='utf-8'))
        assert schema['simulation_start_time_step'] == 0
        assert schema['simulation_end_time_step'] == len(_rows(folder/'weather.csv')) - 2
        for name in ('Building_1.csv', 'weather.csv'):
            assert (folder/name).is_file() and not Path(name).is_absolute()
    with pytest.raises(FileExistsError):
        sp.materialize_splits(_dataset(tmp_path/'dataset2'), tmp_path/'splits', campaign_id='fresh_test_v1')


def test_no_predicted_fields_in_effective_actor_input(tmp_path):
    sp.materialize_splits(_dataset(tmp_path/'dataset'), tmp_path/'splits', campaign_id='fresh_test_v1')
    schema = json.loads((tmp_path/'splits/train_2023/schema.json').read_text(encoding='utf-8'))
    assert schema['observations']['outdoor_dry_bulb_temperature_predicted_1']['active'] is False
    assert schema['observations']['outdoor_dry_bulb_temperature']['active'] is True
    assert sp.effective_observation_names(schema) == ['hour', 'outdoor_dry_bulb_temperature']
    with pytest.raises(ValueError):
        sp.assert_no_future_fields(['hour', 'electricity_pricing_predicted_2'])


def test_heldout_perturbation_does_not_change_train_scaler(tmp_path):
    def limits(split_dir):  # stands in for CityLearn's estimator on that split only
        values = [float(row[0]) for row in _rows(split_dir/'weather.csv')[1:]]
        return {'Building_1': {'outdoor_dry_bulb_temperature': (min(values), max(values))}}
    a = sp.materialize_splits(_dataset(tmp_path/'a'), tmp_path/'sa', campaign_id='fresh_test_v1')
    b = sp.materialize_splits(_dataset(tmp_path/'b', heldout_offset=1e6), tmp_path/'sb', campaign_id='fresh_test_v1')
    norm_a = sp.fit_normalizer(a, limits)
    norm_b = sp.fit_normalizer(b, limits)
    assert norm_a.bounds == norm_b.bounds == {'Building_1': {'outdoor_dry_bulb_temperature': (0.0, 8759.0)}}
    assert norm_a.train_fit_hash == norm_b.train_fit_hash and norm_a.fit_scope == 'train_2023'
    assert a.splits[1].sha256 != b.splits[1].sha256  # the held-out data really differ


def test_scaler_shared_with_inference(tmp_path):
    from uc3m.adapters.citylearn import fresh_observations as fo
    manifest = sp.materialize_splits(_dataset(tmp_path/'dataset'), tmp_path/'splits', campaign_id='fresh_test_v1')
    spec = sp.fit_normalizer(manifest, lambda d: {'Building_1': {'outdoor_dry_bulb_temperature': (0.0, 10.0)}})

    class FakeBuilding:  # mimics CityLearn's Building limit estimator signature
        name = 'Building_1'

        def estimate_observation_space_limits(self, include_all=None, periodic_normalization=None):
            return ({'outdoor_dry_bulb_temperature': -1e9}, {'outdoor_dry_bulb_temperature': 1e9})
    with fo.frozen_observation_limits(spec, building_class=FakeBuilding):
        low, high = FakeBuilding().estimate_observation_space_limits()
        assert (low['outdoor_dry_bulb_temperature'], high['outdoor_dry_bulb_temperature']) == (0.0, 10.0)
    low, _ = FakeBuilding().estimate_observation_space_limits()
    assert low['outdoor_dry_bulb_temperature'] == -1e9  # restored after the block
    scaled, flags = sp.apply_frozen_normalizer({'Building_1': {'outdoor_dry_bulb_temperature': 12.0}}, spec)
    assert scaled['Building_1']['outdoor_dry_bulb_temperature'] == pytest.approx(1.0)  # clipped
    assert flags == [('Building_1', 'outdoor_dry_bulb_temperature', 12.0)]  # extrapolation recorded


def test_assets_identical_across_splits(tmp_path):
    sizes = {'Building_1': {'cooling_device': {'nominal_power': 139.624}}}
    sp.materialize_splits(_dataset(tmp_path/'dataset'), tmp_path/'splits', campaign_id='fresh_test_v1',
                          fixed_devices=sizes)
    seen = set()
    for split in ('train_2023', 'validation_2024', 'test_2025'):
        schema = json.loads((tmp_path/'splits'/split/'schema.json').read_text(encoding='utf-8'))
        device = schema['buildings']['Building_1']['cooling_device']
        assert device['autosize'] is False  # a per-year autosize would change the asset between splits
        seen.add(device['attributes']['nominal_power'])
    assert seen == {139.624}


@pytest.mark.parametrize('alias', ['iquitos_v2', 'iquitos_v3', 'iquitos_v4'])
def test_real_assets_do_not_depend_on_the_env_seed(alias):
    # CityLearn draws unset device parameters from the env seed; the campaign
    # freezes them so seeds only change the learner, never the physical system.
    from citylearn.citylearn import CityLearnEnv
    schema = REPO/'data/campaigns'/alias/'splits/train_2023/schema.json'
    assert schema.is_file(), 'campaign splits not materialized yet (T3 not complete)'
    draws = []
    for seed in (901, 1001):
        env = CityLearnEnv(str(schema), random_seed=seed)
        env.reset()
        draws.append([(b.cooling_device.nominal_power, b.cooling_device.efficiency,
                       b.cooling_device.target_cooling_temperature) for b in env.buildings])
    assert draws[0] == draws[1]


@pytest.mark.parametrize('alias', ['iquitos_v2', 'iquitos_v3', 'iquitos_v4'])
def test_real_campaign_splits_reset_and_step(alias):
    root = REPO/'data/campaigns'/alias
    manifest_path = root/'split_manifest.json'
    assert manifest_path.is_file(), 'campaign splits not materialized yet (T3 not complete)'
    from uc3m.adapters.citylearn import fresh_observations as fo
    report = fo.smoke_splits(root)
    assert set(report) == {'train_2023', 'validation_2024', 'test_2025'}
    for split, row in report.items():
        assert row['reset_ok'] and row['steps'] >= 24 and row['finite'], (split, row)
        assert not row['predicted_fields_observed'], (split, row)
