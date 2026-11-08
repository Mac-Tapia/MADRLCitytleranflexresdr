"""Pure acceptance-composition test with newly generated synthetic evidence.

No learner, simulator, historical model or measured scientific result is used.
This proves the gate can accept a complete contract and reject a changed one;
the four real learners are verified separately by test_real_learning.py.
"""
import hashlib
import json
import subprocess
import uuid
from pathlib import Path
import yaml

from tests.fresh_training.test_attempt_acceptance import _stage_learner
from tests.fresh_training.test_pipeline import synthetic_evaluate
from tools.eval import build_campaign_statistical_report as report_tool
from uc3m.application import pipeline
from uc3m.application.evaluation import fresh_analysis as fa
from uc3m.application.evaluation.analysis_acceptance import verify_scientific_analysis
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'


def _physical_contract_evaluate(attempt_root, split_id, campaign_root, **kwargs):
    report = synthetic_evaluate(attempt_root, split_id, campaign_root, **kwargs)
    folder = Path(attempt_root)/'evaluation'/split_id
    report.update(trace_hash='a'*64, baseline_trace_hash='b'*64,
                  balance_checks={'energy': {'passed': True}})
    scenario = report['context']['scenario']
    report['comparable_kpi_gains'] = [{'name': name, 'gain': None if name == 'price_signal_deviation' else 0.1,
                                      'available': name != 'price_signal_deviation'}
                                     for _, (scen, kpis) in fa.comparable_kpis().items()
                                     if scen == scenario for name in kpis]
    (folder/'kpi_report.json').write_text(json.dumps(report), encoding='utf-8')
    rows = {'validation_2024': 8784, 'test_2025': 8760}[split_id]
    runs = {name: {'split': split_id, 'trace_hash': digest*64, 'completed_steps': rows,
                   'training_updates': 0} for name, digest in [('control', 'a'), ('baseline', 'b')]}
    (folder/'frozen_runs.json').write_text(json.dumps(runs), encoding='utf-8')
    (folder/'evaluation_manifest.json').write_text(json.dumps({'schema_version': 2, 'split': split_id,
        'expected_full_split_rows': rows, 'files': {name: hashlib.sha256((folder/name).read_bytes()).hexdigest()
                                                  for name in ('kpi_report.json', 'frozen_runs.json')}}), encoding='utf-8')


def test_hpo_candidates_remain_distinct_then_complete_test_analysis_reloads(tmp_path):
    subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File',
                    'scripts/verify_project_context.ps1'], cwd=REPO, check=True)
    owned = REPO/'.superpowers/sdd/remediacion_integrada'/('contract_' + uuid.uuid4().hex)
    owned.mkdir()
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    config['campaign_id'] = 'fresh_synthetic_contract_20261101_v1'
    config['seeds']['development'] = [901]
    algorithms = yaml.safe_load((REPO/config['algorithm_config']).read_text(encoding='utf-8'))
    algorithms['hyperparameter_grid'] = {'learning_rate': [0.0001], 'hidden_dimension': [128],
                                        'gamma': [0.99, 0.9999]}
    algorithm_path = owned/'algorithms.yaml'
    algorithm_path.write_text(yaml.safe_dump(algorithms), encoding='utf-8')
    config['algorithm_config'] = algorithm_path.relative_to(REPO).as_posix()
    config_path = owned/'config.yaml'
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')
    fc.prepare_campaign(config_path, REPO, artifact_root=tmp_path/'campaign')
    manifest = tmp_path/'campaign/campaign_manifest.json'
    learner = _stage_learner(fc.load_algorithm_config(algorithm_path), 17)
    assert fc.run_stage(manifest, 'hpo', learner, REPO, authorized=True)['status'] == 'training_complete'
    evaluated = pipeline.evaluate_stage(manifest, stage='hpo', split='validation_2024',
                                        evaluate=_physical_contract_evaluate)
    assert len(evaluated['evaluated']) == 24 and not evaluated['failed']
    # Two configurations share one development seed in this bounded contract
    # fixture. Production still has eight configurations x three seeds.
    selected = pipeline.freeze_hpo(manifest, config_path)
    assert selected['status'] == 'ok' and (manifest.parent/'test_unlock.json').is_file()
    assert fc.run_stage(manifest, 'confirm', learner, REPO, authorized=True)['status'] == 'training_complete'
    # The test split stays closed until the candidate is chosen on validation.
    assert pipeline.main(['evaluate', '--manifest', str(manifest), '--split', 'test_2025']) == 2
    evaluated = pipeline.evaluate_stage(manifest, stage='confirm', split='validation_2024',
                                        evaluate=_physical_contract_evaluate)
    assert len(evaluated['evaluated']) == 144 and not evaluated['failed']
    pipeline.analyze_stage(manifest, stage='confirm', split='validation_2024')
    assert pipeline.select_model(manifest, stage='confirm', split='validation_2024')
    evaluated = pipeline.evaluate_stage(manifest, stage='confirm', split='test_2025',
                                        evaluate=_physical_contract_evaluate)
    assert len(evaluated['evaluated']) == 144 and not evaluated['failed']
    folder = pipeline.analyze_stage(manifest, stage='confirm', split='test_2025')
    assert verify_scientific_analysis(manifest, analysis_manifest=folder/'analysis_manifest.json')
    # D6: the single report tool reads this same analysis, with the 144 confirmatory attempts.
    arguments = ['--manifest', str(manifest), '--stage', 'confirm', '--split', 'test_2025']
    assert report_tool.main(arguments + ['--output-dir', str(tmp_path/'report')]) == 0
    written = json.loads((tmp_path/'report'/report_tool.REPORT_JSON).read_text(encoding='utf-8'))
    assert written['status'] == 'scientifically_complete' and written['scientific_acceptance'] is False
    assert written['excluded_attempts'] == [] and len(written['treatments']) == 4*len(written['comparisons'])
    assert pipeline.main(['select', *arguments]) == 2      # the candidate is never chosen on the test split
    changed = next(manifest.parent.glob('confirm/**/evaluation/test_2025/frozen_runs.json'))
    changed.write_text('{}', encoding='utf-8')
    assert not verify_scientific_analysis(manifest)
    assert report_tool.main(arguments + ['--output-dir', str(tmp_path/'refused')]) == 2
    assert not (tmp_path/'refused').exists()
