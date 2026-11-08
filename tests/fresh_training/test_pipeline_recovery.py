"""I08: failures stop the CLI and interrupted analysis can be retried safely."""
import dataclasses
import hashlib
import json

import pytest

from tests.fresh_training.test_pipeline import (
    REPO, SPLIT, campaign as campaign, synthetic_evaluate,
)
from tests.fresh_training.gate_fixture import synthetic_gate
from uc3m.application import pipeline
from uc3m.application.evaluation.fresh_analysis import FrozenProtocol


def _gate(root, manifest):
    recorded = json.loads(manifest.read_text(encoding='utf-8'))
    identity = recorded['identity']
    return synthetic_gate(root, context={'git_head': identity['source_git_head'], 'source_sha256': identity['source_sha256'],
                                         'test_source_sha256': identity['test_source_sha256']},
                          campaign_id=recorded['campaign_id'], spec_hash=recorded['spec_hash'])


def test_evaluation_failure_stops_the_cli(campaign, capsys):
    code = pipeline.main(['evaluate', '--manifest', str(campaign), '--stage', 'pilot',
                          '--split', 'test_2025', '--project-root', str(REPO)])
    assert code == 2
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report['failed'] and report['status'] != 'ok'


def test_analysis_recovers_without_overwriting_a_stale_partial(campaign):
    pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT, evaluate=synthetic_evaluate)
    partial = campaign.parent/'analysis'/f'pilot_{SPLIT}.partial'
    partial.mkdir(parents=True)
    sentinel = partial/'diagnostic.txt'
    sentinel.write_text('preserve previous cut', encoding='utf-8')
    protocol = dataclasses.replace(FrozenProtocol.default(), seeds=(901,))
    folder = pipeline.analyze_stage(campaign, stage='pilot', split=SPLIT, protocol=protocol)
    assert folder.is_dir() and sentinel.read_text(encoding='utf-8') == 'preserve previous cut'
    report = json.loads((folder/'scientific_report.json').read_text(encoding='utf-8'))
    manifest = json.loads(campaign.read_text(encoding='utf-8'))
    assert report['campaign_id'] == manifest['campaign_id'] and report['status'] == 'incomplete'
    registered = manifest['analyses'][f'pilot:{SPLIT}']
    assert registered['sha256'] == hashlib.sha256((folder/'analysis_manifest.json').read_bytes()).hexdigest()


def test_the_cli_refuses_an_incomplete_analysis_so_a_complete_one_can_follow(campaign, capsys):
    pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT, evaluate=synthetic_evaluate)
    code = pipeline.main(['analyze', '--manifest', str(campaign), '--stage', 'pilot', '--split', SPLIT])
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 2 and report['status'] == 'refused' and 'nothing was published' in report['reason']
    assert not (campaign.parent/'analysis'/f'pilot_{SPLIT}').exists()
    assert f'pilot:{SPLIT}' not in (json.loads(campaign.read_text(encoding='utf-8')).get('analyses') or {})


def test_confirm_test_split_stays_closed_until_a_model_is_selected_on_validation(tmp_path):
    manifest = tmp_path/'campaign_manifest.json'
    manifest.write_text(json.dumps({'campaign_id': 'c', 'analyses': {}}), encoding='utf-8')
    with pytest.raises(PermissionError, match='opens after the selection'):
        pipeline.evaluate_stage(manifest, project_root=REPO, stage='confirm', split='test_2025')
    folder = tmp_path/'analysis'/f'confirm_{SPLIT}'
    folder.mkdir(parents=True)
    (folder/'analysis_manifest.json').write_text('{}', encoding='utf-8')
    manifest.write_text(json.dumps({'campaign_id': 'c', 'analyses': {f'confirm:{SPLIT}': {
        'path': f'analysis/confirm_{SPLIT}/analysis_manifest.json', 'sha256': 'x'}}}), encoding='utf-8')
    with pytest.raises(PermissionError, match='opens after the selection'):      # analyzed, but nothing selected
        pipeline.require_selection_before_test(manifest)
    (folder/'model_selection.json').write_text('{}', encoding='utf-8')
    pipeline.require_selection_before_test(manifest)


def test_a_sensitivity_analysis_names_its_variant(tmp_path):
    with pytest.raises(ValueError, match='--candidate'):
        pipeline.analyze_stage(tmp_path/'campaign_manifest.json', stage='sensitivity', split=SPLIT)


def test_sensitivity_variants_share_seeds_only_when_they_are_not_separated(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from uc3m.application.evaluation import fresh_analysis, results_catalog as rc
    attempts = [SimpleNamespace(stage='sensitivity', treatment_id=f'sensitivity/maac/e1/{variant}/seed_1001')
                for variant in ('p055', 'p065')]
    monkeypatch.setattr(rc, 'discover_attempts', lambda path, **kwargs: attempts)
    monkeypatch.setattr(rc, 'read_evaluation_report', lambda attempt, split, **kwargs: ({}, 'a'*64))
    row = {'campaign_id': 'c', 'algorithm': 'MAAC', 'scenario': 'E1', 'seed': 1001, 'split': SPLIT, 'endpoint': 'k',
           'value': 1.0, 'kpi_report_sha256': 'a'*64}
    monkeypatch.setattr(fresh_analysis, 'rows_from_kpi_report', lambda report, report_sha256: [dict(row)])
    with pytest.raises(ValueError, match='duplicate seed row'):
        rc.build_seed_table(tmp_path, stage='sensitivity', split=SPLIT)
    assert len(rc.build_seed_table(tmp_path, stage='sensitivity', split=SPLIT, candidate='p055').rows) == 1


def test_a_killed_evaluation_worker_is_a_refusal_with_its_action(monkeypatch, capsys, tmp_path):
    from concurrent.futures.process import BrokenProcessPool

    def killed(args):
        raise BrokenProcessPool('killed')
    monkeypatch.setattr(pipeline, '_run', killed)
    assert pipeline.main(['status', '--manifest', str(tmp_path/'m.json')]) == 2
    assert 'finished evaluations are kept' in capsys.readouterr().out


def test_delivery_receives_the_explicit_gate_and_analysis(campaign, tmp_path):
    pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT, evaluate=synthetic_evaluate)
    folder = pipeline.analyze_stage(campaign, stage='pilot', split=SPLIT,
                                    protocol=dataclasses.replace(FrozenProtocol.default(), seeds=(901,)))
    result = pipeline.deliver(campaign, tmp_path/'delivery', stage='pilot', split=SPLIT,
                              gate_report=_gate(tmp_path, campaign), analysis_manifest=folder/'analysis_manifest.json')
    assert result['acceptance']['software_acceptance'] is True
    assert result['acceptance']['scientific_acceptance'] is False
