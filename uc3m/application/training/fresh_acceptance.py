"""Acceptance of a fresh campaign from its own artifacts (T10).

verify_fresh_acceptance rereads everything it accepts: the campaign identity
and ownership claim, the hashes of every stage manifest, and, for each
completed treatment, the attempt's learning evidence and the hash of its
checkpoint bundle. Software acceptance (clean gate, untampered artifacts) and
scientific acceptance (all stages trained and a scientific report of this
campaign) are separate answers; a prepared campaign without a verified model
is never ready.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.fresh_policy import read_attempt
from uc3m.domain.campaigns import canonical_hash
from uc3m.domain.evidence import checkpoint_bundle_hash as _bundle_hash

FRESH_PREFIX = 'fresh_'


@dataclass(frozen=True)
class AcceptanceReport:
    campaign_id: Optional[str]
    status: str
    software_acceptance: bool
    scientific_acceptance: bool
    checks: Dict[str, bool]
    reasons: Tuple[str, ...]

    def as_dict(self):
        return {'campaign_id': self.campaign_id, 'status': self.status,
                'software_acceptance': self.software_acceptance,
                'scientific_acceptance': self.scientific_acceptance,
                'checks': dict(self.checks), 'reasons': list(self.reasons)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def _is_link(path: Path) -> bool:
    is_junction = getattr(path, 'is_junction', None)
    return path.is_symlink() or bool(is_junction and is_junction())


def _inside(path: Path, base: Path) -> bool:
    """True for a real (non-link) file whose resolved location stays under base."""
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


def _gate_is_clean(gate_report: Optional[Path]) -> bool:
    gate = _read(gate_report) if gate_report else None
    if not isinstance(gate, dict):
        return False
    counters = gate.get('counters') or {}
    return (gate.get('exit_code') == 0 and gate.get('software_acceptance') is True
            and int(counters.get('tests') or 0) > 0
            and not any(int(counters.get(key) or 0) for key in ('failures', 'errors', 'skipped')))


def _count(value) -> bool:
    """A recorded count: an int that is not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _checkpoint_reasons(evidence: Mapping[str, object], attempt_root: Path) -> List[str]:
    """Listed checkpoints exist inside the attempt, not through links, and match the bundle hash."""
    listed = evidence.get('checkpoint_files') or []
    if not listed:
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
    successful = dict(evidence.get('successful_optimizer_updates_by_owner') or {})
    attempted = dict(evidence.get('attempted_optimizer_steps_by_owner') or {})
    initial = dict(evidence.get('initial_parameter_hashes') or {})
    final = dict(evidence.get('final_parameter_hashes') or {})
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
        if initial.get(owner) is None or initial.get(owner) == final.get(owner):
            reasons.append(f'parameters_unchanged:{owner}')
    nonfinite = evidence.get('nonfinite_events')
    if not _count(nonfinite) or nonfinite < 0:
        reasons.append('invalid_nonfinite_events')
    steps = evidence.get('env_steps')
    if not _count(steps) or steps <= 0:
        reasons.append('invalid_env_steps')
    episodes = evidence.get('completed_episodes')
    if not _count(episodes) or episodes < 0:
        reasons.append('invalid_completed_episodes')
    return reasons + _checkpoint_reasons(evidence, attempt_root)


def treatment_trust_reasons(artifacts: Path, campaign_id: str, treatment: dict):
    """Reasons a completed treatment cannot be trusted; empty when its model is verified."""
    name = treatment.get('treatment_id', '?')
    attempt = next((a for a in treatment.get('attempts') or [] if a.get('training_complete')), None)
    if attempt is None:
        return [f'no_complete_attempt:{name}']
    root = artifacts/str(attempt.get('path', ''))
    if not _inside(root/'learning_evidence.json', artifacts):
        return [f'untrusted_attempt_path:{name}']
    evidence = _read(root/'learning_evidence.json') or {}
    completion = _read(root/'completion.json') or {}
    reasons = []
    if evidence.get('campaign_id') != campaign_id:
        reasons.append(f'foreign_evidence:{name}')
    if not (evidence.get('verified') and evidence.get('exit_code') == 0 and not evidence.get('salvage')
            and completion.get('training_complete') is True):
        reasons.append(f'unverified_learning:{name}')
    if _checkpoint_reasons(evidence, root):
        reasons.append(f'untrusted_checkpoint:{name}')
    return reasons


def verify_fresh_acceptance(manifest_path: Path, *, gate_report: Optional[Path] = None) -> AcceptanceReport:
    manifest_path = Path(manifest_path)
    artifacts = manifest_path.parent
    manifest = _read(manifest_path) or {}
    campaign_id = manifest.get('campaign_id')
    reasons, checks = [], {}

    checks['fresh_identity'] = (manifest.get('schema_version') == 1 and isinstance(campaign_id, str)
                                and campaign_id.startswith(FRESH_PREFIX) and isinstance(manifest.get('identity'), dict))
    if not checks['fresh_identity']:
        reasons.append('not_a_fresh_campaign')
    claim = _read(artifacts/'campaign.json') or {}
    checks['campaign_claim'] = (claim.get('campaign_id') == campaign_id
                                and claim.get('spec_hash') == manifest.get('spec_hash'))
    if not checks['campaign_claim']:
        reasons.append('campaign_claim_mismatch')
    checks['spec_hash'] = (checks['fresh_identity']
                           and canonical_hash(manifest['identity']) == manifest.get('spec_hash'))
    if checks['fresh_identity'] and not checks['spec_hash']:
        reasons.append('spec_hash_mismatch')

    stages = manifest.get('stages') or {}
    checks['stage_manifests'] = bool(stages)
    for stage, record in stages.items():
        path = artifacts/str(record.get('path', ''))
        if not _inside(path, artifacts) or _sha256(path) != record.get('sha256'):
            checks['stage_manifests'] = False
            reasons.append(f'stage_manifest_modified:{stage}')

    checks['gate_clean'] = _gate_is_clean(gate_report)
    if not checks['gate_clean']:
        reasons.append('gate_not_clean')

    verified_models, stages_complete = 0, bool(stages)
    model_reasons = []
    for stage in stages:
        result = _read(artifacts/'stages'/f'{stage}_result.json')
        if not isinstance(result, dict) or result.get('status') != 'training_complete':
            stages_complete = False
            continue
        if result.get('campaign_id') != campaign_id:
            model_reasons.append(f'foreign_stage_result:{stage}')
            continue
        for treatment in result.get('treatments') or []:
            found = treatment_trust_reasons(artifacts, campaign_id, treatment)
            model_reasons.extend(found)
            verified_models += 0 if found else 1
    checks['trusted_models'] = not model_reasons
    reasons.extend(model_reasons)

    software = all(checks.values())
    report = _read(artifacts/'reports/scientific_report.json')
    scientific_report = (isinstance(report, dict) and report.get('campaign_id') == campaign_id
                         and report.get('status') == 'scientifically_complete')
    if verified_models == 0:
        status = 'not_ready_no_model'
        reasons.append('no_verified_model')
    elif not stages_complete or not scientific_report:
        status = 'trained_not_evaluated'
        reasons.append('scientific_evaluation_pending')
    else:
        status = 'scientifically_complete'
    if not software:
        status = 'rejected'
    return AcceptanceReport(campaign_id, status, software, software and status == 'scientifically_complete',
                            checks, tuple(reasons))
