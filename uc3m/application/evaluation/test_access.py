"""Campaign-scoped test access after the selected configurations are frozen.

An arbitrary JSON file beside the dataset cannot unlock a held-out split.
This record binds the campaign, frozen selection and predeclared protocol;
it is permission to evaluate, never scientific or operational acceptance.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.attempt_evidence import _read
from uc3m.application.training.attempt_trust import load_trust_contract
from uc3m.application.training.persistence import write_json_atomic
from uc3m.domain.campaigns import canonical_hash

FILE = 'test_unlock.json'


def _contract(manifest_path):
    from uc3m.application.training.fresh_campaign import load_configuration_freezes
    from uc3m.application.evaluation.fresh_analysis import FrozenProtocol
    manifest_path = Path(manifest_path)
    manifest = _read(manifest_path) or {}
    trust = load_trust_contract(manifest_path.parent, manifest.get('campaign_id'))
    if trust.reasons:
        raise PermissionError('test access requires a valid campaign plan')
    freezes = load_configuration_freezes(manifest_path.parent, manifest)
    if set(freezes) != set(manifest['optimizer_owners']):
        raise PermissionError('every algorithm needs its frozen configuration')
    from uc3m.application.pipeline import _validation_rows
    from uc3m.application.training.fresh_tuning import TuningProtocol, select_hyperparameters
    expected, treatments, hyper = {}, {}, {}
    for row in trust.rows.values():
        if row['stage'] != 'hpo':
            continue
        a, c, s, seed = row['algorithm'], row['candidate'], row['scenario'], row['seed']
        expected.setdefault(a, set()).add((c, s, seed))
        treatments[(a, c, s, seed)] = row
        hyper[(a, c)] = row['effective_hyperparameters']
    tuning = TuningProtocol(manifest['campaign_id'], expected, treatments, hyper,
                            (manifest.get('collapsed_candidates') or {}).get('hpo', {}))
    rows = _validation_rows(manifest_path, manifest['campaign_id'])
    for algorithm, freeze in freezes.items():
        selected = select_hyperparameters(rows.get(algorithm, []), tuning).as_dict()
        actual = freeze.as_dict()
        selected.pop('frozen_at')
        actual.pop('frozen_at')
        if selected != actual:
            raise PermissionError('frozen choice no longer matches verified validation evidence')
    from uc3m.application.evaluation.endpoint_applicability import not_applicable_endpoints
    protocol = dataclasses.replace(FrozenProtocol.default(), split='test_2025',
                                   not_applicable_endpoints=not_applicable_endpoints(manifest))
    return {'campaign_id': manifest['campaign_id'], 'spec_hash': manifest['spec_hash'],
            'dataset_hash': manifest['identity']['dataset_hash'],
            'configuration_freezes': manifest['configuration_freezes'],
            'freeze_hashes': {a: f.freeze_hash() for a, f in freezes.items()},
            'protocol_sha256': canonical_hash(dataclasses.asdict(protocol))}


def write_test_unlock(manifest_path):
    record = _contract(manifest_path)
    path = contained_path(Path(manifest_path).parent, FILE)
    if path.exists():
        if _read(path) != record:
            raise PermissionError('a conflicting test access record already exists')
    else:
        write_json_atomic(path, record)
    return path


def verify_test_unlock(manifest_path):
    path = contained_path(Path(manifest_path).parent, FILE)
    if not path.is_file() or _read(path) != _contract(manifest_path):
        raise PermissionError('test split locked: missing or changed campaign freeze/protocol')
    return True
