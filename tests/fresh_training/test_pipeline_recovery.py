"""I08: failures stop the CLI and interrupted analysis can be retried safely."""
import dataclasses
import hashlib
import json

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


def test_delivery_receives_the_explicit_gate_and_analysis(campaign, tmp_path):
    pipeline.evaluate_stage(campaign, project_root=REPO, stage='pilot', split=SPLIT, evaluate=synthetic_evaluate)
    folder = pipeline.analyze_stage(campaign, stage='pilot', split=SPLIT,
                                    protocol=dataclasses.replace(FrozenProtocol.default(), seeds=(901,)))
    result = pipeline.deliver(campaign, tmp_path/'delivery', stage='pilot', split=SPLIT,
                              gate_report=_gate(tmp_path, campaign), analysis_manifest=folder/'analysis_manifest.json')
    assert result['acceptance']['software_acceptance'] is True
    assert result['acceptance']['scientific_acceptance'] is False
