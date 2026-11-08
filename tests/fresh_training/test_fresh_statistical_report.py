"""D5/D6 of the module 8 plan: one path from real fresh-attempt artifacts to the report and the selection.

The campaign comes from the writers that produce the real layout: prepare_campaign,
run_stage (attempt.json, resolved_treatment.json, learning_evidence.json, completion.json),
pipeline.evaluate_stage over the evaluate_frozen file format (schema 2) and pipeline.analyze_stage.
Only the learner and the KPI values are synthetic. SYNTHETIC VALUES: nothing here is a thesis result.
"""
import csv
import hashlib
import json
import shutil
import uuid
from pathlib import Path

import pytest
import yaml

from tests.fresh_training.test_attempt_acceptance import _stage_learner
from tools.eval import build_campaign_statistical_report as tool
from uc3m.adapters.local_artifacts import LocalArtifactStore
from uc3m.application import pipeline
from uc3m.application.artifacts import BackupVerificationError, RetentionPolicy, backup_run
from uc3m.application.evaluation import fresh_analysis as fa
from uc3m.application.evaluation import results_catalog as rc
from uc3m.application.training import drive_sync as ds
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
SPLIT = 'validation_2024'
STAGE = 'pilot'
SEEDS = [901, 902, 903]
LEVEL = {'HAPPO': 0.10, 'MASAC': 0.20, 'MATD3': 0.30, 'MAAC': 0.40}
OFFSET = {901: 0.00, 902: 0.01, 903: 0.03}
EXPECTED_ROWS = {'train_2023': 8760, 'validation_2024': 8784, 'test_2025': 8760}
AXIS_OF = {'E1': 'flexibility', 'E2': 'co2_emissions', 'E3': 'energy_cost'}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _gain(algorithm, seed):
    return LEVEL[algorithm] + OFFSET[seed]


def _write_evaluation(attempt_root, split_id, gain=None):
    """The file format of evaluate_frozen; the values depend on the algorithm and the seed."""
    attempt_root = Path(attempt_root)
    folder = attempt_root/'evaluation'/split_id
    folder.mkdir(parents=True, exist_ok=True)
    record = json.loads((attempt_root/'attempt.json').read_text(encoding='utf-8'))
    treatment = json.loads((attempt_root/'resolved_treatment.json').read_text(encoding='utf-8'))
    evidence = json.loads((attempt_root/'learning_evidence.json').read_text(encoding='utf-8'))
    algorithm, scenario, seed = treatment['algorithm'], treatment['scenario'], int(record['seed'])
    value = _gain(algorithm, seed) if gain is None else gain
    report = {'context': {'campaign_id': evidence['campaign_id'], 'treatment_id': record['treatment_id'],
                          'algorithm': algorithm, 'scenario': scenario, 'seed': seed, 'split': split_id},
              'axis_gains': {'flexibility': value, 'co2_emissions': value, 'energy_cost': value},
              'trace_hash': 'a'*64, 'baseline_trace_hash': 'b'*64,
              'comparable_kpi_gains': [{'name': name, 'gain': None if name == 'price_signal_deviation' else value/2,
                                        'available': name != 'price_signal_deviation'}
                                       for _, (scen, kpis) in fa.comparable_kpis().items()
                                       if scen == scenario for name in kpis]}
    (folder/'kpi_report.json').write_text(json.dumps(report), encoding='utf-8')
    runs = {name: {'split': split_id, 'trace_hash': digest*64, 'completed_steps': EXPECTED_ROWS[split_id],
                   'training_updates': 0} for name, digest in [('control', 'a'), ('baseline', 'b')]}
    (folder/'frozen_runs.json').write_text(json.dumps(runs), encoding='utf-8')
    (folder/'evaluation_manifest.json').write_text(json.dumps(
        {'schema_version': 2, 'split': split_id, 'expected_full_split_rows': EXPECTED_ROWS[split_id],
         'files': {name: _sha(folder/name) for name in ('kpi_report.json', 'frozen_runs.json')}}), encoding='utf-8')


def _evaluate(attempt_root, split_id, campaign_root, **_):
    _write_evaluation(attempt_root, split_id)


@pytest.fixture(scope='module')
def evaluated(tmp_path_factory):
    """Trained and evaluated, not analyzed: 4 algorithms x 3 scenarios x 3 seeds."""
    root = tmp_path_factory.mktemp('fresh_report')
    # Campaign inputs must resolve inside the project (integrity._relative), as in native_attempts.
    owned = REPO/'.superpowers/sdd/remediacion_integrada'/('report_' + uuid.uuid4().hex)
    owned.mkdir(parents=True)
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    config['stages'] = {STAGE: {'episodes': 2, 'episode_time_steps': 24, 'seeds': SEEDS,
                                'scenarios': ['E1', 'E2', 'E3']}}
    config['resource_authorization'] = {'authorized_stages': [STAGE]}
    config_path = owned/'config.yaml'
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')
    fc.prepare_campaign(config_path, REPO, artifact_root=root/'campaign')
    manifest = root/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/config['algorithm_config'])
    result = fc.run_stage(manifest, STAGE, _stage_learner(algorithm_config, 17), REPO, authorized=True)
    assert result['status'] == 'training_complete' and result['completed_treatments'] == 36
    done = pipeline.evaluate_stage(manifest, project_root=REPO, stage=STAGE, split=SPLIT, evaluate=_evaluate)
    assert len(done['evaluated']) == 36 and not done['failed']
    shutil.rmtree(owned)
    return manifest


@pytest.fixture(scope='module')
def analyzed(evaluated, tmp_path_factory):
    target = tmp_path_factory.mktemp('fresh_report_analyzed')/'campaign'
    shutil.copytree(evaluated.parent, target)
    manifest = target/'campaign_manifest.json'
    pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    return manifest


def _copy(manifest, tmp_path):
    target = tmp_path/'copy'
    shutil.copytree(manifest.parent, target)
    return target/'campaign_manifest.json'


def _run_tool(manifest, out):
    return tool.main(['--manifest', str(manifest), '--stage', STAGE, '--split', SPLIT, '--output-dir', str(out)])


def _refused(manifest, tmp_path, capsys):
    out = tmp_path/'report'
    assert _run_tool(manifest, out) == 2
    assert not out.exists() or not any(out.iterdir())
    return capsys.readouterr().err


def _report_of(attempt):
    return attempt.attempt_root/'evaluation'/SPLIT/'kpi_report.json'


def _append_space(path):
    path.write_text(path.read_text(encoding='utf-8') + ' ', encoding='utf-8')


# --- the fixture is the real layout ---------------------------------------------------------------


def test_the_fixture_has_the_real_layout_and_the_old_catalog_finds_nothing(evaluated):
    roots = [a.attempt_root for a in rc.discover_attempts(evaluated)]
    assert len(roots) == 36
    for root in roots:
        for name in ('attempt.json', 'resolved_treatment.json', 'learning_evidence.json', 'completion.json'):
            assert (root/name).is_file()
        assert not (root/'evidence.json').exists() and not (root/'experiment.json').exists()
        assert 'status' not in json.loads((root/'completion.json').read_text(encoding='utf-8'))
    assert rc.discover_runs(evaluated.parent) == []


# --- D6: seed table, statistics ---------------------------------------------------------------------


def test_report_is_built_from_real_attempts_with_every_seed(analyzed, tmp_path):
    out = tmp_path/'report'
    assert _run_tool(analyzed, out) == 0
    report = json.loads((out/tool.REPORT_JSON).read_text(encoding='utf-8'))
    assert report['campaign_id'] == json.loads(analyzed.read_text(encoding='utf-8'))['campaign_id']
    assert report['stage'] == STAGE and report['split'] == SPLIT
    assert report['status'] == 'analysis_complete' and report['scientific_acceptance'] is False
    assert report['excluded_attempts'] == []
    registered = json.loads(analyzed.read_text(encoding='utf-8'))['analyses'][f'{STAGE}:{SPLIT}']
    assert report['source_analysis']['sha256'] == registered['sha256']
    with (out/tool.SEED_TABLE_CSV).open(encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    axis = {(r['algorithm'], r['scenario'], int(r['seed'])): float(r['value'])
            for r in rows if r['endpoint'] == AXIS_OF[r['scenario']]}
    assert len(axis) == 36
    for (algorithm, _, seed), value in axis.items():
        assert value == pytest.approx(_gain(algorithm, seed))
    for row in rows:
        assert len(row['kpi_report_sha256']) == 64


def test_every_figure_of_the_tool_is_the_one_pipeline_analyze_wrote(analyzed, tmp_path):
    out = tmp_path/'report'
    assert _run_tool(analyzed, out) == 0
    report = json.loads((out/tool.REPORT_JSON).read_text(encoding='utf-8'))
    folder = analyzed.parent/'analysis'/f'{STAGE}_{SPLIT}'
    source = json.loads((folder/'scientific_report.json').read_text(encoding='utf-8'))
    by_key = {(s['algorithm'], s['scenario'], s['endpoint']): s for s in source['seed_statistics']}
    assert len(report['treatments']) == len(by_key) > 0
    for row in report['treatments']:
        expected = by_key[(row['algorithm'], row['scenario'], row['endpoint'])]
        assert (row['mean'], row['std'], row['iqm']) == (expected['mean'], expected['std'], expected['iqm'])
        assert [row['ci_low'], row['ci_high']] == list(expected['ci95_mean'])
        assert row['seeds'] == SEEDS and row['n_seeds'] == 3
    (flex,) = [c for c in report['comparisons'] if c['scenario'] == 'E1' and c['endpoint'] == 'flexibility']
    assert flex['descriptive_leader']['algorithm'] == 'MAAC'
    assert flex['inferential_decision']['omnibus']['test'] == 'friedman'
    # Three seeds cannot reach Holm significance: the leader stays descriptive.
    assert flex['inferential_decision']['superior_algorithm'] is None


def test_no_analysis_registered_is_refused_and_points_to_the_single_path(evaluated, tmp_path, capsys):
    err = _refused(_copy(evaluated, tmp_path), tmp_path, capsys)
    assert 'pipeline analyze' in err


def test_old_arguments_and_implicit_campaigns_are_gone(tmp_path):
    for argv in (['--results-root', str(tmp_path)], ['--campaign-config', 'x.yaml'], []):
        with pytest.raises(SystemExit) as refused:
            tool.main(argv)
        assert refused.value.code == 2


def test_an_existing_report_is_never_overwritten(analyzed, tmp_path, capsys):
    out = tmp_path/'report'
    assert _run_tool(analyzed, out) == 0
    before = _sha(out/tool.REPORT_JSON)
    assert _run_tool(analyzed, out) == 2
    assert 'overwritten' in capsys.readouterr().err and _sha(out/tool.REPORT_JSON) == before


# --- D6: fail closed, with the reason --------------------------------------------------------------


def test_untrusted_attempt_is_excluded_with_its_reason_in_the_published_analysis(evaluated, tmp_path, capsys):
    manifest = _copy(evaluated, tmp_path)
    victim = rc.discover_attempts(manifest)[0]
    (victim.attempt_root/'native/checkpoints/model.pt').write_bytes(b'tampered')
    folder = pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    report = json.loads((folder/'scientific_report.json').read_text(encoding='utf-8'))
    assert report['status'] == 'incomplete' and report['coverage']['complete'] is False
    (excluded,) = report['excluded_attempts']
    assert excluded['treatment_id'] == victim.treatment_id
    assert any('untrusted_checkpoint' in reason for reason in excluded['reasons'])
    table = json.loads((folder/'seed_table.json').read_text(encoding='utf-8'))['rows']
    assert victim.seed not in {r['seed'] for r in table
                               if r['algorithm'] == victim.algorithm and r['scenario'] == victim.scenario}
    err = _refused(manifest, tmp_path, capsys)
    assert victim.treatment_id in err and 'untrusted_checkpoint' in err


def test_missing_evaluation_is_a_named_exclusion(evaluated, tmp_path, capsys):
    manifest = _copy(evaluated, tmp_path)
    victim = rc.discover_attempts(manifest)[0]
    shutil.rmtree(victim.attempt_root/'evaluation')
    folder = pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    report = json.loads((folder/'scientific_report.json').read_text(encoding='utf-8'))
    (excluded,) = report['excluded_attempts']
    assert excluded['treatment_id'] == victim.treatment_id and excluded['reasons'] == [f'evaluation_missing:{SPLIT}']
    err = _refused(manifest, tmp_path, capsys)
    assert victim.treatment_id in err and 'evaluation_missing' in err


def test_changed_evaluations_stop_the_analysis_naming_every_attempt(evaluated, tmp_path):
    manifest = _copy(evaluated, tmp_path)
    victims = rc.discover_attempts(manifest)[:2]
    for victim in victims:
        _append_space(_report_of(victim))
    with pytest.raises(ValueError) as refused:
        pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    for victim in victims:
        assert victim.treatment_id in str(refused.value)
    assert 'sha256' in str(refused.value)
    assert not (manifest.parent/'analysis'/f'{STAGE}_{SPLIT}').exists()


def test_audit_lists_every_attempt_and_never_counts_an_unverified_one(evaluated, tmp_path):
    manifest = _copy(evaluated, tmp_path)
    changed, removed, untrusted = rc.discover_attempts(manifest)[:3]
    _append_space(_report_of(changed))
    shutil.rmtree(removed.attempt_root/'evaluation')
    (untrusted.attempt_root/'native/checkpoints/model.pt').write_bytes(b'tampered')
    audit = {a.treatment_id: a for a in rc.audit_stage_evaluations(manifest, stage=STAGE, split=SPLIT)}
    assert len(audit) == 36 and sum(a.included for a in audit.values()) == 33
    assert audit[changed.treatment_id].evaluation_unverified
    assert any('sha256' in reason for reason in audit[changed.treatment_id].reasons)
    assert audit[removed.treatment_id].reasons == (f'evaluation_missing:{SPLIT}',)
    assert any('untrusted_checkpoint' in r for r in audit[untrusted.treatment_id].reasons)
    assert not audit[untrusted.treatment_id].evaluation_unverified


def test_an_attempt_changed_after_the_analysis_stops_the_report(analyzed, tmp_path, capsys):
    manifest = _copy(analyzed, tmp_path)
    victim = rc.discover_attempts(manifest)[0]
    (victim.attempt_root/'native/checkpoints/model.pt').write_bytes(b'tampered')
    err = _refused(manifest, tmp_path, capsys)
    assert victim.treatment_id in err and 'untrusted_checkpoint' in err


def test_a_report_changed_after_the_analysis_stops_the_report(analyzed, tmp_path, capsys):
    manifest = _copy(analyzed, tmp_path)
    victim = rc.discover_attempts(manifest)[0]
    _append_space(_report_of(victim))
    err = _refused(manifest, tmp_path, capsys)
    assert victim.treatment_id in err and 'sha256' in err


def _rehash_analysis(manifest, mutate):
    """A forger who rewrites one figure and every digest of the analysis chain."""
    folder = manifest.parent/'analysis'/f'{STAGE}_{SPLIT}'
    report = json.loads((folder/'scientific_report.json').read_text(encoding='utf-8'))
    mutate(report)
    (folder/'scientific_report.json').write_text(json.dumps(report), encoding='utf-8')
    analysis = json.loads((folder/'analysis_manifest.json').read_text(encoding='utf-8'))
    analysis['files']['scientific_report.json'] = _sha(folder/'scientific_report.json')
    (folder/'analysis_manifest.json').write_text(json.dumps(analysis), encoding='utf-8')
    record = json.loads(manifest.read_text(encoding='utf-8'))
    record['analyses'][f'{STAGE}:{SPLIT}']['sha256'] = _sha(folder/'analysis_manifest.json')
    manifest.write_text(json.dumps(record), encoding='utf-8')


def test_a_figure_rewritten_with_a_consistent_hash_chain_is_detected(analyzed, tmp_path, capsys):
    manifest = _copy(analyzed, tmp_path)
    _rehash_analysis(manifest, lambda report: report['seed_statistics'][0].update(mean=9.0))
    assert 'recomputed' in _refused(manifest, tmp_path, capsys)


def test_a_changed_analysis_file_is_detected(analyzed, tmp_path, capsys):
    manifest = _copy(analyzed, tmp_path)
    _append_space(manifest.parent/'analysis'/f'{STAGE}_{SPLIT}'/'seed_table.json')
    assert 'seed_table.json' in _refused(manifest, tmp_path, capsys)


# --- FR-005.6: selection command ---------------------------------------------------------------------


def _hypervolume(algorithm, seed):
    return fa.hypervolume([(_gain(algorithm, seed),)*3])


def test_select_reads_the_verified_analysis_and_never_names_a_winner_without_significance(analyzed, tmp_path, capsys):
    manifest = _copy(analyzed, tmp_path)
    assert pipeline.main(['select', '--manifest', str(manifest), '--stage', STAGE, '--split', SPLIT]) == 0
    printed = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert printed['status'] == 'ok'
    target = manifest.parent/'analysis'/f'{STAGE}_{SPLIT}'/'model_selection.json'
    selection = json.loads(target.read_text(encoding='utf-8'))
    assert selection['descriptive_candidate'] == 'MAAC' and selection['selection_kind'] == 'descriptive'
    assert selection['inferential_winner'] is None and selection['inferential_status'] == 'no_inferential_winner'
    assert selection['scientific_acceptance'] is False and selection['split'] == SPLIT
    registered = json.loads(manifest.read_text(encoding='utf-8'))['analyses'][f'{STAGE}:{SPLIT}']
    assert selection['analysis_manifest_sha256'] == registered['sha256']
    assert selection['ranking'][0]['algorithm'] == 'MAAC'
    for row in selection['ranking']:
        expected = [_hypervolume(row['algorithm'], seed) for seed in SEEDS]
        assert row['n_seeds'] == 3 and row['mean_hypervolume'] == pytest.approx(sum(expected)/3)
        assert [row['hypervolume_by_seed'][str(seed)] for seed in SEEDS] == pytest.approx(expected)
    assert pipeline.main(['select', '--manifest', str(manifest), '--stage', STAGE, '--split', SPLIT]) == 2
    assert 'overwritten' in json.loads(capsys.readouterr().out.strip().splitlines()[-1])['reason']


def test_select_never_reads_the_test_split(analyzed, capsys):
    assert pipeline.main(['select', '--manifest', str(analyzed), '--stage', STAGE, '--split', 'test_2025']) == 2
    assert 'validation' in json.loads(capsys.readouterr().out.strip().splitlines()[-1])['reason']


def test_select_refuses_an_incomplete_campaign(evaluated, tmp_path):
    manifest = _copy(evaluated, tmp_path)
    shutil.rmtree(rc.discover_attempts(manifest)[0].attempt_root/'evaluation')
    pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    with pytest.raises(ValueError, match='incomplete'):
        pipeline.select_model(manifest, stage=STAGE, split=SPLIT)


def test_select_refuses_a_changed_attempt(analyzed, tmp_path):
    manifest = _copy(analyzed, tmp_path)
    (rc.discover_attempts(manifest)[0].attempt_root/'native/checkpoints/model.pt').write_bytes(b'tampered')
    with pytest.raises(ValueError):
        pipeline.select_model(manifest, stage=STAGE, split=SPLIT)
    assert not (manifest.parent/'analysis'/f'{STAGE}_{SPLIT}'/'model_selection.json').exists()


def test_selection_reports_saturated_gains_and_keeps_the_originals(evaluated, tmp_path):
    manifest = _copy(evaluated, tmp_path)
    attempt = next(a for a in rc.discover_attempts(manifest) if a.algorithm == 'HAPPO' and a.scenario == 'E1')
    folder = attempt.attempt_root/'evaluation'/SPLIT
    shutil.rmtree(folder)
    _write_evaluation(attempt.attempt_root, SPLIT, gain=1.5)
    pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    selection = pipeline.select_model(manifest, stage=STAGE, split=SPLIT)
    row = next(r for r in selection['ranking'] if r['algorithm'] == 'HAPPO')
    assert row['saturated_axes'] == {str(attempt.seed): ['flexibility']}


# --- D5: FR-008.3 for fresh attempts ---------------------------------------------------------------


def _snapshot(root):
    return {p.relative_to(root).as_posix(): _sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not p.name.endswith('.lock')}


def test_backup_run_refuses_a_fresh_attempt_and_names_the_copy_that_applies(evaluated, tmp_path):
    attempt = rc.discover_attempts(evaluated)[0].attempt_root
    policy = RetentionPolicy.from_mapping(yaml.safe_load(
        (REPO/'governance/artifact_retention_policy.yaml').read_text(encoding='utf-8')))
    store = LocalArtifactStore(tmp_path/'backup', producer='test')
    with pytest.raises(BackupVerificationError, match='drive_sync'):
        backup_run(attempt, store, policy)
    assert not (tmp_path/'backup').exists() or not any((tmp_path/'backup').iterdir())


def test_drive_copy_restores_every_file_by_hash_and_the_report_runs_on_the_restored_campaign(analyzed, tmp_path):
    source = _copy(analyzed, tmp_path).parent
    drive, restored = tmp_path/'drive', tmp_path/'restored'
    pipeline.select_model(source/'campaign_manifest.json', stage=STAGE, split=SPLIT)
    assert not ds.sync_finished_attempts(source, drive)['conflicts']
    report = ds.restore_finished_attempts(drive, restored, json.loads(
        (source/'campaign_manifest.json').read_text(encoding='utf-8'))['campaign_id'])
    assert not report['conflicts'] and not report['rejected'] and len(report['restored_complete']) == 36
    before, after = _snapshot(source), _snapshot(restored)
    kept = {k: v for k, v in before.items() if k.startswith(('analysis/', f'{STAGE}/', 'stages/'))
            or k == 'campaign_manifest.json'}
    assert kept and {k: after.get(k) for k in kept} == kept
    assert f'analysis/{STAGE}_{SPLIT}/model_selection.json' in after
    assert _run_tool(restored/'campaign_manifest.json', tmp_path/'report') == 0


def test_a_byte_changed_on_the_drive_copy_is_rejected(analyzed, tmp_path):
    source = _copy(analyzed, tmp_path).parent
    drive = tmp_path/'drive'
    assert not ds.sync_finished_attempts(source, drive)['conflicts']
    campaign_id = json.loads((source/'campaign_manifest.json').read_text(encoding='utf-8'))['campaign_id']
    attempt = rc.discover_attempts(source/'campaign_manifest.json')[0].attempt_root
    relative = attempt.relative_to(source)
    copied = drive/relative/'attempt.json'
    original = copied.read_bytes()
    copied.write_bytes(original + b' ')
    report = ds.restore_finished_attempts(drive, tmp_path/'first', campaign_id)
    assert report['rejected'][relative.as_posix()] == ['drive_copy_digest_mismatch']
    copied.write_bytes(original)
    evaluation = drive/relative/'evaluation'/SPLIT/'kpi_report.json'
    evaluation.write_bytes(evaluation.read_bytes() + b' ')
    report = ds.restore_finished_attempts(drive, tmp_path/'second', campaign_id)
    assert (relative/'evaluation'/SPLIT/'kpi_report.json').as_posix() in report['conflicts']


# --- the real pilot of configs/experiments/iquitos.yaml: one seed, E1 only -------------------------


def test_the_one_seed_pilot_gives_no_inferential_report_and_no_selection(tmp_path, capsys):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    fc.run_stage(manifest, STAGE, _stage_learner(algorithm_config, 17), REPO, authorized=True)
    done = pipeline.evaluate_stage(manifest, project_root=REPO, stage=STAGE, split=SPLIT, evaluate=_evaluate)
    assert len(done['evaluated']) == 4
    pipeline.analyze_stage(manifest, stage=STAGE, split=SPLIT)
    assert 'at least 2 seeds' in _refused(manifest, tmp_path, capsys)
    with pytest.raises(ValueError, match='incomplete'):
        pipeline.select_model(manifest, stage=STAGE, split=SPLIT)
