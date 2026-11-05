"""I01: persisted evidence must pass the same contract as native completion."""
import json
import hashlib
import shutil

import pytest

from tests.fresh_training.test_security_and_acceptance import _campaign, _passed_gate
from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance


def _write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.mark.parametrize('field,value', [
    ('env_steps', 0), ('completed_episodes', 0), ('attempt_id', 'a999'),
    ('successful_optimizer_updates_by_owner', {'policy_0/actor': 0, 'policy_0/critic': 0}),
    ('attempted_optimizer_steps_by_owner', {}), ('initial_parameter_hashes', {}),
    ('successful_optimizer_updates_by_owner', 'malformed'),
])
def test_invalid_learning_is_rejected_on_readback(tmp_path, field, value):
    manifest = _campaign(tmp_path)
    gate = _passed_gate(tmp_path)
    assert verify_fresh_acceptance(manifest, gate_report=gate).software_acceptance
    evidence = next(manifest.parent.rglob('learning_evidence.json'))
    payload = json.loads(evidence.read_text(encoding='utf-8'))
    payload[field] = value
    _write(evidence, payload)
    assert not verify_fresh_acceptance(manifest, gate_report=gate).software_acceptance


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'foreign'])
def test_completed_stage_requires_exact_planned_coverage(tmp_path, change):
    manifest = _campaign(tmp_path)
    path = manifest.parent/'stages/confirm_result.json'
    result = json.loads(path.read_text(encoding='utf-8'))
    if change == 'missing':
        result['treatments'] = []
    elif change == 'duplicate':
        result['treatments'] *= 2
    else:
        result['treatments'][0]['treatment_id'] = 'foreign'
    _write(path, result)
    report = verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path))
    assert not report.software_acceptance
    assert not report.scientific_acceptance


@pytest.mark.parametrize('field,value', [('campaign_id', 'fresh_other_v1'), ('git_head', 'e'*40),
                                       ('source_sha256', 'f'*64), ('test_source_sha256', 'f'*64),
                                       ('junit_sha256', '0'*64), ('source_state_stable', False)])
def test_gate_is_bound_to_campaign_sources_and_junit(tmp_path, field, value):
    manifest = _campaign(tmp_path)
    gate = _passed_gate(tmp_path)
    payload = json.loads(gate.read_text(encoding='utf-8'))
    payload[field] = value
    _write(gate, payload)
    assert not verify_fresh_acceptance(manifest, gate_report=gate).software_acceptance


def test_minimal_scientific_claim_is_never_sufficient(tmp_path):
    manifest = _campaign(tmp_path)
    report = manifest.parent/'reports/scientific_report.json'
    report.parent.mkdir()
    _write(report, {'campaign_id': 'fresh_test_20261101_v1', 'status': 'scientifically_complete'})
    result = verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path))
    assert result.software_acceptance and not result.scientific_acceptance


def test_plan_metadata_is_bound_to_the_campaign_identity(tmp_path):
    manifest = _campaign(tmp_path)
    payload = json.loads(manifest.read_text(encoding='utf-8'))
    stage = manifest.parent/'stages/confirm.json'
    planned = json.loads(stage.read_text(encoding='utf-8'))
    planned['treatments'][0]['episodes'] = 2
    _write(stage, planned)
    payload['stages']['confirm']['sha256'] = hashlib.sha256(stage.read_bytes()).hexdigest()
    _write(manifest, payload)
    resolved = next(manifest.parent.rglob('resolved_treatment.json'))
    row = json.loads(resolved.read_text(encoding='utf-8'))
    row['episodes'] = 2
    _write(resolved, row)
    evidence = resolved.parent/'learning_evidence.json'
    value = json.loads(evidence.read_text(encoding='utf-8'))
    value.update(completed_episodes=2, env_steps=48)
    _write(evidence, value)
    assert not verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path)).software_acceptance


def test_catalog_uses_the_attempt_selected_by_strict_validation(tmp_path):
    from uc3m.application.evaluation.results_catalog import discover_attempts
    manifest = _campaign(tmp_path)
    first = next(manifest.parent.rglob('learning_evidence.json')).parent
    second = first.with_name('try_02')
    shutil.copytree(first, second)
    for name in ('attempt.json', 'learning_evidence.json'):
        path = second/name
        payload = json.loads(path.read_text(encoding='utf-8'))
        payload['attempt_id'] = 'a002'
        _write(path, payload)
    next(first.rglob('*.pt')).write_bytes(b'corrupted first attempt')
    result = manifest.parent/'stages/confirm_result.json'
    payload = json.loads(result.read_text(encoding='utf-8'))
    payload['treatments'][0]['attempts'].append({'attempt_id': 'a002', 'training_complete': True,
                                               'path': second.relative_to(manifest.parent).as_posix()})
    _write(result, payload)
    attempts = discover_attempts(manifest)
    assert len(attempts) == 1 and attempts[0].accepted
    assert attempts[0].attempt_id == 'a002' and attempts[0].attempt_root == second
