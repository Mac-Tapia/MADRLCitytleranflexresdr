"""Preregister structural KPI applicability from the frozen exogenous files."""
from __future__ import annotations

import csv
import io
import hashlib
import json
import math
from pathlib import Path

from uc3m.application.dataset.provenance import contained_path
from uc3m.domain.campaigns import canonical_hash

PRICE_ENDPOINT = ('E3', 'price_signal_deviation')


def classify_endpoint_applicability(dataset_root: Path, project_root: Path, *, tariff_policy=None):
    dataset_root, project_root = Path(dataset_root), Path(project_root)
    splits = json.loads((dataset_root/'split_manifest.json').read_text(encoding='utf-8'))['splits']
    records = []
    for split in splits:
        schema_path = contained_path(dataset_root, 'splits/' + split['schema_path'])
        schema = json.loads(schema_path.read_text(encoding='utf-8'))
        prices = {b['pricing'] for b in schema['buildings'].values() if b.get('include', True)}
        for relative in sorted(prices):
            path = contained_path(schema_path.parent, relative)
            payload = path.read_bytes().replace(b'\r\n', b'\n')
            values = [float(r['electricity_pricing']) for r in
                      csv.DictReader(io.StringIO(payload.decode('utf-8-sig'), newline=''))]
            if len(values) != split['rows'] or not values or not all(math.isfinite(v) for v in values):
                raise ValueError('price applicability requires complete finite split prices')
            records.append({'path': path.relative_to(project_root).as_posix(), 'split': split['split_id'],
                            'sha256': hashlib.sha256(payload).hexdigest(), 'rows': len(values),
                            'minimum': min(values), 'maximum': max(values)})
    if {r['split'] for r in records} != {'train_2023', 'validation_2024', 'test_2025'}:
        raise ValueError('price applicability requires all three frozen splits')
    effective = (None if tariff_policy is None else {'policy_id': tariff_policy.policy_id,
        'mode': tariff_policy.mode, 'multiplier': tariff_policy.multiplier,
        'fingerprint': tariff_policy.fingerprint()})
    mode = effective['mode'] if effective else None
    flat = mode == 'flat' or (mode in (None, 'rtp') and all(r['maximum']-r['minimum'] <= 1e-12 for r in records))
    return {'schema_version': 1, 'rule': 'price response is undefined without variation after the frozen tariff transformation',
            'not_applicable_endpoints': [list(PRICE_ENDPOINT)] if flat else [], 'price_files': records,
            'effective_tariff': effective}


def not_applicable_endpoints(manifest):
    declaration = manifest.get('endpoint_applicability')
    if declaration is None:
        return ()  # Old contracts retain every endpoint; absent data never unlocks acceptance.
    if canonical_hash(declaration) != manifest['identity'].get('endpoint_applicability_sha256'):
        raise ValueError('endpoint applicability was not frozen in the campaign identity')
    endpoints = tuple(tuple(e) for e in declaration.get('not_applicable_endpoints', []))
    if endpoints not in ((), (PRICE_ENDPOINT,)):
        raise ValueError('only structurally undefined price response can be non-applicable')
    prices = declaration.get('price_files') or []
    if ({r['split'] for r in prices} != {'train_2023', 'validation_2024', 'test_2025'}
            or any(type(r['rows']) is not int or r['rows'] <= 0
                   or not all(not isinstance(r[k], bool) and isinstance(r[k], (int, float))
                              and math.isfinite(r[k]) for k in ('minimum', 'maximum'))
                   for r in prices)):
        raise ValueError('incomplete price applicability evidence')
    from uc3m.domain.scenarios import TariffPolicy
    effective = declaration.get('effective_tariff')
    mode = None
    if effective is not None:
        policy = TariffPolicy(effective['policy_id'], effective['mode'], effective['multiplier'])
        if policy.fingerprint() != effective.get('fingerprint'):
            raise ValueError('effective tariff fingerprint changed')
        mode = policy.mode
    flat = mode == 'flat' or (mode in (None, 'rtp') and all(0 <= r['maximum']-r['minimum'] <= 1e-12 for r in prices))
    if bool(endpoints) != flat:
        raise ValueError('price applicability contradicts the recorded price spans')
    return endpoints
