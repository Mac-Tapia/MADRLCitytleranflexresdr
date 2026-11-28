"""Phase 2 audit reads the configured fresh campaign, not the retired smoke folder."""
import json
from pathlib import Path

import pytest

from tools.ops import audit_modular_training as amt
from uc3m.application.evaluation import results_catalog
from uc3m.application.evaluation.results_catalog import FreshAttempt

ROOT = Path(__file__).resolve().parents[2]


def _manifest(tmp_path, stages):
    path = tmp_path/'campaign_manifest.json'
    path.write_text(json.dumps({'campaign_id': 'fresh_test', 'stages': {
        stage: {'treatments': count} for stage, count in stages.items()}}), encoding='utf-8')
    return path


def _attempt(stage, algorithm, accepted=True, n=0):
    return FreshAttempt('fresh_test', stage, f'{stage}/{algorithm}/{n}', algorithm, 'E1', 901, 'a1',
                        Path('.'), accepted, () if accepted else ('not_complete',),
                        planned_treatment_id=f'{stage}/{algorithm.lower()}/{n}')


@pytest.fixture
def foundation_ready(monkeypatch):
    monkeypatch.setattr(amt, '_foundation_ready', lambda root: True)


def test_default_manifest_is_the_storage_alias_of_the_campaign_config():
    path = amt.campaign_manifest_path(ROOT, amt.CONFIG)
    import yaml
    alias = yaml.safe_load((ROOT/amt.CONFIG).read_text(encoding='utf-8'))['storage_alias']
    assert path == ROOT/'outputs/campaigns'/alias/'campaign_manifest.json'


def test_four_accepted_pilot_algorithms_pass_and_pending_is_computed(tmp_path, monkeypatch, foundation_ready):
    manifest = _manifest(tmp_path, {'pilot': 4, 'hpo': 2, 'confirm': 1, 'sensitivity': 1})
    found = [_attempt('pilot', a) for a in sorted(amt.ALGORITHMS)]
    found += [_attempt('hpo', 'HAPPO', n=0), _attempt('hpo', 'HAPPO', n=1), _attempt('confirm', 'MAAC')]
    monkeypatch.setattr(results_catalog, 'discover_attempts', lambda path, accepted_only: found)
    report = amt.audit_campaign(manifest, project_root=tmp_path)
    assert report['four_algorithm_smoke_verified'] is True
    assert report['status'] == 'pilot_verified'
    assert report['stages']['hpo'] == {'planned_treatments': 2, 'accepted_treatments': 2}
    assert report['pending'] == ['stage_sensitivity', 'scientific_acceptance']
    assert report['scientific_acceptance'] is False


def test_rejected_or_missing_pilot_algorithm_keeps_the_gate_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(amt, '_foundation_ready', lambda root: False)
    manifest = _manifest(tmp_path, {'pilot': 4})
    found = [_attempt('pilot', 'HAPPO'), _attempt('pilot', 'MASAC'), _attempt('pilot', 'MATD3'),
             _attempt('pilot', 'MAAC', accepted=False)]
    monkeypatch.setattr(results_catalog, 'discover_attempts', lambda path, accepted_only: found)
    report = amt.audit_campaign(manifest, project_root=tmp_path)
    assert report['four_algorithm_smoke_verified'] is False
    assert report['pending'][:2] == ['pilot_four_algorithms', 'open_source_provenance_gate']
    assert {'stage_hpo', 'stage_confirm', 'stage_sensitivity'} <= set(report['pending'])
    assert [row['reasons'] for row in report['runs'] if row['status'] == 'rejected'] == [['not_complete']]


def test_unprepared_campaign_is_reported_not_raised(tmp_path, foundation_ready):
    report = amt.audit_campaign(tmp_path/'missing.json', project_root=tmp_path)
    assert report['status'] == 'campaign_not_prepared'
    assert report['pending'][0] == 'campaign_prepare'


def test_main_writes_its_own_report_and_never_the_tracked_history(tmp_path, monkeypatch, foundation_ready):
    tracked = ROOT/'data/audits/modular_training_acceptance.json'
    before = tracked.read_bytes()
    manifest = _manifest(tmp_path, {'pilot': 4})
    monkeypatch.setattr(results_catalog, 'discover_attempts', lambda path, accepted_only: [])
    output = tmp_path/'report.json'
    assert amt.main(['--manifest', str(manifest), '--output', str(output)]) == 1
    assert json.loads(output.read_text(encoding='utf-8'))['status'] == 'pilot_pending'
    assert tracked.read_bytes() == before


def test_configured_campaign_audits_cleanly_before_the_pilot():
    """The real factura campaign is prepared: the audit reads it and only the pilot is missing."""
    manifest = amt.campaign_manifest_path(ROOT, amt.CONFIG)
    if not manifest.is_file():
        pytest.fail(f'configured campaign not prepared: {manifest}')
    report = amt.audit_campaign(manifest)
    assert report['campaign_id'].startswith('fresh_')
    assert report['stages']['pilot']['planned_treatments'] == 4
    if not report['four_algorithm_smoke_verified']:
        assert report['pending'][0] == 'pilot_four_algorithms'
