"""P10: the post-training pipeline composes existing use cases; it never trains.

status → freeze (HPO, validation only) → evaluate (frozen policies) → analyze (seed
table + scientific report) → deliver. Every step reads the explicit campaign, never
overwrites a result and reports refusals as data. Frozen evaluations run in parallel
worker processes because each attempt writes only inside its own folder.
"""
import ast
import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from tests.fresh_training.test_attempt_acceptance import _stage_learner
from uc3m.application import pipeline
from uc3m.application.evaluation import fresh_analysis as fa
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
SPLIT = 'validation_2024'


def synthetic_evaluate(attempt_root, split_id, campaign_root, **_):
    """Writes the evaluate_frozen layout (kpi_report.json + evaluation_manifest.json)."""
    attempt_root = Path(attempt_root)
    folder = attempt_root/'evaluation'/split_id
    if (folder/'kpi_report.json').exists():
        raise FileExistsError(folder)
    record = json.loads((attempt_root/'attempt.json').read_text(encoding='utf-8'))
    treatment = json.loads((attempt_root/'resolved_treatment.json').read_text(encoding='utf-8'))
    evidence = json.loads((attempt_root/'learning_evidence.json').read_text(encoding='utf-8'))
    report = {'context': {'campaign_id': evidence['campaign_id'], 'treatment_id': record['treatment_id'],
                          'algorithm': treatment['algorithm'], 'scenario': treatment['scenario'],
                          'seed': int(record['seed']), 'split': split_id},
              'axis_gains': {'flexibility': 0.1, 'co2_emissions': 0.2, 'energy_cost': 0.3}}
    folder.mkdir(parents=True)
    path = folder/'kpi_report.json'
    path.write_text(json.dumps(report), encoding='utf-8')
    (folder/'evaluation_manifest.json').write_text(json.dumps(
        {'files': {'kpi_report.json': hashlib.sha256(path.read_bytes()).hexdigest()}}), encoding='utf-8')
    return report


@pytest.fixture()
def campaign(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    fc.run_stage(manifest_path, 'pilot', _stage_learner(algorithm_config, 17), REPO, authorized=True)
    return manifest_path


def test_status_lists_reasons_after_cut(campaign):
    attempt = next(p for p in campaign.parent.rglob('model.pt'))
    attempt.write_bytes(b'corrupted after a session cut')
    rows = pipeline.stage_status(campaign)
    assert len(rows) == 4
    refused = [r for r in rows if not r['accepted']]
    assert len(refused) == 1 and any('untrusted_checkpoint' in reason for reason in refused[0]['reasons'])
    assert all(r['accepted'] for r in rows if r is not refused[0])
    assert {'stage', 'treatment_id', 'algorithm', 'scenario', 'seed', 'attempt_id'} <= set(rows[0])


@pytest.mark.parametrize('workers', [1, 2])
def test_evaluate_skips_existing_and_reports(campaign, workers):
    first = pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT,
                                    evaluate=synthetic_evaluate, workers=workers)
    assert len(first['evaluated']) == 4 and first['existing'] == [] and first['failed'] == []
    second = pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT,
                                     evaluate=synthetic_evaluate, workers=workers)
    assert second['evaluated'] == [] and len(second['existing']) == 4 and second['failed'] == []


def test_evaluate_reports_refusals_without_writing(campaign):
    # The real evaluator refuses these synthetic, unloadable models; the pipeline reports
    # each refusal as data and writes no evaluation.
    result = pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split='test_2025')
    assert result['evaluated'] == [] and len(result['failed']) == 4
    assert all(item['reason'] for item in result['failed'])
    assert not any(campaign.parent.rglob('kpi_report.json'))


def test_analyze_writes_hashed_report_and_refuses_overwrite(campaign):
    pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT, evaluate=synthetic_evaluate)
    protocol = dataclasses.replace(fa.FrozenProtocol.default(), seeds=(901,))
    folder = pipeline.analyze_stage(campaign, stage='pilot', split=SPLIT, protocol=protocol)
    assert folder == campaign.parent/'analysis'/f'pilot_{SPLIT}'
    names = {'seed_table.json', 'scientific_report.json'}
    recorded = json.loads((folder/'analysis_manifest.json').read_text(encoding='utf-8'))['files']
    assert set(recorded) == names
    for name in names:
        assert recorded[name] == hashlib.sha256((folder/name).read_bytes()).hexdigest()
    assert json.loads((folder/'seed_table.json').read_text(encoding='utf-8'))['rows']
    with pytest.raises(FileExistsError):
        pipeline.analyze_stage(campaign, stage='pilot', split=SPLIT, protocol=protocol)


def test_pipeline_never_trains():
    source = Path(pipeline.__file__).read_text(encoding='utf-8')
    tree = ast.parse(source)
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not any('native_entrypoint' in name or name == 'subprocess' for name in imported)
    called = {node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
              for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert 'run_stage' not in called and 'create_attempt' not in called


def test_main_prints_json_and_exit_codes(campaign, tmp_path, capsys):
    assert pipeline.main(['status', '--manifest', str(campaign)]) == 0
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report['status'] == 'ok' and len(report['treatments']) == 4
    assert pipeline.main(['status', '--manifest', str(tmp_path/'missing.json')]) == 2
    refused = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert refused['status'] == 'refused' and refused['reason']


def test_freeze_without_hpo_results_is_blocked_not_hidden(campaign, capsys):
    code = pipeline.main(['freeze', '--manifest', str(campaign), '--config', str(CONFIG)])
    assert code == 2
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report['status'] == 'refused' and 'blocked' in report
    assert set(report['blocked']) == {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
    assert not (campaign.parent/fc.FREEZES_FILE).exists()
