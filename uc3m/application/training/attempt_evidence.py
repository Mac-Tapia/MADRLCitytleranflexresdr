"""Strict attempt evidence, shared by creation and every persisted readback."""
from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path
from typing import List, Mapping, Sequence

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.fresh_policy import read_attempt
from uc3m.domain.evidence import checkpoint_bundle_hash as _bundle_hash


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path: Path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def _is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def _inside(path: Path, base: Path) -> bool:
    """True for a real (non-link) file whose resolved location stays under base."""
    if _is_link(base):
        return False
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(base.resolve(strict=True))
    except (OSError, ValueError):
        return False
    current = path
    while current != base and current != current.parent:
        if _is_link(current):
            return False
        current = current.parent
    return resolved.is_file()


def _count(value) -> bool:
    """A recorded count: an int that is not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _checkpoint_reasons(evidence: Mapping[str, object], attempt_root: Path) -> List[str]:
    """Listed checkpoints exist inside the attempt, not through links, and match the bundle hash."""
    listed = evidence.get('checkpoint_files') or []
    if not isinstance(listed, list) or not listed or any(not isinstance(name, str) for name in listed):
        return ['no_checkpoint']
    files = []
    for name in listed:
        try:
            path = contained_path(attempt_root, str(name))
        except ValueError:
            return ['checkpoint_outside_attempt']
        if not path.is_file():
            return ['checkpoint_missing']
        files.append(path)
    return [] if _bundle_hash(files) == evidence.get('checkpoint_bundle_hash') else ['checkpoint_hash_mismatch']


def attempt_evidence_reasons(evidence: Mapping[str, object], attempt_root: Path, *, campaign_id: str, attempt_id: str,
                             treatment_id: str, seed: int, expected_owners: Sequence[str],
                             min_success_ratio: float = 0.99) -> List[str]:
    """Reasons the learning evidence of one attempt cannot be trusted; empty when it can.

    Owners come from the backend declaration, never from the owners that happen to
    appear. ``min_success_ratio`` (successful/attempted optimizer steps per owner)
    is a project criterion: the native guard drops non-finite steps on purpose, so
    isolated non-finite events are allowed.
    """
    expected = tuple(expected_owners)
    if not expected:
        raise ValueError('expected optimizer owners must be declared for the backend')
    attempt_root = Path(attempt_root)
    reasons = []
    if evidence.get('campaign_id') != campaign_id:
        reasons.append('foreign_campaign')
    try:
        record = read_attempt(attempt_root)
    except (OSError, ValueError, KeyError, TypeError):
        record = None
        reasons.append('attempt_record_missing')
    if evidence.get('attempt_id') != attempt_id or (record is not None and record.get('attempt_id') != attempt_id):
        reasons.append('foreign_attempt')
    if record is not None:
        if record.get('treatment_id') != treatment_id:
            reasons.append('foreign_treatment')
        if record.get('seed') != seed:
            reasons.append('foreign_seed')
    fields = ('successful_optimizer_updates_by_owner', 'attempted_optimizer_steps_by_owner',
              'initial_parameter_hashes', 'final_parameter_hashes')
    if any(not isinstance(evidence.get(key), Mapping) for key in fields):
        return reasons + ['invalid_optimizer_evidence']
    successful, attempted, initial, final = (dict(evidence[key]) for key in fields)
    for owner in sorted(set(successful) - set(expected)):
        reasons.append(f'unexpected_owner:{owner}')
    for owner in expected:
        if owner not in successful:
            reasons.append(f'missing_owner:{owner}')
            continue
        count, tried = successful[owner], attempted.get(owner)
        if not _count(count) or count < 0:
            reasons.append(f'invalid_update_count:{owner}')
            continue
        if count == 0:
            reasons.append(f'no_successful_update:{owner}')
        elif not _count(tried) or tried < count or count/tried < float(min_success_ratio):
            reasons.append(f'low_success_ratio:{owner}')
        if (any(not isinstance(values.get(owner), str) or len(values[owner]) != 64
                or any(c not in '0123456789abcdef' for c in values[owner]) for values in (initial, final))
                or initial.get(owner) == final.get(owner)):
            reasons.append(f'parameters_unchanged:{owner}')
    nonfinite = evidence.get('nonfinite_events')
    if not _count(nonfinite) or nonfinite < 0:
        reasons.append('invalid_nonfinite_events')
    steps = evidence.get('env_steps')
    if not _count(steps) or steps <= 0:
        reasons.append('invalid_env_steps')
    episodes = evidence.get('completed_episodes')
    if not _count(episodes) or episodes <= 0:
        reasons.append('invalid_completed_episodes')
    return reasons + _checkpoint_reasons(evidence, attempt_root)


