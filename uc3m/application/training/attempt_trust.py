"""Re-read attempts against their hash-bound campaign plan, not completion flags."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Dict, Tuple

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.attempt_evidence import (
    _checkpoint_reasons, _count, _inside, _is_link, _read, _sha256, attempt_evidence_reasons,
)
from uc3m.application.training.fresh_policy import read_attempt
from uc3m.domain.campaigns import canonical_hash, treatment_key_from_resolved


@dataclass
class CampaignTrustContract:
    manifest: dict
    rows: Dict[str, dict]
    stages: Dict[str, Tuple[str, ...]]
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class TrustedAttemptContext:
    manifest_path: Path
    manifest: dict
    resolved: dict
    record: dict
    evidence: dict


def read_trusted_attempt(attempt_root: Path, *, algorithm=None) -> TrustedAttemptContext:
    """Bind a native load to its nearest campaign and the complete persisted key.

    The readable plan ID and the fingerprint are deliberately different IDs.
    Neither a completion flag nor an algorithm label substitutes for this readback.
    """
    root = Path(os.path.abspath(attempt_root))
    for ancestor in (root, *root.parents):
        if _is_link(ancestor):
            raise PermissionError('attempt reached through a link or junction')
    manifest_path = next((p/'campaign_manifest.json' for p in root.parents
                          if (p/'campaign_manifest.json').exists()), None)
    if manifest_path is None or not _inside(manifest_path, manifest_path.parent):
        raise PermissionError('attempt has no contained campaign manifest')
    artifacts = manifest_path.parent
    files = ('attempt.json', 'resolved_treatment.json', 'learning_evidence.json', 'completion.json')
    if any(not _inside(root/name, artifacts) for name in files):
        raise PermissionError('attempt metadata missing or outside campaign')
    manifest, resolved, record, evidence = [_read(p) or {} for p in
        (manifest_path, root/'resolved_treatment.json', root/'attempt.json', root/'learning_evidence.json')]
    if algorithm is not None and resolved.get('algorithm') != algorithm:
        raise PermissionError('attempt belongs to another algorithm')
    candidate = {'attempt_id': record.get('attempt_id'), 'training_complete': True,
                 'path': root.relative_to(artifacts).as_posix()}
    chosen, reasons = select_trusted_attempt(artifacts, manifest.get('campaign_id'),
        {'treatment_id': resolved.get('treatment_id'), 'attempts': [candidate]})
    if chosen is None:
        raise PermissionError('untrusted attempt: ' + ', '.join(reasons))
    return TrustedAttemptContext(manifest_path, manifest, resolved, record, evidence)


def load_trust_contract(artifacts: Path, campaign_id: str) -> CampaignTrustContract:
    artifacts = Path(artifacts)
    path = artifacts/'campaign_manifest.json'
    if not _inside(path, artifacts):
        return CampaignTrustContract({}, {}, {}, ('untrusted_campaign_manifest',))
    manifest = _read(path) or {}
    identity, owners = manifest.get('identity'), manifest.get('optimizer_owners')
    if not isinstance(identity, dict):
        return CampaignTrustContract(manifest, {}, {}, ('campaign_contract_mismatch',))
    reasons, rows, stages = [], {}, {}
    if manifest.get('inputs') and canonical_hash(manifest['inputs']) != (identity or {}).get('input_manifest_sha256'):
        reasons.append('input_manifest_mismatch')
    if ('supervision' in manifest and canonical_hash(manifest['supervision']) != identity.get('supervision_sha256')):
        reasons.append('supervision_policy_mismatch')
    from uc3m.application.evaluation.endpoint_applicability import not_applicable_endpoints
    try:
        not_applicable_endpoints(manifest)
    except (KeyError, ValueError, TypeError):
        reasons.append('endpoint_applicability_mismatch')
    if (manifest.get('campaign_id') != campaign_id or not isinstance(identity, dict)
            or canonical_hash(identity) != manifest.get('spec_hash')):
        reasons.append('campaign_contract_mismatch')
    owner_shape = (isinstance(owners, dict) and bool(owners)
                   and all(isinstance(v, list) and bool(v)
                           and all(isinstance(o, str) and bool(o) for o in v)
                           and len(v) == len(set(v)) for v in owners.values()))
    if (not owner_shape or not isinstance(identity, dict)
            or canonical_hash(owners) != identity.get('optimizer_owners_sha256')):
        reasons.append('optimizer_owners_mismatch')
    stage_records = manifest.get('stages')
    if not isinstance(stage_records, dict):
        stage_records = {}
    if not isinstance(identity, dict) or canonical_hash(stage_records) != identity.get('stage_plan_sha256'):
        reasons.append('stage_plan_identity_mismatch')
    if (not isinstance(identity, dict)
            or canonical_hash(manifest.get('input_policy')) != identity.get('input_policy_sha256')):
        reasons.append('input_policy_mismatch')
    claim_path = artifacts/'campaign.json'
    claim = _read(claim_path) if _inside(claim_path, artifacts) else None
    if (not claim or claim.get('campaign_id') != campaign_id
            or claim.get('spec_hash') != manifest.get('spec_hash')):
        reasons.append('campaign_claim_mismatch')
    for stage, record in stage_records.items():
        try:
            path = contained_path(artifacts, record['path'])
            if not _inside(path, artifacts) or _sha256(path) != record.get('sha256'):
                raise ValueError('stage hash')
            payload = _read(path) or {}
            planned = payload.get('treatments')
            if (payload.get('stage') != stage or not isinstance(planned, list)
                    or record.get('treatments') != len(planned)):
                raise ValueError('stage shape')
            names = []
            for row in planned:
                name = row['treatment_id']
                if (not isinstance(name, str) or name in rows or row.get('stage') != stage
                        or not _count(row.get('seed')) or not _count(row.get('episodes')) or row['episodes'] <= 0
                        or not _count(row.get('episode_time_steps')) or row['episode_time_steps'] <= 0):
                    raise ValueError('planned treatment identity')
                rows[name] = row
                names.append(name)
            stages[stage] = tuple(names)
        except (OSError, ValueError, KeyError, TypeError):
            reasons.append(f'stage_manifest_modified:{stage}')
    if not stages:
        reasons.append('stage_manifests_missing')
    return CampaignTrustContract(manifest, rows, stages, tuple(reasons))


def _attempt_reasons(artifacts, campaign_id, name, attempt, contract):
    try:
        root = contained_path(artifacts, attempt['path'])
        for file in ('attempt.json', 'resolved_treatment.json', 'learning_evidence.json', 'completion.json'):
            if not _inside(root/file, artifacts):
                return [f'untrusted_attempt_path:{name}']
        evidence = _read(root/'learning_evidence.json') or {}
        record = read_attempt(root)
        resolved = _read(root/'resolved_treatment.json') or {}
        planned = contract.rows[name]
        if 'configuration_freeze' in planned.get('requires', []):
            from uc3m.application.training.fresh_campaign import (
                load_configuration_freezes, effective_hyperparameters, resolve_native_arguments)
            freezes = load_configuration_freezes(artifacts, contract.manifest)
            freeze = freezes.get(planned['algorithm'])
            algorithms = contract.manifest.get('algorithm_contract')
            if (freeze is None or not isinstance(algorithms, dict)
                    or canonical_hash(algorithms) != contract.manifest['identity'].get('algorithm_contract_sha256')):
                return [f'unbound_configuration_freeze:{name}']
            effective, clamps = effective_hyperparameters(planned['algorithm'], dict(freeze.hyperparameters),
                                                         algorithms, planned['episode_time_steps'])
            if (resolved.get('configuration_freeze_hash') != freeze.freeze_hash()
                    or resolved.get('hyperparameters') != dict(freeze.hyperparameters)
                    or resolved.get('effective_hyperparameters') != effective
                    or resolved.get('native_clamps') != clamps):
                return [f'configuration_freeze_mismatch:{name}']
            expected_arguments = list(planned['identity_arguments']) + resolve_native_arguments(
                planned['algorithm'], effective, algorithms)
        else:
            expected_arguments = list(planned['native_arguments'])
            if any(resolved.get(k) != planned.get(k) for k in ('hyperparameters', 'effective_hyperparameters')):
                return [f'planned_hyperparameters_mismatch:{name}']
        if resolved.get('phase_buffer') is not None:
            from uc3m.application.training.budget_evidence import read_buffer_proof
            try:
                buffer = read_buffer_proof(root, resolved, record, contract.manifest)
            except (OSError, ValueError, KeyError, TypeError):
                return [f'phase_budget_proof_mismatch:{name}']
            flag = str(buffer['flag'])
            if (expected_arguments.count(flag) != 1 or type(buffer['effective']) is not int
                    or type(buffer['native']) is not int or not 0 < buffer['effective'] <= buffer['native']
                    or int(expected_arguments[expected_arguments.index(flag)+1]) != buffer['native']
                    or buffer.get('reduced') is not (buffer['effective'] < buffer['native'])):
                return [f'phase_buffer_mismatch:{name}']
            expected_arguments[expected_arguments.index(flag)+1] = str(buffer['effective'])
        if resolved.get('native_arguments') != expected_arguments:
            return [f'planned_native_arguments_mismatch:{name}']
        if 'native_arguments' in evidence or 'requires' in planned:
            recorded_args = evidence.get('native_arguments')
            launch_args = expected_arguments + ([] if '--no-resume' in expected_arguments else ['--no-resume'])
            if (not isinstance(recorded_args, list) or recorded_args[:-2] != launch_args
                    or recorded_args[-2:-1] != ['--output-dir']
                    or not isinstance(recorded_args[-1], str) or not recorded_args[-1]):
                return [f'native_evidence_arguments_mismatch:{name}']
        key = treatment_key_from_resolved(resolved, contract.manifest)
        if (not _count(record.get('seed')) or not _count(resolved.get('seed'))
                or not _count(resolved.get('episodes')) or not _count(resolved.get('episode_time_steps'))
                or record.get('treatment') != key.as_dict() or record.get('treatment_id') != key.treatment_id
                or any(resolved.get(k) != planned.get(k) for k in
                       ('treatment_id', 'stage', 'algorithm', 'scenario', 'seed', 'episodes',
                        'episode_time_steps', 'weights', 'dataset_hash', 'requires'))):
            return [f'foreign_treatment:{name}']
        owners = contract.manifest['optimizer_owners'][planned['algorithm']]
        found = attempt_evidence_reasons(evidence, root, campaign_id=campaign_id,
                                        attempt_id=attempt['attempt_id'], treatment_id=key.treatment_id,
                                        seed=planned['seed'], expected_owners=owners)
        reasons = [f'{reason}:{name}' for reason in found]
        if evidence.get('campaign_id') != campaign_id:
            reasons.append(f'foreign_evidence:{name}')
        completion = _read(root/'completion.json') or {}
        if not (evidence.get('verified') is True and type(evidence.get('exit_code')) is int
                and evidence['exit_code'] == 0 and evidence.get('salvage') is None
                and completion.get('training_complete') is True):
            reasons.append(f'unverified_learning:{name}')
        if _checkpoint_reasons(evidence, root):
            reasons.append(f'untrusted_checkpoint:{name}')
        for field, minimum in [('env_steps', planned['episodes']*planned['episode_time_steps']),
                               ('completed_episodes', planned['episodes'])]:
            if not _count(evidence.get(field)) or evidence[field] < minimum:
                reasons.append(f'trajectory_shorter_than_target:{name}')
        weights = evidence.get('effective_axis_weights')
        if (not isinstance(weights, dict) or set(weights) != {'flex', 'carbon', 'cost'}
                or any(isinstance(weights[k], bool) or not isinstance(weights[k], (int, float))
                       or not math.isfinite(weights[k]) or abs(weights[k]-v) > 1e-12
                       for k, v in zip(('flex', 'carbon', 'cost'), planned['weights']))):
            reasons.append(f'effective_weights_mismatch:{name}')
        supervision = evidence.get('supervision')
        ratio = supervision.get('constraint_dominance_ratio') if isinstance(supervision, dict) else None
        limit = contract.manifest.get('supervision', {}).get('max_constraint_dominance_ratio', 1.0)
        if (isinstance(ratio, bool) or not isinstance(ratio, (int, float))
                or not math.isfinite(ratio) or ratio < 0 or ratio > limit):
            reasons.append(f'invalid_supervision:{name}')
        return reasons
    except (OSError, ValueError, KeyError, TypeError):
        return [f'malformed_learning_evidence:{name}']


def select_trusted_attempt(artifacts: Path, campaign_id: str, treatment: dict, *, contract=None):
    """Pick the latest strictly valid completed attempt, never just a true flag."""
    contract = contract or load_trust_contract(artifacts, campaign_id)
    if contract.reasons:
        return None, list(contract.reasons)
    name = treatment.get('treatment_id', '?')
    if name not in contract.rows:
        return None, [f'unplanned_treatment:{name}']
    attempts = [a for a in treatment.get('attempts') or [] if isinstance(a, dict)
                and a.get('training_complete') is True]
    reasons = [f'no_complete_attempt:{name}']
    for attempt in reversed(attempts):
        reasons = _attempt_reasons(Path(artifacts), campaign_id, name, attempt, contract)
        if not reasons:
            return attempt, []
    return None, reasons


def treatment_trust_reasons(artifacts: Path, campaign_id: str, treatment: dict, *, contract=None):
    return select_trusted_attempt(artifacts, campaign_id, treatment, contract=contract)[1]
