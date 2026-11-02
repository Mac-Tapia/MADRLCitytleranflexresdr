"""P02/A04/A15: an attempt is accepted only from evidence bound to it that shows real learning.

Contract agreed between sessions: ``attempt_evidence_reasons(evidence, attempt_root, *,
campaign_id, attempt_id, treatment_id, seed, expected_owners, min_success_ratio=0.99)``
in ``uc3m.application.training.fresh_acceptance`` returns the reasons the evidence
cannot be trusted; an empty list means trustworthy. Expected owners come from the
backend declaration, never from the owners that happen to appear. ``min_success_ratio``
(successful/attempted optimizer steps per owner) is a project criterion: the native
guard drops non-finite steps on purpose, so isolated non-finite events are allowed.
Owner names are the ones the native backends emit (HAPPO actor_agent0..16 + critic,
MASAC masac_policy/critic_q1/critic_q2/alpha, MAAC maac_agentN_policy + maac_critic).
"""
import hashlib
import json
import os
from pathlib import Path

import pytest

from uc3m.application.training import fresh_acceptance as fa

CAMPAIGN = 'fresh_iquitos_20261101_v1'
TREATMENT = 'confirm_MASAC_E1_s1001'
MASAC_OWNERS = ('masac_policy', 'masac_critic_q1', 'masac_critic_q2', 'masac_alpha')


def _bundle_hash(files):
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(Path(path).name.encode('utf-8') + b'\0' + Path(path).read_bytes())
    return digest.hexdigest()


def _attempt(tmp_path, *, attempt_id='a001', seed=1001):
    root = tmp_path/'try_01'
    (root/'native/checkpoints').mkdir(parents=True)
    (root/'attempt.json').write_text(json.dumps({
        'treatment_id': TREATMENT, 'attempt_id': attempt_id, 'seed': seed,
        'initial_episode': 0, 'fresh_start': True}), encoding='utf-8')
    checkpoint = root/'native/checkpoints/policy.pt'
    checkpoint.write_bytes(b'weights')
    evidence = {
        'campaign_id': CAMPAIGN, 'attempt_id': attempt_id, 'env_steps': 50*8760, 'completed_episodes': 50,
        'successful_optimizer_updates_by_owner': {o: 100 for o in MASAC_OWNERS},
        'attempted_optimizer_steps_by_owner': {o: 100 for o in MASAC_OWNERS},
        'initial_parameter_hashes': {o: 'a'*64 for o in MASAC_OWNERS},
        'final_parameter_hashes': {o: 'b'*64 for o in MASAC_OWNERS},
        'nonfinite_events': 0, 'checkpoint_files': ['native/checkpoints/policy.pt'],
        'checkpoint_bundle_hash': _bundle_hash([checkpoint]), 'verified': True, 'exit_code': 0, 'salvage': None}
    return root, evidence


def _reasons(root, evidence, **overrides):
    kwargs = dict(campaign_id=CAMPAIGN, attempt_id='a001', treatment_id=TREATMENT, seed=1001,
                  expected_owners=MASAC_OWNERS)
    kwargs.update(overrides)
    return fa.attempt_evidence_reasons(evidence, root, **kwargs)


def test_verified_attempt_has_no_reasons(tmp_path):
    root, evidence = _attempt(tmp_path)
    assert _reasons(root, evidence) == []


def test_foreign_attempt_zero_updates_missing_checkpoint_rejected(tmp_path):
    # The audited case: weights and supervision look valid, but the evidence belongs to
    # another campaign, every owner has zero updates and the checkpoint does not exist.
    root, evidence = _attempt(tmp_path)
    evidence.update(campaign_id='fresh_other_20261101_v1',
                    successful_optimizer_updates_by_owner={o: 0 for o in MASAC_OWNERS},
                    checkpoint_files=['native/checkpoints/missing.pt'],
                    effective_axis_weights={'flex': 0.6, 'carbon': 0.15, 'cost': 0.25},
                    supervision={'constraint_dominance_ratio': 0.1})
    reasons = _reasons(root, evidence)
    assert 'foreign_campaign' in reasons
    assert all(f'no_successful_update:{o}' in reasons for o in MASAC_OWNERS)
    assert 'checkpoint_missing' in reasons


def test_evidence_of_another_attempt_rejected(tmp_path):
    root, evidence = _attempt(tmp_path)
    evidence['attempt_id'] = 'a002'
    assert 'foreign_attempt' in _reasons(root, evidence)


def test_attempt_json_must_match_the_treatment_being_run(tmp_path):
    root, evidence = _attempt(tmp_path, seed=1002)
    assert 'foreign_seed' in _reasons(root, evidence)
    assert 'foreign_treatment' in _reasons(root, evidence, treatment_id='confirm_MASAC_E2_s1001')
    assert 'foreign_attempt' in _reasons(root, evidence, attempt_id='a003')


def test_missing_attempt_record_rejected(tmp_path):
    root, evidence = _attempt(tmp_path)
    (root/'attempt.json').unlink()
    assert 'attempt_record_missing' in _reasons(root, evidence)


def test_missing_expected_owner_rejected_even_if_others_updated(tmp_path):
    root, evidence = _attempt(tmp_path)
    for key in ('successful_optimizer_updates_by_owner', 'attempted_optimizer_steps_by_owner',
                'initial_parameter_hashes', 'final_parameter_hashes'):
        del evidence[key]['masac_alpha']
    assert 'missing_owner:masac_alpha' in _reasons(root, evidence)


def test_unexpected_owner_is_not_a_substitute(tmp_path):
    root, evidence = _attempt(tmp_path)
    evidence['successful_optimizer_updates_by_owner']['extra_actor'] = 5
    assert 'unexpected_owner:extra_actor' in _reasons(root, evidence)


@pytest.mark.parametrize('count', [True, -3, 2.5, '10', None])
def test_update_counts_must_be_positive_integers(tmp_path, count):
    root, evidence = _attempt(tmp_path)
    evidence['successful_optimizer_updates_by_owner']['masac_policy'] = count
    assert 'invalid_update_count:masac_policy' in _reasons(root, evidence)


def test_isolated_nonfinite_steps_allowed_low_success_ratio_rejected(tmp_path):
    root, evidence = _attempt(tmp_path)
    evidence['attempted_optimizer_steps_by_owner']['masac_policy'] = 101
    evidence['nonfinite_events'] = 1
    assert _reasons(root, evidence) == []
    evidence['attempted_optimizer_steps_by_owner']['masac_policy'] = 200
    assert 'low_success_ratio:masac_policy' in _reasons(root, evidence)
    assert _reasons(root, evidence, min_success_ratio=0.4) == []


@pytest.mark.parametrize('value', [-1, True, 1.5, None])
def test_nonfinite_events_must_be_a_recorded_nonnegative_integer(tmp_path, value):
    root, evidence = _attempt(tmp_path)
    evidence['nonfinite_events'] = value
    assert 'invalid_nonfinite_events' in _reasons(root, evidence)


def test_unchanged_parameters_are_not_learning(tmp_path):
    root, evidence = _attempt(tmp_path)
    evidence['final_parameter_hashes']['masac_critic_q2'] = 'a'*64
    assert 'parameters_unchanged:masac_critic_q2' in _reasons(root, evidence)


@pytest.mark.parametrize('field, value', [('env_steps', True), ('env_steps', -8760), ('env_steps', 0),
                                          ('env_steps', '438000'), ('completed_episodes', False),
                                          ('completed_episodes', -1)])
def test_step_and_episode_counts_must_be_integers(tmp_path, field, value):
    root, evidence = _attempt(tmp_path)
    evidence[field] = value
    assert f'invalid_{field}' in _reasons(root, evidence)


def test_no_checkpoint_listed_rejected(tmp_path):
    root, evidence = _attempt(tmp_path)
    evidence['checkpoint_files'] = []
    assert 'no_checkpoint' in _reasons(root, evidence)


def test_modified_checkpoint_rejected(tmp_path):
    root, evidence = _attempt(tmp_path)
    (root/'native/checkpoints/policy.pt').write_bytes(b'other weights')
    assert 'checkpoint_hash_mismatch' in _reasons(root, evidence)


@pytest.mark.parametrize('listed', ['../outside.pt', 'C:/Windows/win.ini', '/etc/passwd'])
def test_checkpoint_outside_attempt_rejected(tmp_path, listed):
    root, evidence = _attempt(tmp_path)
    (tmp_path/'outside.pt').write_bytes(b'weights')
    evidence['checkpoint_files'] = [listed]
    assert 'checkpoint_outside_attempt' in _reasons(root, evidence)


def test_checkpoint_under_linked_directory_rejected(tmp_path):
    root, evidence = _attempt(tmp_path)
    elsewhere = tmp_path/'elsewhere'
    elsewhere.mkdir()
    (elsewhere/'policy.pt').write_bytes(b'weights')
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(elsewhere), str(root/'native/linked'))
    else:  # pragma: no cover
        os.symlink(elsewhere, root/'native/linked', target_is_directory=True)
    evidence['checkpoint_files'] = ['native/linked/policy.pt']
    evidence['checkpoint_bundle_hash'] = _bundle_hash([elsewhere/'policy.pt'])
    assert 'checkpoint_outside_attempt' in _reasons(root, evidence)


def test_expected_owners_cannot_be_empty(tmp_path):
    root, evidence = _attempt(tmp_path)
    with pytest.raises(ValueError):
        _reasons(root, evidence, expected_owners=())


# --- Wiring into the stage decision (fresh_campaign) -------------------------------------------------

from uc3m.application.training import fresh_campaign as fc  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'


def test_expected_owners_are_declared_per_backend():
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    happo = fc.expected_optimizer_owners('HAPPO', algorithm_config, n_agents=17)
    assert happo == tuple(f'actor_agent{i}' for i in range(17)) + ('critic',)
    assert fc.expected_optimizer_owners('MASAC', algorithm_config, n_agents=17) == MASAC_OWNERS
    maac = fc.expected_optimizer_owners('MAAC', algorithm_config, n_agents=17)
    assert len(maac) == 18 and maac[-1] == 'maac_critic' and maac[0] == 'maac_agent0_policy'
    matd3 = fc.expected_optimizer_owners('MATD3', algorithm_config, n_agents=17)
    assert len(matd3) == 34 and matd3[:2] == ('policy_0/actor', 'policy_0/critic')


def test_completion_with_binding_uses_the_single_evidence_rule(tmp_path):
    root, evidence = _attempt(tmp_path)
    evidence.update(successful_optimizer_updates_by_owner={o: 0 for o in MASAC_OWNERS},
                    effective_axis_weights={'flex': 0.6, 'carbon': 0.15, 'cost': 0.25},
                    supervision={'constraint_dominance_ratio': 0.1})
    decision = fc.attempt_completion(
        evidence, target_episodes=50, episode_time_steps=8760, expected_weights=(0.6, 0.15, 0.25),
        max_constraint_dominance_ratio=1.0, attempt_root=root, campaign_id=CAMPAIGN, attempt_id='a001',
        treatment_id=TREATMENT, seed=1001, expected_owners=MASAC_OWNERS)
    assert decision['training_complete'] is False
    assert 'no_successful_update:masac_policy' in decision['reasons']
    assert 'no_observed_updates' not in decision['reasons']  # the old truthiness rule is not repeated


def _stage_learner(algorithm_config, n_agents, mutate=None):
    def learn(treatment, attempt_root):
        record = json.loads((attempt_root/'attempt.json').read_text(encoding='utf-8'))
        owners = fc.expected_optimizer_owners(treatment['algorithm'], algorithm_config, n_agents=n_agents)
        checkpoint = attempt_root/'native/checkpoints/model.pt'
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_bytes(b'weights')
        weights = dict(zip(fc.REWARD_AXIS_KEYS, treatment['weights']))
        evidence = {
            'campaign_id': record['treatment']['campaign_id'], 'attempt_id': record['attempt_id'],
            'env_steps': treatment['episodes']*treatment['episode_time_steps'],
            'completed_episodes': treatment['episodes'],
            'successful_optimizer_updates_by_owner': {o: 10 for o in owners},
            'attempted_optimizer_steps_by_owner': {o: 10 for o in owners},
            'initial_parameter_hashes': {o: 'a'*64 for o in owners},
            'final_parameter_hashes': {o: 'b'*64 for o in owners},
            'nonfinite_events': 0, 'checkpoint_files': ['native/checkpoints/model.pt'],
            'checkpoint_bundle_hash': _bundle_hash([checkpoint]), 'verified': True, 'exit_code': 0,
            'salvage': None, 'effective_axis_weights': weights,
            'supervision': {'constraint_dominance_ratio': 0.1}}
        if mutate:
            mutate(evidence)
        # Like the native entrypoint, the evidence is persisted inside the attempt.
        (attempt_root/'learning_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')
        return evidence
    return learn


def test_stage_promotes_only_bound_evidence(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    n_agents = fc.schema_agent_count(REPO, json.loads(manifest_path.read_text(encoding='utf-8')))
    assert n_agents == 17
    good = fc.run_stage(manifest_path, 'pilot', _stage_learner(algorithm_config, n_agents), REPO, authorized=True)
    assert good['status'] == 'training_complete'

    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'foreign')
    foreign = fc.run_stage(tmp_path/'foreign/campaign_manifest.json', 'pilot',
                           _stage_learner(algorithm_config, n_agents,
                                          lambda e: e.update(campaign_id='fresh_other_20261101_v1')),
                           REPO, authorized=True)
    assert foreign['completed_treatments'] == 0
    reasons = foreign['treatments'][0]['attempts'][0]['reasons']
    assert 'foreign_campaign' in reasons


@pytest.mark.parametrize('persist', ['absent', 'different'])
def test_only_evidence_persisted_by_the_child_counts(tmp_path, persist):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    learn = _stage_learner(algorithm_config, 17)

    def in_memory(treatment, attempt_root):
        evidence = learn(treatment, attempt_root)
        if persist == 'absent':
            (attempt_root/'learning_evidence.json').unlink()
        else:
            (attempt_root/'learning_evidence.json').write_text(
                json.dumps(dict(evidence, env_steps=1)), encoding='utf-8')
        return evidence

    result = fc.run_stage(manifest_path, 'pilot', in_memory, REPO, authorized=True)
    assert result['completed_treatments'] == 0 and result['stopped_at_phase'] == 0
    ran = [t for t in result['treatments'] if t['attempts']]
    assert {t['treatment_id'].split('/')[1] for t in ran} == {'happo', 'masac'}  # phase 2 never starts
    for treatment in ran:
        assert treatment['attempts'][0]['reasons'] == ['evidence_not_persisted']
    if persist == 'absent':  # run_stage never writes the returned value to disk
        assert not any((tmp_path/'campaign').rglob('learning_evidence.json'))


class _SessionCut(Exception):
    """A Colab session that disconnects in the middle of a stage."""


def test_relaunch_keeps_verified_attempts_and_restarts_the_rest_from_zero(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    good = _stage_learner(algorithm_config, 17)
    calls = []

    def first_session(treatment, attempt_root):
        calls.append((treatment['algorithm'], attempt_root.name))
        if treatment['algorithm'] == 'MASAC':
            raise _SessionCut('runtime disconnected')  # cut inside the learner: no completion.json
        return good(treatment, attempt_root)

    first = fc.run_stage(manifest_path, 'pilot', first_session, REPO, authorized=True)
    assert sorted(calls) == [('HAPPO', 'try_01'), ('MASAC', 'try_01')]  # phase 2 never started
    assert first['status'] == 'incomplete' and first['stopped_at_phase'] == 0
    masac = next(t for t in first['treatments'] if '/masac/' in t['treatment_id'])
    assert 'runtime disconnected' in masac['error']

    second = []

    def second_session(treatment, attempt_root):
        second.append((treatment['algorithm'], attempt_root.name))
        return good(treatment, attempt_root)

    result = fc.run_stage(manifest_path, 'pilot', second_session, REPO, authorized=True)
    assert sorted(second) == [('MAAC', 'try_01'), ('MASAC', 'try_02'), ('MATD3', 'try_01')]
    assert result['status'] == 'training_complete' and result['completed_treatments'] == 4
    by_algorithm = {t['treatment_id'].split('/')[1]: t for t in result['treatments']}
    assert [a['attempt_id'] for a in by_algorithm['happo']['attempts']] == ['a001']
    assert by_algorithm['happo']['reused_verified_attempt'] is True
    assert [a['attempt_id'] for a in by_algorithm['masac']['attempts']] == ['a001', 'a002']
    assert [a['training_complete'] for a in by_algorithm['masac']['attempts']] == [False, True]
    assert by_algorithm['masac']['attempts'][0]['reasons'] == ['interrupted_without_completion']
    assert [a['attempt_id'] for a in by_algorithm['matd3']['attempts']] == ['a001']
    assert [a['attempt_id'] for a in by_algorithm['maac']['attempts']] == ['a001']


def test_tampered_verified_attempt_is_not_reused(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    good = _stage_learner(algorithm_config, 17)
    fc.run_stage(manifest_path, 'pilot', good, REPO, authorized=True)
    for checkpoint in (tmp_path/'campaign').rglob('model.pt'):
        checkpoint.write_bytes(b'restored from a corrupted copy')
    calls = []

    def again(treatment, attempt_root):
        calls.append(attempt_root.name)
        return good(treatment, attempt_root)

    result = fc.run_stage(manifest_path, 'pilot', again, REPO, authorized=True)
    assert calls == ['try_02']*4 and result['completed_treatments'] == 4


def _failed(good, treatment, attempt_root):
    evidence = good(treatment, attempt_root)
    evidence.update(verified=False, exit_code=1)
    (attempt_root/'learning_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')
    return evidence


def test_completion_and_stage_result_are_published_atomically(tmp_path, monkeypatch):
    # The Drive sync copies an attempt as soon as completion.json exists; it must never
    # see a half-written completion.json or stage result.
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    from uc3m.application.training import fresh_policy
    atomic = []
    real = fresh_policy.write_json_atomic

    def spy(path, payload):
        atomic.append(Path(path).name)
        return real(path, payload)

    monkeypatch.setattr(fresh_policy, 'write_json_atomic', spy)
    fc.run_stage(manifest_path, 'pilot', _stage_learner(algorithm_config, 17), REPO, authorized=True)
    assert atomic.count('completion.json') == 4
    assert 'pilot_result.json' in atomic
