"""T10: acceptance gate of the fresh campaign; an omission or a tampered artifact never promotes.

Synthetic campaigns are written to temporary directories with the same layout
prepare_campaign/run_stage produce. Software acceptance and scientific
acceptance are reported separately; a prepared campaign without a verified
model is never ready.
"""
import hashlib
import http.client
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest
import yaml

from uc3m.adapters.algorithms.native_entrypoint import _bundle_hash
from uc3m.application.thesis.evidence_registry import EvidenceRegistry
from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance
from uc3m.domain.campaigns import canonical_hash
from uc3m.presentation.training_panel import make_server

HERE = Path(__file__).resolve().parent
CAMPAIGN_ID = 'fresh_test_20261101_v1'
OWNERS = ('policy_0/actor', 'policy_0/critic')


def _planned_row():
    return {'treatment_id': 'confirm-MATD3-E1-s1001', 'stage': 'confirm', 'algorithm': 'MATD3',
            'scenario': 'E1', 'seed': 1001, 'episodes': 1, 'episode_time_steps': 24,
            'native_arguments': [], 'hyperparameters': None, 'weights': [0.6, 0.15, 0.25],
            'dataset_hash': '2'*64}


def _identity():
    stage_hash = hashlib.sha256(json.dumps({'stage': 'confirm', 'treatments': [_planned_row()]}).encode()).hexdigest()
    return {'config_sha256': '1'*64, 'dataset_hash': '2'*64, 'source_sha256': '3'*64,
            'algorithm_config_sha256': '4'*64, 'normalizer_sha256': '5'*64,
            'source_git_head': 'd'*40, 'test_source_sha256': '6'*64,
            'optimizer_owners_sha256': canonical_hash({'MATD3': list(OWNERS)}),
            'input_policy_sha256': canonical_hash(_input_policy()),
            'stage_plan_sha256': canonical_hash({'confirm': {'path': 'stages/confirm.json',
                                                           'sha256': stage_hash, 'treatments': 1}})}


def _input_policy():
    layout = yaml.safe_load((HERE.parents[1]/'governance/repository_layout.yaml').read_text(encoding='utf-8'))
    return {'retired_roots': list(layout['retired_historical_roots'].values()) + layout['forbidden_input_roots']}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _campaign(tmp_path, *, train=True):
    """A prepared campaign with one confirm treatment and, optionally, one verified attempt."""
    root = tmp_path/'outputs/campaigns/test_v1'
    (root/'stages').mkdir(parents=True)
    stage = root/'stages/confirm.json'
    row = _planned_row()
    stage.write_text(json.dumps({'stage': 'confirm', 'treatments': [row]}),
                     encoding='utf-8')
    identity = _identity()
    manifest = {'schema_version': 1, 'campaign_id': CAMPAIGN_ID, 'storage_alias': 'test_v1', 'status': 'planned',
                'spec_hash': canonical_hash(identity), 'identity': identity,
                'optimizer_owners': {'MATD3': list(OWNERS)},
                'input_policy': _input_policy(),
                'stages': {'confirm': {'path': 'stages/confirm.json', 'sha256': _sha(stage), 'treatments': 1}}}
    (root/'campaign_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (root/'campaign.json').write_text(json.dumps({'schema_version': 1, 'campaign_id': CAMPAIGN_ID,
                                                  'spec_hash': manifest['spec_hash']}), encoding='utf-8')
    if train:
        attempt = root/'attempts/confirm/matd3/e1/seed_1001/try_01'
        checkpoint = attempt/'native/E1_s1001/checkpoints/models/actor_agent0.pt'
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_bytes(b'fresh weights')
        from uc3m.application.training.fresh_campaign import _treatment_key
        key = _treatment_key(row, manifest)
        (attempt/'attempt.json').write_text(json.dumps({
            'attempt_id': 'a001', 'treatment_id': key.treatment_id, 'seed': 1001,
            'initial_episode': 0, 'fresh_start': True, 'treatment': key.as_dict()}), encoding='utf-8')
        (attempt/'resolved_treatment.json').write_text(json.dumps(row), encoding='utf-8')
        evidence = {'campaign_id': CAMPAIGN_ID, 'attempt_id': 'a001', 'verified': True, 'exit_code': 0,
                    'salvage': None, 'checkpoint_bundle_hash': _bundle_hash([checkpoint]),
                    'checkpoint_files': [str(checkpoint.relative_to(attempt))],
                    'successful_optimizer_updates_by_owner': {owner: 4 for owner in OWNERS},
                    'attempted_optimizer_steps_by_owner': {owner: 4 for owner in OWNERS},
                    'initial_parameter_hashes': {owner: 'a'*64 for owner in OWNERS},
                    'final_parameter_hashes': {owner: 'b'*64 for owner in OWNERS},
                    'env_steps': 24, 'completed_episodes': 1, 'nonfinite_events': 0,
                    'effective_axis_weights': {'flex': 0.6, 'carbon': 0.15, 'cost': 0.25},
                    'supervision': {'constraint_dominance_ratio': 0.1}}
        (attempt/'learning_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')
        (attempt/'completion.json').write_text(json.dumps({'training_complete': True, 'reasons': []}),
                                               encoding='utf-8')
        result = {'campaign_id': CAMPAIGN_ID, 'stage': 'confirm', 'planned_treatments': 1,
                  'completed_treatments': 1, 'status': 'training_complete',
                  'treatments': [{'treatment_id': 'confirm-MATD3-E1-s1001', 'training_complete': True,
                                  'attempts': [{'attempt_id': 'a001', 'training_complete': True,
                                                'path': attempt.relative_to(root).as_posix()}]}]}
        (root/'stages/confirm_result.json').write_text(json.dumps(result), encoding='utf-8')
    return root/'campaign_manifest.json'


def _passed_gate(tmp_path, **counters):
    from tests.fresh_training.gate_fixture import synthetic_gate
    return synthetic_gate(tmp_path, context={'git_head': 'd'*40, 'source_sha256': '3'*64, 'test_source_sha256': '6'*64},
                          campaign_id=CAMPAIGN_ID, spec_hash=canonical_hash(_identity()), **counters)


def test_skips_xfail_xpass_fail_new_acceptance(tmp_path):
    profile = tmp_path/'profile'
    profile.mkdir()
    shutil.copy(HERE/'conftest.py', profile/'conftest.py')
    for name, body in {'skip': 'pytest.skip("missing input")',
                       'xfail': 'pytest.xfail("known gap")'}.items():
        (profile/f'test_{name}.py').write_text(f'import pytest\n\ndef test_{name}():\n    {body}\n', encoding='utf-8')
    (profile/'test_xpass.py').write_text('import pytest\n\n@pytest.mark.xfail(reason="x")\ndef test_xpass():\n'
                                         '    assert True\n', encoding='utf-8')
    for name in ('skip', 'xfail', 'xpass'):
        done = subprocess.run([sys.executable, '-B', '-m', 'pytest', f'test_{name}.py', '-q', '-p', 'no:cacheprovider'],
                              cwd=profile, capture_output=True, text=True, timeout=300)
        assert done.returncode != 0, (name, done.stdout[-2000:])
        assert f'FRESH-PROFILE REJECTED {name}' in done.stdout
    # A gate report with an omission is not software acceptance either.
    report = verify_fresh_acceptance(_campaign(tmp_path), gate_report=_passed_gate(tmp_path, skipped=1))
    assert report.software_acceptance is False and 'gate_not_clean' in report.reasons


def test_old_manifest_cannot_promote_new_campaign(tmp_path):
    manifest = _campaign(tmp_path)
    payload = json.loads(manifest.read_text(encoding='utf-8'))
    old = dict(payload, campaign_id='iquitos_v4_multiseed')        # pre-fresh identity
    manifest.write_text(json.dumps(old), encoding='utf-8')
    report = verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path))
    assert report.software_acceptance is False and 'not_a_fresh_campaign' in report.reasons
    # A fresh-looking manifest without the ownership claim beside it is foreign too.
    manifest.write_text(json.dumps(payload), encoding='utf-8')
    (manifest.parent/'campaign.json').unlink()
    report = verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path))
    assert report.software_acceptance is False and 'campaign_claim_mismatch' in report.reasons


def test_hash_tamper_blocks_promotion(tmp_path):
    manifest = _campaign(tmp_path)
    assert verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path)).software_acceptance is True
    stage = manifest.parent/'stages/confirm.json'
    stage.write_text(stage.read_text(encoding='utf-8').replace('s1001', 's1002'), encoding='utf-8')
    report = verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path))
    assert report.software_acceptance is False and 'stage_manifest_modified:confirm' in report.reasons
    # The spec hash is recomputed from the identity, not trusted.
    manifest2 = _campaign(tmp_path/'second')
    payload = json.loads(manifest2.read_text(encoding='utf-8'))
    payload['identity']['dataset_hash'] = '3'*64
    manifest2.write_text(json.dumps(payload), encoding='utf-8')
    assert 'spec_hash_mismatch' in verify_fresh_acceptance(manifest2, gate_report=_passed_gate(tmp_path)).reasons
    # Registered evidence is rechecked against its hash before acceptance.
    figure = tmp_path/'figure.json'
    figure.write_text(json.dumps({'campaign_id': CAMPAIGN_ID, 'value': 1}), encoding='utf-8')
    registry = EvidenceRegistry()
    expected = _sha(figure)
    assert registry.register_verified_evidence(figure, expected, CAMPAIGN_ID, 'validation').accepted
    figure.write_text(json.dumps({'campaign_id': CAMPAIGN_ID, 'value': 2}), encoding='utf-8')
    with pytest.raises(PermissionError):
        registry.register_verified_evidence(figure, expected, CAMPAIGN_ID, 'validation')
    other = tmp_path/'other.json'
    other.write_text(json.dumps({'campaign_id': 'iquitos_v4_multiseed'}), encoding='utf-8')
    with pytest.raises(PermissionError):
        registry.register_verified_evidence(other, _sha(other), CAMPAIGN_ID, 'validation')


def test_no_model_is_not_ready(tmp_path):
    report = verify_fresh_acceptance(_campaign(tmp_path, train=False), gate_report=_passed_gate(tmp_path))
    assert report.status == 'not_ready_no_model'
    assert report.software_acceptance is True        # the software gate can pass with nothing trained
    assert report.scientific_acceptance is False and 'no_verified_model' in report.reasons
    trained = verify_fresh_acceptance(_campaign(tmp_path/'trained'), gate_report=_passed_gate(tmp_path))
    assert trained.status == 'trained_not_evaluated' and trained.scientific_acceptance is False


def test_panel_loopback_read_only(tmp_path):
    server = make_server(tmp_path, port=0)
    assert server.server_address[0] == '127.0.0.1'
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        def request(method, path):
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
            connection.request(method, path, body=b'{}' if method != 'GET' else None)
            response = connection.getresponse()
            response.read()
            connection.close()
            return response
        assert request('GET', '/api/runs').status == 200
        assert request('GET', '/api/runs').getheader('Cache-Control') == 'no-store'
        for method in ('POST', 'PUT', 'DELETE'):
            assert request(method, '/api/runs').status in (405, 501)
        assert request('GET', '/../campaign_manifest.json').status == 404
    finally:
        server.shutdown()
        server.server_close()


def test_checkpoint_must_be_trusted_new_artifact(tmp_path):
    manifest = _campaign(tmp_path)
    attempt = manifest.parent/'attempts/confirm/matd3/e1/seed_1001/try_01'
    checkpoint = attempt/'native/E1_s1001/checkpoints/models/actor_agent0.pt'
    checkpoint.write_bytes(b'replaced weights')
    report = verify_fresh_acceptance(manifest, gate_report=_passed_gate(tmp_path))
    assert report.software_acceptance is False and 'untrusted_checkpoint:confirm-MATD3-E1-s1001' in report.reasons
    # A checkpoint path escaping the attempt directory is never followed.
    manifest2 = _campaign(tmp_path/'escape')
    attempt2 = manifest2.parent/'attempts/confirm/matd3/e1/seed_1001/try_01'
    evidence = json.loads((attempt2/'learning_evidence.json').read_text(encoding='utf-8'))
    evidence['checkpoint_files'] = ['../../../../../../model.pt']
    (attempt2/'learning_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')
    report = verify_fresh_acceptance(manifest2, gate_report=_passed_gate(tmp_path))
    assert 'untrusted_checkpoint:confirm-MATD3-E1-s1001' in report.reasons
    # Evidence of another campaign cannot be grafted into this one.
    manifest3 = _campaign(tmp_path/'foreign')
    attempt3 = manifest3.parent/'attempts/confirm/matd3/e1/seed_1001/try_01'
    evidence = json.loads((attempt3/'learning_evidence.json').read_text(encoding='utf-8'))
    evidence['campaign_id'] = 'fresh_other_20261101_v1'
    (attempt3/'learning_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')
    assert 'foreign_evidence:confirm-MATD3-E1-s1001' in verify_fresh_acceptance(
        manifest3, gate_report=_passed_gate(tmp_path)).reasons
