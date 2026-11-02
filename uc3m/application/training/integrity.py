"""Identity of the campaign inputs, recomputed before a learner or an evaluator runs.

A hash recorded in a manifest proves nothing until it is recomputed. Preparing a
campaign records config, algorithm config, scenario catalog and its objective
policies, KPI catalog, dataset tree, dataset acceptance, split manifest, every
split tree, normalizer and own sources. A stage or an evaluation starts only
after every one of them is recomputed and equal; a file that changes while it
is verified is refused as well. Text identities normalize CRLF to LF (the same
rule as the dataset tree hash); checkpoint bytes are never hashed here. Every
path is contained by all its ancestors: drives, UNC, parents and junctions are
refused before anything is read.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

import yaml

from uc3m.application.dataset.construction import hash_directory
from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.preflight import source_snapshot

TEXT_SUFFIXES = {'.yaml', '.yml', '.json', '.csv', '.txt', '.toml', '.py'}
FIXED_INPUTS = ('config', 'algorithm_config', 'scenario_catalog', 'objective_policies', 'kpi_catalog', 'dataset',
                'dataset_acceptance', 'split_manifest', 'normalizer', 'source')

__all__ = ['IntegrityResult', 'campaign_inputs', 'contained_path', 'tree_sha256', 'verify_campaign_inputs',
           'verify_split_input']


@dataclass(frozen=True)
class IntegrityResult:
    accepted: bool
    checks: Tuple[str, ...]
    reasons: Tuple[str, ...]
    verified_hashes: Dict[str, str] = field(default_factory=dict)

    def as_dict(self):
        return {'accepted': self.accepted, 'checks': list(self.checks), 'reasons': list(self.reasons),
                'verified_hashes': dict(self.verified_hashes)}


def _file_sha256(path: Path) -> str:
    payload = Path(path).read_bytes()
    if Path(path).suffix.casefold() in TEXT_SUFFIXES:
        payload = payload.replace(b'\r\n', b'\n')
    return hashlib.sha256(payload).hexdigest()


def tree_sha256(path: Path) -> str:
    return hash_directory(path)[1]


def _relative(root: Path, path) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        raise ValueError(f'{path}: campaign input resolves outside the project root') from None


def _measure(root: Path, record: Mapping[str, object]) -> str:
    kind = record.get('kind')
    if kind == 'source':
        return source_snapshot(root, scope='fresh')
    path = contained_path(root, str(record['path']))
    if kind == 'tree':
        if not path.is_dir():
            raise FileNotFoundError(path)
        return tree_sha256(path)
    if kind == 'file':
        if not path.is_file():
            raise FileNotFoundError(path)
        return _file_sha256(path)
    raise ValueError(f'unknown input kind {kind!r}')


def campaign_inputs(config: Mapping[str, object], project_root: Path) -> Dict[str, Dict[str, str]]:
    """Record every input of a campaign with its recomputable hash."""
    root = Path(project_root)
    dataset_root = str(config['dataset_root']).rstrip('/')
    catalog = str(config['scenario_catalog'])
    catalog_payload = yaml.safe_load(contained_path(root, catalog).read_text(encoding='utf-8'))
    policies = (Path(catalog).parent/catalog_payload['objective_policies_file']).as_posix()
    records: Dict[str, Dict[str, str]] = {
        'config': {'kind': 'file', 'path': _relative(root, config['_path'])},
        'algorithm_config': {'kind': 'file', 'path': str(config['algorithm_config'])},
        'scenario_catalog': {'kind': 'file', 'path': catalog},
        'objective_policies': {'kind': 'file', 'path': policies},
        'kpi_catalog': {'kind': 'file', 'path': str(config['kpi_catalog'])},
        'dataset': {'kind': 'tree', 'path': f'{dataset_root}/dataset'},
        'dataset_acceptance': {'kind': 'file', 'path': f'{dataset_root}/dataset_acceptance.json'},
        'split_manifest': {'kind': 'file', 'path': f'{dataset_root}/split_manifest.json'},
        'normalizer': {'kind': 'file', 'path': f'{dataset_root}/normalizer.json'},
        'source': {'kind': 'source', 'path': '.'},
    }
    split_manifest = json.loads(contained_path(root, records['split_manifest']['path']).read_text(encoding='utf-8'))
    directories = {s['split_id']: s['directory'] for s in split_manifest['splits']}
    for split_id in config['splits']:
        records[f'split:{split_id}'] = {'kind': 'tree', 'path': f'{dataset_root}/splits/{directories[split_id]}'}
    for record in records.values():
        record['sha256'] = _measure(root, record)
    return records


def verify_campaign_inputs(manifest_path: Path, project_root: Path) -> IntegrityResult:
    """Recompute every recorded input; any difference, absence or escape refuses the campaign."""
    root = Path(project_root)
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    inputs = manifest.get('inputs')
    if not isinstance(inputs, Mapping) or not inputs:
        return IntegrityResult(False, (), ('inputs_unrecorded',))
    checks: List[str] = []
    reasons: List[str] = [f'{name}_unrecorded' for name in FIXED_INPUTS if name not in inputs]
    if not any(str(name).startswith('split:') for name in inputs):
        reasons.append('splits_unrecorded')
    verified: Dict[str, str] = {}
    for name in sorted(inputs):
        record = inputs[name]
        checks.append(name)
        try:
            digest = _measure(root, record)
        except ValueError as refused:
            reasons.append(f'{name}_path_refused: {refused}')
            continue
        except OSError:
            reasons.append(f'{name}_missing')
            continue
        if digest != record.get('sha256'):
            reasons.append(f'{name}_changed')
        else:
            verified[name] = digest
    # A file rewritten while it was being verified is not the file that was verified.
    for name in sorted(verified):
        if inputs[name].get('kind') != 'file':
            continue
        try:
            again = _file_sha256(contained_path(root, str(inputs[name]['path'])))
        except (OSError, ValueError):
            again = None
        if again != verified[name]:
            reasons.append(f'{name}_changed_during_verification')
            del verified[name]
    return IntegrityResult(not reasons, tuple(checks), tuple(reasons), verified)


def verify_split_input(campaign_root: Path, split_dir: Path) -> str:
    """The evaluated split is the one the split manifest recorded, inside the campaign."""
    campaign_root, split_dir = Path(campaign_root), Path(split_dir)
    try:
        relative = split_dir.absolute().relative_to(campaign_root.absolute()).as_posix()
        contained = contained_path(campaign_root, relative)
    except ValueError as refused:
        raise PermissionError(f'split {split_dir}: {refused}') from None
    manifest = json.loads((campaign_root/'split_manifest.json').read_text(encoding='utf-8'))
    record = next((s for s in manifest['splits'] if f"splits/{s['directory']}" == relative), None)
    if record is None:
        raise PermissionError(f'split {relative} is not recorded in the split manifest')
    if tree_sha256(contained) != record['sha256']:
        raise PermissionError(f"split {record['split_id']} changed after the split manifest was written")
    return record['sha256']
