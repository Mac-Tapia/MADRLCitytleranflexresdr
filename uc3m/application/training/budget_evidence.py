"""Attempt-local, pre-learning custody of the buffer actually selected.

Stage results may not exist after a cut. Later resource measurements may also
change worker counts or add a buffer for a phase that had not started. Neither
invalidates the immutable budget evidence of an already completed attempt.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.attempt_evidence import _inside, _read, _sha256
from uc3m.application.training.persistence import write_json_atomic
from uc3m.domain.campaigns import canonical_hash

FILE = 'phase_budget.json'
IDENTITY_FIELDS = ('attempt_id', 'treatment_id', 'seed')


def persist_buffer_proof(attempt_root: Path, row: dict, manifest: dict, budget_path: Path):
    """Called after attempt identity is created, before the learner is invoked."""
    record = _read(contained_path(attempt_root, 'attempt.json')) or {}
    raw = Path(budget_path).read_bytes()
    source = json.loads(raw.decode('utf-8'))
    buffer = row['phase_buffer']
    if source.get('stage') != row['stage'] or (source.get('buffers') or {}).get(row['algorithm']) != buffer:
        raise PermissionError('budget changed before learning')
    proof = {'schema_version': 1, 'campaign_id': manifest['campaign_id'], 'spec_hash': manifest['spec_hash'],
             'stage': row['stage'], 'algorithm': row['algorithm'],
             'identity': {k: record[k] for k in IDENTITY_FIELDS}, 'buffer': buffer,
             'buffer_sha256': canonical_hash(buffer), 'source_budget_json': raw.decode('utf-8'),
             'source_budget_sha256': hashlib.sha256(raw).hexdigest()}
    target = contained_path(attempt_root, FILE)
    if target.exists():
        raise FileExistsError('a fresh attempt already has budget evidence')
    write_json_atomic(target, proof)
    row['phase_budget_proof_sha256'] = _sha256(target)


def read_buffer_proof(attempt_root: Path, resolved: dict, record: dict, manifest: dict):
    path = contained_path(attempt_root, FILE)
    if not _inside(path, attempt_root) or _sha256(path) != resolved.get('phase_budget_proof_sha256'):
        raise ValueError('missing or changed attempt budget proof')
    proof = _read(path) or {}
    buffer = proof.get('buffer')
    if (not isinstance(buffer, dict) or proof.get('campaign_id') != manifest['campaign_id']
            or proof.get('spec_hash') != manifest['spec_hash'] or proof.get('stage') != resolved['stage']
            or proof.get('algorithm') != resolved['algorithm']
            or proof.get('identity') != {k: record[k] for k in IDENTITY_FIELDS}
            or buffer != resolved.get('phase_buffer') or canonical_hash(buffer) != proof.get('buffer_sha256')
            or canonical_hash(buffer) != resolved.get('phase_buffer_sha256')):
        raise ValueError('foreign attempt budget proof')
    raw = proof['source_budget_json'].encode('utf-8')
    source = json.loads(raw.decode('utf-8'))
    if (hashlib.sha256(raw).hexdigest() != proof.get('source_budget_sha256')
            or source.get('stage') != resolved['stage']
            or (source.get('buffers') or {}).get(resolved['algorithm']) != buffer):
        raise ValueError('budget source snapshot differs from selected buffer')
    return buffer
