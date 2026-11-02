"""Physical train/validation/test splits and a normalizer fitted on train only.

Each split is a self-contained CityLearn dataset (schema plus sliced CSVs) whose
simulation window is that year only, so nothing estimated from it can see
another year. Perfect-forecast columns stay in the files for schema
compatibility but are deactivated as observations. Observation bounds are
fitted once on the training split and reused frozen for validation and test.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

from uc3m.application.dataset.construction import hash_directory

TOTAL_ROWS = 26304
LIMA = timezone(timedelta(hours=-5))  # America/Lima has no daylight saving time
SPLITS: Tuple[Tuple[str, int, int, int], ...] = (
    ('train_2023', 2023, 0, 8760),
    ('validation_2024', 2024, 8760, 8784),
    ('test_2025', 2025, 17544, 8760),
)
FUTURE_MARKER = '_predicted_'

Bounds = Mapping[str, Mapping[str, Tuple[float, float]]]


@dataclass(frozen=True)
class SplitRecord:
    split_id: str
    directory: str
    schema_path: str
    start: str
    end: str
    rows: int
    sha256: str

    def as_dict(self):
        return dict(self.__dict__)


@dataclass(frozen=True)
class SplitManifest:
    campaign_id: str
    source_dataset_sha256: str
    splits: Tuple[SplitRecord, ...]
    fit_dependencies: Mapping[str, str]
    root: Path = field(compare=False, repr=False, default=Path('.'))

    def split(self, split_id: str) -> SplitRecord:
        return next(s for s in self.splits if s.split_id == split_id)

    def path(self, split_id: str) -> Path:
        return self.root/self.split(split_id).directory

    def as_dict(self):
        return {'schema_version': 1, 'campaign_id': self.campaign_id,
                'source_dataset_sha256': self.source_dataset_sha256,
                'splits': [s.as_dict() for s in self.splits], 'fit_dependencies': dict(self.fit_dependencies)}


@dataclass(frozen=True)
class NormalizerSpec:
    fit_scope: str
    train_split_sha256: str
    bounds: Bounds
    periodic_bounds: Bounds
    out_of_range_policy: str
    train_fit_hash: str

    def as_dict(self):
        def plain(b):
            return {k: {n: list(v) for n, v in row.items()} for k, row in b.items()}
        return {'schema_version': 1, 'fit_scope': self.fit_scope, 'train_split_sha256': self.train_split_sha256,
                'bounds': plain(self.bounds), 'periodic_bounds': plain(self.periodic_bounds),
                'out_of_range_policy': self.out_of_range_policy, 'train_fit_hash': self.train_fit_hash}

    @classmethod
    def from_dict(cls, payload):
        def tuples(b):
            return {k: {n: (float(v[0]), float(v[1])) for n, v in row.items()} for k, row in b.items()}
        return cls(payload['fit_scope'], payload['train_split_sha256'], tuples(payload['bounds']),
                   tuples(payload.get('periodic_bounds', {})), payload['out_of_range_policy'],
                   payload['train_fit_hash'])


def _csv_references(payload) -> List[str]:
    found = []

    def visit(value):
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str) and value.lower().endswith('.csv'):
            found.append(value)
    visit(payload)
    return sorted(set(found))


def _deactivate_future(observations: Mapping[str, Mapping[str, object]]):
    return {name: ({**cfg, 'active': False} if FUTURE_MARKER in name else dict(cfg))
            for name, cfg in observations.items()}


def effective_observation_names(schema: Mapping[str, object]) -> List[str]:
    return [name for name, cfg in schema.get('observations', {}).items() if cfg.get('active')]


def assert_no_future_fields(names: Sequence[str]) -> None:
    future = [name for name in names if FUTURE_MARKER in name]
    if future:
        raise ValueError(f'perfect-forecast fields are not admitted as actor inputs: {future}')


def _iso(year: int, hours: int) -> str:
    return (datetime(year, 1, 1, tzinfo=LIMA) + timedelta(hours=hours)).isoformat()


def _fix_devices(building: Dict[str, object], sizes: Mapping[str, Mapping[str, float]]):
    """The physical system is the same in every split: no per-window autosize."""
    for device, attributes in sizes.items():
        config = dict(building.get(device) or {})
        config['autosize'] = False
        config['attributes'] = {**dict(config.get('attributes') or {}), **dict(attributes)}
        config.pop('autosize_attributes', None)
        building[device] = config


def materialize_splits(dataset_dir: Path, output_dir: Path, *, campaign_id: str,
                       fixed_devices: Mapping[str, Mapping[str, Mapping[str, float]]] = None) -> SplitManifest:
    dataset_dir, output_dir = Path(dataset_dir), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f'{output_dir} already exists; frozen splits are never overwritten')
    schema = json.loads((dataset_dir/'schema.json').read_text(encoding='utf-8'))
    references = _csv_references(schema)
    for split_id, _, _, _ in SPLITS:
        (output_dir/split_id).mkdir(parents=True)
    for name in references:
        source = dataset_dir/name
        if Path(name).is_absolute() or '..' in Path(name).parts or not source.is_file():
            raise ValueError(f'schema reference {name!r} is not a file inside the dataset')
        with open(source, newline='', encoding='utf-8') as stream:
            reader = csv.reader(stream)
            header = next(reader)
            rows = list(reader)
        if len(rows) != TOTAL_ROWS:
            raise ValueError(f'{name}: {len(rows)} rows, expected {TOTAL_ROWS}')
        for split_id, _, start, length in SPLITS:
            target = output_dir/split_id/name
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream, lineterminator='\n')
                writer.writerow(header)
                writer.writerows(rows[start:start + length])
    records = []
    for split_id, year, start, length in SPLITS:
        split_schema = dict(schema, root_directory=None, simulation_start_time_step=0,
                            simulation_end_time_step=length - 1)
        split_schema['observations'] = _deactivate_future(schema.get('observations', {}))
        buildings = {}
        for key, building in schema.get('buildings', {}).items():
            building = dict(building)
            if isinstance(building.get('observations'), dict):
                building['observations'] = _deactivate_future(building['observations'])
            autosized = [name for name, value in building.items() if isinstance(value, dict) and value.get('autosize')]
            sizes = dict((fixed_devices or {}).get(key, {}))
            if set(autosized) - set(sizes):
                raise ValueError(f'{key}: autosized devices {sorted(set(autosized) - set(sizes))} need a frozen size')
            _fix_devices(building, sizes)
            buildings[key] = building
        split_schema['buildings'] = buildings
        (output_dir/split_id/'schema.json').write_text(json.dumps(split_schema, indent=2), encoding='utf-8')
        _, digest = hash_directory(output_dir/split_id)
        records.append(SplitRecord(split_id, split_id, f'{split_id}/schema.json', _iso(year, 0),
                                   _iso(year, length - 1), length, digest))
    _, source_digest = hash_directory(dataset_dir)
    return SplitManifest(campaign_id, source_digest, tuple(records),
                         {'normalizer': 'train_2023 only', 'predicted_fields': 'deactivated'}, root=output_dir)


def fit_normalizer(manifest: SplitManifest, limits: Callable[[Path], Bounds],
                   periodic_limits: Callable[[Path], Bounds] = None) -> NormalizerSpec:
    """Bounds come from the training split alone; held-out splits are never read."""
    train = manifest.split('train_2023')
    bounds = {b: {n: (float(lo), float(hi)) for n, (lo, hi) in row.items()}
              for b, row in limits(manifest.path('train_2023')).items()}
    periodic = {}
    if periodic_limits is not None:
        periodic = {b: {n: (float(lo), float(hi)) for n, (lo, hi) in row.items()}
                    for b, row in periodic_limits(manifest.path('train_2023')).items()}
    body = json.dumps({'train': train.sha256, 'bounds': bounds, 'periodic': periodic}, sort_keys=True)
    return NormalizerSpec('train_2023', train.sha256, bounds, periodic, 'clip_and_record',
                          hashlib.sha256(body.encode('utf-8')).hexdigest())


def apply_frozen_normalizer(observations: Mapping[str, Mapping[str, float]], spec: NormalizerSpec):
    scaled: Dict[str, Dict[str, float]] = {}
    flags = []
    for building, values in observations.items():
        row = {}
        for name, value in values.items():
            low, high = spec.bounds[building][name]
            if value < low or value > high:
                flags.append((building, name, value))
            row[name] = 0.0 if high == low else min(1.0, max(0.0, (value - low)/(high - low)))
        scaled[building] = row
    return scaled, flags
