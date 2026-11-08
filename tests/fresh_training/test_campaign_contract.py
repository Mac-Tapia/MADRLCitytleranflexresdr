"""T6: the fresh campaign DAG, resolved native configuration and completion rules.

The DAG is prepared from configs/experiments/iquitos.yaml without training or a
GPU. Completion is decided from attempt evidence: salvage, interruption,
missing updates or an episode label without a trajectory never promote.
"""
import json
import re
from pathlib import Path

import pytest
import yaml

from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'


@pytest.fixture(scope='module')
def dag():
    return fc.build_dag(fc.load_campaign_config(CONFIG, REPO), REPO)


def test_144_unique_confirmatory_treatments(dag):
    confirm = [t for t in dag.treatments if t.stage == 'confirm']
    assert len(confirm) == 144 and len({t.treatment_id for t in confirm}) == 144
    assert {t.seed for t in confirm} == set(range(1001, 1013))
    budget = dag.budget()
    assert budget['confirm'] == {'treatments': 144, 'episodes': 7200, 'env_steps': 63_072_000}
    # No native clamp (owner 2026-11-01): 8 distinct configurations for HAPPO, MATD3 and MAAC; MASAC searches
    # only rnn_hidden_dim 128 on iquitos_v6 (D-M3-8), 4 configurations: 36 HPO treatments fewer.
    assert budget['hpo'] == {'treatments': 252, 'episodes': 2520, 'env_steps': 22_075_200}
    assert budget['sensitivity'] == {'treatments': 72, 'episodes': 3600, 'env_steps': 31_536_000}
    assert sum(budget[s]['env_steps'] for s in ('hpo', 'confirm', 'sensitivity')) == 116_683_200
    # Owner decision 2026-11-01: the pilot walks 3 full years (8760 steps) per algorithm so it
    # measures real RAM/VRAM and wall time; 4 treatments x 3 x 8760 = 105 120 steps.
    assert budget['pilot'] == {'treatments': 4, 'episodes': 12, 'env_steps': 105_120}
    pilot = [t for t in dag.treatments if t.stage == 'pilot']
    assert {t.seed for t in pilot} == {901} and {t.scenario for t in pilot} == {'E1'}


def test_all_treatments_force_no_resume(dag):
    for treatment in dag.treatments:
        assert '--no-resume' not in treatment.native_arguments  # added by the entrypoint, never optional
        assert not any(a.startswith('--resume') for a in treatment.native_arguments)
    from uc3m.adapters.algorithms.native_entrypoint import native_arguments
    assert native_arguments(list(dag.treatments[0].native_arguments))[-1] == '--no-resume'


def _evidence(**overrides):
    payload = {'verified': True, 'exit_code': 0, 'salvage': None, 'reasons': [], 'completed_episodes': 50,
               'env_steps': 50*8760, 'successful_optimizer_updates_by_owner': {'actor_agent0': 10},
               'checkpoint_files': ['native/checkpoints/a.pt']}
    payload.update(overrides)
    return payload


def test_interrupted_attempt_never_promotes():
    decision = fc.attempt_completion(_evidence(exit_code=None, verified=False, reasons=['native_exit_code:None']),
                                     target_episodes=50, episode_time_steps=8760)
    assert decision['training_complete'] is False and 'interrupted_or_failed' in decision['reasons']
    assert fc.attempt_completion(None, target_episodes=50, episode_time_steps=8760)['reasons'] == ['no_evidence']


def test_salvage_is_not_training_complete():
    decision = fc.attempt_completion(_evidence(salvage="NameError: name 'VecEnvWrapper' is not defined"),
                                     target_episodes=50, episode_time_steps=8760)
    assert decision['training_complete'] is False and 'completed_with_salvage' in decision['reasons']


def test_episode_claim_cannot_replace_trajectory():
    # 49 earlier + 1 resumed labelled 50: the attempt only walked one episode.
    decision = fc.attempt_completion(_evidence(completed_episodes=50, env_steps=8760),
                                     target_episodes=50, episode_time_steps=8760)
    assert decision['training_complete'] is False and 'trajectory_shorter_than_target' in decision['reasons']
    assert fc.attempt_completion(_evidence(), target_episodes=50, episode_time_steps=8760)['training_complete']


def test_weights_only_keeps_tariff_and_assets_equal(dag):
    confirm = [t for t in dag.treatments if t.stage == 'confirm']
    for key in ('schema_path', 'tariff_policy', 'constraint_policy', 'dataset_hash'):
        assert len({getattr(t, key) for t in confirm}) == 1, key
    weights = {t.scenario: t.weights for t in confirm}
    assert weights == {'E1': (0.60, 0.15, 0.25), 'E2': (0.25, 0.60, 0.15), 'E3': (0.15, 0.25, 0.60)}
    extremes = {(t.scenario, t.candidate): t.weights for t in dag.treatments if t.stage == 'sensitivity'}
    assert extremes[('E1', 'p055')] == pytest.approx((0.55, 0.16875, 0.28125))
    assert extremes[('E3', 'p065')] == pytest.approx((0.13125, 0.21875, 0.65))


def test_resolved_config_matches_backend(dag):
    common = (REPO/'CityLearn/scripts/citylearn_v3_training_common.py').read_text(encoding='utf-8')
    shared = set(re.findall(r'add_argument\(\s*"(--[a-z0-9-]+)"', common))  # common launcher parser
    for algorithm in ('HAPPO', 'MASAC', 'MATD3', 'MAAC'):
        source = (REPO/'CityLearn/scripts'/f'train_citylearn_v3_{algorithm.lower()}.py').read_text(encoding='utf-8')
        accepted = set(re.findall(r'add_argument\(\s*"(--[a-z0-9-]+)"', source)) | shared
        for treatment in (t for t in dag.treatments if t.algorithm == algorithm):
            flags = {a for a in treatment.native_arguments if a.startswith('--')}
            assert flags <= accepted, (algorithm, flags - accepted)
    # Native launchers default to CPU with one thread; the campaign runs them on the GPU.
    assert all('--cuda' in t.native_arguments for t in dag.treatments)
    hpo = [t for t in dag.treatments if t.stage == 'hpo' and t.algorithm == 'MAAC']
    assert {t.hyperparameters['learning_rate'] for t in hpo} == {0.0001, 0.0003}
    sample = hpo[0]
    args = sample.native_arguments
    assert args[args.index('--pi-lr') + 1] == args[args.index('--q-lr') + 1] == str(sample.hyperparameters['learning_rate'])


def test_unknown_hyperparameter_fails(tmp_path):
    payload = yaml.safe_load((REPO/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))
    payload['algorithms']['MATD3']['fixed']['entropy_bonus'] = 0.1
    bad = tmp_path/'native.yaml'
    bad.write_text(yaml.safe_dump(payload), encoding='utf-8')
    with pytest.raises(ValueError):
        fc.load_algorithm_config(bad)
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    config['surprise'] = 1
    (tmp_path/'campaign.yaml').write_text(yaml.safe_dump(config), encoding='utf-8')
    with pytest.raises(ValueError):
        fc.load_campaign_config(tmp_path/'campaign.yaml', REPO)


def test_fresh_args_cannot_override_identity():
    with pytest.raises(ValueError):
        fc.resolve_native_arguments('MATD3', {'learning_rate': 1e-4, 'hidden_dimension': 128, 'gamma': 0.99},
                                    fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml'),
                                    extra=['--seed', '7'])


def test_stage_runs_through_injected_learner_and_retries_from_zero(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    calls = []

    def learner(treatment, attempt_root):
        calls.append((treatment['treatment_id'], attempt_root.name))
        assert not any(p.name != 'attempt.json' for p in attempt_root.iterdir())  # fresh, empty attempt
        ok = not (treatment['algorithm'] == 'MASAC' and len(calls) <= 2)
        return _learned(treatment, attempt_root, verified=ok, exit_code=0 if ok else 1,
                        reasons=[] if ok else ['boom'])
    result = fc.run_stage(tmp_path/'campaign/campaign_manifest.json', 'pilot', learner, REPO,
                          authorized=True, max_attempts=2)
    assert result['planned_treatments'] == 4 and result['completed_treatments'] == 4
    masac = [name for tid, name in calls if '/masac/' in tid]
    assert masac == ['try_01', 'try_02'] and result['failed_attempts'] == 1
    with pytest.raises(PermissionError):
        fc.run_stage(tmp_path/'campaign/campaign_manifest.json', 'confirm', learner, REPO, authorized=True)
    with pytest.raises(PermissionError):
        fc.run_stage(tmp_path/'campaign/campaign_manifest.json', 'pilot', learner, REPO, authorized=False)


def test_prepare_needs_no_gpu(tmp_path, monkeypatch):
    import torch
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: pytest.fail('prepare must not probe the GPU'))
    manifest = fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    payload = json.loads((tmp_path/'campaign/campaign_manifest.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'planned' and payload['launch_authorized'] == {}
    assert payload['budget']['confirm']['treatments'] == 144 and manifest['spec_hash'] == payload['spec_hash']
    with pytest.raises(FileExistsError):
        fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')


# ---------------------------------------------------------------------------
# Audit 2026-11-01: frozen configuration, effective weights, replay, MASAC grid.
# ---------------------------------------------------------------------------
AXES = ('flex', 'carbon', 'cost')


def _learned(treatment, attempt_root=None, **overrides):
    """Evidence a correct learner writes, including runtime weights and supervision.

    With ``attempt_root`` the evidence is bound to that attempt (campaign, attempt id,
    every declared optimizer updated, parameters changed, a contained synthetic checkpoint bundle), as
    run_stage requires; without it only the metadata checks of attempt_completion apply.
    """
    payload = {'verified': True, 'exit_code': 0, 'salvage': None, 'reasons': [],
               'env_steps': treatment['episodes']*treatment['episode_time_steps'],
               'completed_episodes': treatment['episodes'],
               'successful_optimizer_updates_by_owner': {'a': 1}, 'checkpoint_files': ['x.pt'],
               'effective_axis_weights': dict(zip(AXES, treatment['weights'])),
               'supervision': {'constraint_dominance_ratio': 0.2, 'saturation_fraction': 0.0}}
    if attempt_root is not None:
        import hashlib
        record = json.loads((attempt_root/'attempt.json').read_text(encoding='utf-8'))
        algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
        owners = fc.expected_optimizer_owners(treatment['algorithm'], algorithm_config, n_agents=17)
        checkpoint = attempt_root/'native/checkpoints/model.pt'
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_bytes(b'weights')
        payload.update(
            campaign_id=record['treatment']['campaign_id'], attempt_id=record['attempt_id'],
            completed_episodes=treatment['episodes'],
            successful_optimizer_updates_by_owner={o: 1 for o in owners},
            attempted_optimizer_steps_by_owner={o: 1 for o in owners},
            initial_parameter_hashes={o: 'a'*64 for o in owners},
            final_parameter_hashes={o: 'b'*64 for o in owners}, nonfinite_events=0,
            checkpoint_files=['native/checkpoints/model.pt'],
            native_arguments=list(treatment['native_arguments']) + ['--no-resume', '--output-dir', str(attempt_root/'native')],
            checkpoint_bundle_hash=hashlib.sha256(
                checkpoint.name.encode('utf-8') + b'\0' + checkpoint.read_bytes()).hexdigest())
    payload.update(overrides)
    if attempt_root is not None:  # like the native entrypoint: evidence lives in the attempt
        (attempt_root/'learning_evidence.json').write_text(json.dumps(payload), encoding='utf-8')
    return payload


def _validation_hash(label):
    from uc3m.domain.campaigns import canonical_hash
    return canonical_hash({'validation_manifest': label})


def _freeze_all(manifest_path, manifest, choose='c2'):
    freezes = []
    for algorithm, candidates in manifest['hpo_candidates_by_algorithm'].items():
        label = choose if choose in candidates else sorted(candidates)[0]
        freezes.append(fc.freeze_configuration(
            manifest['campaign_id'], algorithm, candidates[label], [_validation_hash(algorithm)],
            selection_rule='feasibility_then_mean_normalized_gain_vs_rbc', candidates=sorted(candidates),
            reason=f'test selection {label}'))
    return fc.write_configuration_freezes(manifest_path, freezes)


def _record_calls():
    calls = []

    def learner(treatment, attempt_root):
        calls.append(dict(treatment))
        return _learned(treatment, attempt_root)
    return calls, learner


def _restrict_stage(campaign, stage, keep):
    """Construct a smaller synthetic contract before any attempt; never promote it as the full protocol."""
    from uc3m.domain.campaigns import canonical_hash
    rows_path = campaign/'stages'/f'{stage}.json'
    rows = json.loads(rows_path.read_text(encoding='utf-8'))
    rows['treatments'] = [row for row in rows['treatments'] if keep(row)]
    rows_path.write_text(json.dumps(rows), encoding='utf-8')
    manifest_path = campaign/'campaign_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['stages'][stage]['sha256'] = fc._sha256(rows_path)
    manifest['stages'][stage]['treatments'] = len(rows['treatments'])
    manifest['identity']['stage_plan_sha256'] = canonical_hash(manifest['stages'])
    manifest['spec_hash'] = canonical_hash(manifest['identity'])
    claim_path = campaign/'campaign.json'
    claim = json.loads(claim_path.read_text(encoding='utf-8'))
    claim['spec_hash'] = manifest['spec_hash']
    claim_path.write_text(json.dumps(claim), encoding='utf-8')
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    return rows['treatments']


def test_confirm_refuses_without_valid_freeze_and_marker_is_not_a_freeze(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    payload['configuration_freezes'] = {'unverified_audit_marker': True}   # probe of the audit
    manifest_path.write_text(json.dumps(payload), encoding='utf-8')
    _, learner = _record_calls()
    for stage in ('confirm', 'sensitivity'):
        with pytest.raises(PermissionError):
            fc.run_stage(manifest_path, stage, learner, REPO, authorized=True)


def test_freeze_hash_binds_hyperparameters():
    from uc3m.domain.campaigns import ConfigurationFreeze, canonical_hash
    hyper = {'learning_rate': 0.0001, 'hidden_dimension': 128, 'gamma': 0.99}
    good = fc.freeze_configuration('fresh_iquitos_20261105_v5', 'MATD3', hyper, [_validation_hash('x')],
                                   selection_rule='rule')
    assert good.config_hash == ConfigurationFreeze.config_hash_for('MATD3', hyper)
    with pytest.raises(ValueError):
        ConfigurationFreeze('fresh_iquitos_20261105_v5', 'MATD3', canonical_hash({'other': 1}),
                            (_validation_hash('x'),), 'rule', 'now', hyperparameters=hyper)
    with pytest.raises(ValueError):
        ConfigurationFreeze('fresh_iquitos_20261105_v5', 'MATD3', good.config_hash,
                            (_validation_hash('x'),), 'rule', 'now')


def test_confirm_runs_frozen_hyperparameters_and_identity_includes_them(tmp_path):
    campaign = tmp_path/'campaign'
    fc.prepare_campaign(CONFIG, REPO, artifact_root=campaign)
    manifest_path = campaign/'campaign_manifest.json'
    record = _freeze_all(manifest_path, json.loads(manifest_path.read_text(encoding='utf-8')), choose='c2')
    stored = json.loads((campaign/'configuration_freezes.json').read_text(encoding='utf-8'))
    assert set(stored['freezes']) == {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
    assert record['sha256'] == fc._sha256(campaign/'configuration_freezes.json')
    seen = set()

    def first_per_algorithm(row):
        if row['algorithm'] in seen:
            return False
        seen.add(row['algorithm'])
        return True
    _restrict_stage(campaign, 'confirm', first_per_algorithm)
    calls, learner = _record_calls()
    result = fc.run_stage(manifest_path, 'confirm', learner, REPO, authorized=True)
    assert result['completed_treatments'] == 4
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    for call in calls:
        frozen = stored['freezes'][call['algorithm']]
        assert call['hyperparameters'] == frozen['hyperparameters']
        assert call['configuration_freeze_hash'] == frozen['freeze_hash']
        expected = fc.resolve_native_arguments(call['algorithm'], frozen['hyperparameters'], algorithm_config)
        assert call['native_arguments'][-len(expected):] == expected
        lr_flag = algorithm_config['algorithms'][call['algorithm']]['mapping']['learning_rate'][0]
        args = call['native_arguments']
        assert args[args.index(lr_flag) + 1] == str(frozen['hyperparameters']['learning_rate'])
    # Two different freezes give two different treatment identities.
    base = dict(calls[0])
    other = dict(base, hyperparameters={**base['hyperparameters'], 'gamma': 0.9999},
                 configuration_freeze_hash='0'*64)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert fc._treatment_key(base, manifest).fingerprint() != fc._treatment_key(other, manifest).fingerprint()


def test_tampered_freeze_file_is_refused(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    _freeze_all(manifest_path, json.loads(manifest_path.read_text(encoding='utf-8')))
    path = tmp_path/'campaign/configuration_freezes.json'
    stored = json.loads(path.read_text(encoding='utf-8'))
    stored['freezes']['MATD3']['hyperparameters']['learning_rate'] = 0.5
    path.write_text(json.dumps(stored), encoding='utf-8')
    _, learner = _record_calls()
    with pytest.raises(PermissionError):
        fc.run_stage(manifest_path, 'confirm', learner, REPO, authorized=True)


def test_freeze_must_be_an_hpo_candidate(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    invented = fc.freeze_configuration('fresh_iquitos_20261105_v5', 'MATD3',
                                       {'learning_rate': 0.01, 'hidden_dimension': 64, 'gamma': 0.95},
                                       [_validation_hash('x')], selection_rule='rule')
    with pytest.raises(ValueError):
        fc.write_configuration_freezes(manifest_path, [invented])


def test_sensitivity_writes_hashed_derived_catalog_with_treatment_weights(tmp_path):
    from uc3m.application.configuration import load_scenario_catalog
    from uc3m.domain.objectives import CANONICAL_AXES
    campaign = tmp_path/'campaign'
    fc.prepare_campaign(CONFIG, REPO, artifact_root=campaign)
    manifest_path = campaign/'campaign_manifest.json'
    _freeze_all(manifest_path, json.loads(manifest_path.read_text(encoding='utf-8')))
    rows = _restrict_stage(campaign, 'sensitivity', lambda r: r['algorithm'] == 'MATD3' and r['seed'] == 1001)
    calls, learner = _record_calls()
    result = fc.run_stage(manifest_path, 'sensitivity', learner, REPO, authorized=True)
    assert result['completed_treatments'] == len(rows) == 6
    for call in calls:
        catalog_path = campaign/call['scenario_catalog']
        assert catalog_path.is_file() and catalog_path.parent != REPO/'configs'
        assert call['scenario_catalog_sha256'] == fc.catalog_sha256(catalog_path)
        policy = load_scenario_catalog(catalog_path)[call['scenario']].objective_policy
        assert tuple(policy.weights[a] for a in CANONICAL_AXES) == pytest.approx(tuple(call['weights']), abs=1e-12)
    assert len({c['scenario_catalog_sha256'] for c in calls}) == 6


def test_pilot_points_to_the_single_catalog(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert manifest['scenario_catalog'] == 'configs/scenarios.yaml'
    calls, learner = _record_calls()
    fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True)
    assert {c['scenario_catalog'] for c in calls} == {'configs/scenarios.yaml'}
    assert {c['scenario_catalog_sha256'] for c in calls} == {fc.catalog_sha256(REPO/'configs/scenarios.yaml')}


def test_effective_weights_and_dominance_gate_completion():
    weights = [0.55, 0.16875, 0.28125]
    ok = _learned({'episodes': 50, 'episode_time_steps': 8760, 'weights': weights})
    kwargs = dict(target_episodes=50, episode_time_steps=8760, expected_weights=weights,
                  max_constraint_dominance_ratio=1.0)
    assert fc.attempt_completion(ok, **kwargs)['training_complete']
    wrong = dict(ok, effective_axis_weights={'flex': 0.60, 'carbon': 0.15, 'cost': 0.25})
    assert 'effective_weights_mismatch' in fc.attempt_completion(wrong, **kwargs)['reasons']
    missing = {k: v for k, v in ok.items() if k != 'effective_axis_weights'}
    assert 'effective_weights_unrecorded' in fc.attempt_completion(missing, **kwargs)['reasons']
    dominated = dict(ok, supervision={'constraint_dominance_ratio': 3.0})
    assert 'constraint_terms_dominate_weighted_axes' in fc.attempt_completion(dominated, **kwargs)['reasons']
    unsupervised = {k: v for k, v in ok.items() if k != 'supervision'}
    assert 'supervision_unrecorded' in fc.attempt_completion(unsupervised, **kwargs)['reasons']


def test_dominance_threshold_is_declared_in_the_campaign_config(tmp_path):
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    assert 0 < float(config['supervision']['max_constraint_dominance_ratio']) <= 1.0
    manifest = fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    assert manifest['supervision'] == config['supervision']


def test_replay_and_batch_are_declared_for_off_policy_backends(dag):
    native = yaml.safe_load((REPO/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))
    for algorithm, flag in (('MATD3', '--buffer-size'), ('MAAC', '--buffer-length')):
        for treatment in (t for t in dag.treatments if t.algorithm == algorithm):
            args = treatment.native_arguments
            # MATD3 256; MAAC its author's 1024 (SPEC-015 D-M3-5): the configured value reaches the launcher.
            assert args[args.index('--batch-size') + 1] == str(native['algorithms'][algorithm]['fixed']['batch_size'])
            assert flag in args
    import sys
    if str(REPO/'CityLearn/scripts') not in sys.path:
        sys.path.insert(0, str(REPO/'CityLearn/scripts'))
    from citylearn_v3_training_common import effective_matd3_per_policy_buffer_size
    total = int(native['algorithms']['MATD3']['fixed']['buffer_size'])
    per_policy = effective_matd3_per_policy_buffer_size(total, num_agents=17)
    assert per_policy == 5*8760   # five 8760-step episodes per policy, the MAAC horizon
    # The requirement is bound to the active dataset's measured dims in test_runtime_requirements.py.
    assert int(native['algorithms']['MAAC']['fixed']['buffer_length']) >= 5*8760


def test_masac_grid_has_eight_distinct_native_configurations(dag):
    hpo = [t for t in dag.treatments if t.stage == 'hpo']
    for algorithm in ('HAPPO', 'MASAC', 'MATD3', 'MAAC'):
        rows = [t for t in hpo if t.algorithm == algorithm and t.scenario == 'E1' and t.seed == 901]
        effective = [tuple(sorted(t.effective_hyperparameters.items())) for t in rows]
        expected = 4 if algorithm == 'MASAC' else 8                     # D-M3-8: MASAC only rnn 128 on v6
        assert len(rows) == expected and len(set(effective)) == expected, algorithm
        assert all(not t.native_clamps for t in rows), algorithm
    masac = [t for t in hpo if t.algorithm == 'MASAC']
    assert {t.effective_hyperparameters['hidden_dimension'] for t in masac} == {128}
    for t in masac:
        args = t.native_arguments
        assert args[args.index('--rnn-hidden-dim') + 1] == str(t.hyperparameters['hidden_dimension'])
    assert all(members == [label] for label, members in dag.collapsed_candidates['hpo']['MASAC'].items())


def test_masac_native_update_budget_is_declared():
    native = yaml.safe_load((REPO/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))
    masac = native['algorithms']['MASAC']
    assert masac['fixed']['critic_train_steps'] == 1 and masac['fixed']['critic_batch_size'] == 32
    assert masac['fixed_flags']['critic_train_steps'] == '--critic-train-steps'
    assert masac['fixed_flags']['critic_batch_size'] == '--critic-batch-size'
    assert not any('clamp' in item or 'forced' in item for item in masac.get('declared_limitations', []))
