"""Adversarial readback regressions from the independent implementation review."""
import json

import pytest

from tests.fresh_training.test_pipeline import synthetic_evaluate
from tests.fresh_training.test_security_and_acceptance import _campaign, _sha, CAMPAIGN_ID
from uc3m.application.training import attempt_trust, drive_sync
from uc3m.domain.campaigns import canonical_hash, treatment_key_from_resolved


def _write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def test_short_evaluation_cannot_supply_full_split_scientific_rows(tmp_path):
    from uc3m.application.evaluation.results_catalog import build_seed_table
    manifest = _campaign(tmp_path)
    attempt = next(manifest.parent.rglob('attempt.json')).parent
    synthetic_evaluate(attempt, 'test_2025', tmp_path)
    with pytest.raises(ValueError, match='full|horizon|physical'):
        build_seed_table(manifest, stage='confirm', split='test_2025', require_full_split=True)


def test_self_consistent_native_arguments_must_still_match_planned_configuration(tmp_path):
    manifest_path = _campaign(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    root = next(manifest_path.parent.rglob('attempt.json')).parent
    resolved = json.loads((root/'resolved_treatment.json').read_text())
    resolved['native_arguments'] = ['--gamma', '0.5']
    key = treatment_key_from_resolved(resolved, manifest)
    record = json.loads((root/'attempt.json').read_text())
    record.update(treatment_id=key.treatment_id, treatment=key.as_dict())
    _write(root/'resolved_treatment.json', resolved)
    _write(root/'attempt.json', record)
    with pytest.raises(PermissionError):
        attempt_trust.read_trusted_attempt(root)


def test_reported_native_arguments_are_bound_to_the_resolved_attempt(tmp_path):
    manifest = _campaign(tmp_path)
    root = next(manifest.parent.rglob('attempt.json')).parent
    evidence = json.loads((root/'learning_evidence.json').read_text())
    evidence['native_arguments'] = ['--gamma', '0.5']
    _write(root/'learning_evidence.json', evidence)
    with pytest.raises(PermissionError):
        attempt_trust.read_trusted_attempt(root)


def test_explicitly_required_freeze_cannot_be_bypassed_by_self_consistent_attempt(tmp_path):
    manifest_path = _campaign(tmp_path)
    stage = manifest_path.parent/'stages/confirm.json'
    planned = json.loads(stage.read_text())
    planned['treatments'][0]['requires'] = ['configuration_freeze']
    _write(stage, planned)
    manifest = json.loads(manifest_path.read_text())
    manifest['stages']['confirm']['sha256'] = _sha(stage)
    manifest['identity']['stage_plan_sha256'] = canonical_hash(manifest['stages'])
    manifest['spec_hash'] = canonical_hash(manifest['identity'])
    _write(manifest_path, manifest)
    _write(manifest_path.parent/'campaign.json', {'campaign_id': CAMPAIGN_ID, 'spec_hash': manifest['spec_hash']})
    root = next(manifest_path.parent.rglob('attempt.json')).parent
    with pytest.raises(PermissionError):
        attempt_trust.read_trusted_attempt(root)


def test_drive_keeps_campaign_test_access_record_for_readback(tmp_path):
    manifest = _campaign(tmp_path/'source')
    unlock = manifest.parent/'test_unlock.json'
    unlock.write_text('{"permission":"requires subsequent scientific readback"}', encoding='utf-8')
    drive, target = tmp_path/'drive', tmp_path/'target'
    drive_sync.sync_finished_attempts(manifest.parent, drive)
    report = drive_sync.restore_finished_attempts(drive, target, CAMPAIGN_ID)
    assert not report['conflicts'] and not report['rejected']
    assert (target/'test_unlock.json').read_bytes() == unlock.read_bytes()


def test_supervision_limit_cannot_be_relaxed_outside_the_frozen_identity(tmp_path):
    manifest_path = _campaign(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest['supervision'] = {'max_constraint_dominance_ratio': 100.0}
    _write(manifest_path, manifest)
    root = next(manifest_path.parent.rglob('attempt.json')).parent
    with pytest.raises(PermissionError):
        attempt_trust.read_trusted_attempt(root)


def test_negative_constraint_dominance_is_not_a_measurement(tmp_path):
    manifest = _campaign(tmp_path)
    root = next(manifest.parent.rglob('attempt.json')).parent
    evidence = json.loads((root/'learning_evidence.json').read_text())
    evidence['supervision']['constraint_dominance_ratio'] = -1.0
    _write(root/'learning_evidence.json', evidence)
    with pytest.raises(PermissionError):
        attempt_trust.read_trusted_attempt(root)


def test_completed_episode_target_is_checked_before_phase_advances():
    from uc3m.application.training.fresh_campaign import attempt_completion
    from tests.fresh_training.test_campaign_contract import _evidence
    evidence = _evidence(completed_episodes=1, env_steps=50*8760)
    result = attempt_completion(evidence, target_episodes=50, episode_time_steps=8760)
    assert not result['training_complete']


def test_a_torch_import_failure_refuses_even_a_short_native_attempt():
    from uc3m.adapters.algorithms.native_entrypoint import check_runtime_resources
    result = check_runtime_resources('HAPPO', {'applies_from_episode_time_steps': 1000},
        episode_time_steps=24, measure=lambda: {'ram_gib': 16, 'vram_gib': None,
                                               'torch_import_error': 'WinError1455'})
    assert not result['accepted'] and 'torch_import_failed' in result['reasons']


@pytest.mark.parametrize('steps', [24, 8759, 8760])
def test_physical_metadata_full_horizon_readback_and_hashes(tmp_path, steps):
    from uc3m.application.evaluation.results_catalog import build_seed_table
    manifest = _campaign(tmp_path)
    root = next(manifest.parent.rglob('attempt.json')).parent
    report = synthetic_evaluate(root, 'test_2025', tmp_path)
    folder = root/'evaluation/test_2025'
    report.update(trace_hash='a'*64, baseline_trace_hash='b'*64)
    _write(folder/'kpi_report.json', report)
    _write(folder/'frozen_runs.json', {name: {'split': 'test_2025', 'trace_hash': digest*64,
        'completed_steps': steps, 'training_updates': 0} for name, digest in [('control', 'a'), ('baseline', 'b')]})
    _write(folder/'evaluation_manifest.json', {'schema_version': 2, 'split': 'test_2025',
        'expected_full_split_rows': 8760, 'files': {name: _sha(folder/name) for name in
                                                  ('kpi_report.json', 'frozen_runs.json')}})
    if steps != 8760:
        with pytest.raises(ValueError, match='full physical split'):
            build_seed_table(manifest, split='test_2025', require_full_split=True)
    else:
        assert build_seed_table(manifest, split='test_2025', require_full_split=True).rows
        _write(folder/'frozen_runs.json', {})
        with pytest.raises(ValueError, match='changed'):
            build_seed_table(manifest, split='test_2025', require_full_split=True)
