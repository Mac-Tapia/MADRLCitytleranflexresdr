"""R010 packaging only: real temporary FS, injected non-scientific acceptance."""
import hashlib
import json

import pytest

from uc3m.application.evaluation import fresh_delivery as delivery
from uc3m.application.training.fresh_acceptance import AcceptanceReport
from uc3m.domain.campaigns import canonical_hash


def dump(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')


def fixture_bundle(tmp_path, monkeypatch):
    root = tmp_path/'campaign'
    manifest_path = root/'campaign_manifest.json'
    policy = {'retired_roots': ['retired_fixture_outputs/']}
    identity = {'input_policy_sha256': canonical_hash(policy)}
    analysis_path = root/'reports'/'confirm_test'/'analysis_manifest.json'
    table = analysis_path.parent/'seed_table.json'
    report = analysis_path.parent/'scientific_report.json'
    dump(table, {'campaign_id': 'fresh_fixture_v1', 'rows': [], 'fixture_only': True})
    dump(report, {'campaign_id': 'fresh_fixture_v1', 'status': 'fixture_not_scientific',
                  'decisions': {'scientifically_complete': False}})
    analysis = {'campaign_id': 'fresh_fixture_v1', 'spec_hash': canonical_hash(identity),
                'stage': 'confirm', 'split': 'test_2025',
                'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (table, report)}}
    dump(analysis_path, analysis)
    manifest = {'schema_version': 1, 'campaign_id': 'fresh_fixture_v1', 'identity': identity,
                'spec_hash': canonical_hash(identity), 'input_policy': policy, 'stages': {},
                'analyses': {'confirm:test_2025': {'path': analysis_path.relative_to(root).as_posix(),
                                                'sha256': hashlib.sha256(analysis_path.read_bytes()).hexdigest()}}}
    dump(manifest_path, manifest)
    dump(root/'campaign.json', {'campaign_id': 'fresh_fixture_v1', 'spec_hash': manifest['spec_hash']})
    def packaging_acceptance(*args, **kwargs):
        return AcceptanceReport('fresh_fixture_v1', 'not_ready_no_model', True, False,
                                {'packaging_fixture_only': True}, ('no_scientific_evidence_in_fixture',))
    monkeypatch.setattr(delivery, 'verify_fresh_acceptance', packaging_acceptance)
    return manifest_path, analysis_path, table, report


@pytest.mark.parametrize('entrypoint', ['api', 'cli', 'relative_cli', 'explicit'])
def test_registered_analysis_is_packaged_by_all_entrypoints(tmp_path, monkeypatch, entrypoint):
    manifest, analysis, table, report = fixture_bundle(tmp_path, monkeypatch)
    destination = tmp_path/'delivery'
    if entrypoint in ('cli', 'relative_cli'):
        if entrypoint == 'relative_cli':
            monkeypatch.chdir(tmp_path)
            arguments = ['--manifest', 'campaign/campaign_manifest.json', '--destination', 'delivery']
        else:
            arguments = ['--manifest', str(manifest), '--destination', str(destination)]
        assert delivery.main(arguments) == 0
        result = json.loads((destination/delivery.DELIVERY_FILE).read_text())
    else:
        result = delivery.build_fresh_delivery(manifest, destination,
                                               **({'analysis_manifest': analysis} if entrypoint == 'explicit' else {}))
    assert result['acceptance']['scientific_acceptance'] is False
    assert result['state'] != 'new_campaign_scientifically_complete'
    paths = {row['path'] for row in result['files']}
    for source in (analysis, table, report):
        relative = source.relative_to(manifest.parent)
        assert relative.as_posix() in paths
        assert (destination/relative).read_bytes() == source.read_bytes()
    assert delivery.verify_delivery(destination).accepted


@pytest.mark.parametrize('defect', ['missing_artifact', 'altered_artifact', 'incomplete_registry',
                                   'altered_analysis', 'missing_analysis', 'null_registration'])
def test_registered_analysis_defects_reject_before_staging(tmp_path, monkeypatch, defect):
    manifest, analysis, table, report = fixture_bundle(tmp_path, monkeypatch)
    if defect == 'missing_artifact':
        table.unlink()
    elif defect == 'altered_artifact':
        report.write_text('{}', encoding='utf-8')
    elif defect == 'incomplete_registry':
        payload = json.loads(analysis.read_text())
        payload['files'].pop('seed_table.json')
        dump(analysis, payload)
        registered = json.loads(manifest.read_text())
        registered['analyses']['confirm:test_2025']['sha256'] = hashlib.sha256(analysis.read_bytes()).hexdigest()
        dump(manifest, registered)
    elif defect == 'altered_analysis':
        analysis.write_text(analysis.read_text() + ' ', encoding='utf-8')
    elif defect == 'null_registration':
        registered = json.loads(manifest.read_text())
        registered['analyses']['confirm:test_2025'] = None
        dump(manifest, registered)
    else:
        analysis.unlink()
    with pytest.raises((ValueError, PermissionError, FileNotFoundError)):
        delivery.build_fresh_delivery(manifest, tmp_path/'delivery')
    assert not (tmp_path/'delivery').exists()
    assert not list(tmp_path.glob('delivery.partial_*'))


def test_prepared_delivery_without_analysis_registry_remains_possible(tmp_path, monkeypatch):
    manifest, _, _, _ = fixture_bundle(tmp_path, monkeypatch)
    prepared = json.loads(manifest.read_text())
    prepared.pop('analyses')
    dump(manifest, prepared)
    result = delivery.build_fresh_delivery(manifest, tmp_path/'delivery')
    assert result['state'] == 'implementation_ready_for_training'
    assert result['acceptance']['scientific_acceptance'] is False


def test_explicit_hpo_analysis_without_confirm_registry_survives_nonempty_stages(tmp_path, monkeypatch):
    manifest, analysis, table, report = fixture_bundle(tmp_path, monkeypatch)
    payload = json.loads(manifest.read_text())
    payload.pop('analyses')
    payload['stages'] = {'hpo': {'path': 'stages/hpo_plan.json'}}
    dump(manifest, payload)
    dump(manifest.parent/'stages/hpo_plan.json', {'stage': 'hpo', 'fixture_only': True})
    hpo_analysis = json.loads(analysis.read_text())
    hpo_analysis.update(stage='hpo', split='validation_2024')
    dump(analysis, hpo_analysis)
    destination = tmp_path/'hpo_delivery'
    result = delivery.build_fresh_delivery(manifest, destination, analysis_manifest=analysis)
    assert result['acceptance']['scientific_acceptance'] is False
    assert result['state'] != 'new_campaign_scientifically_complete'
    for source in (analysis, table, report):
        assert (destination/source.relative_to(manifest.parent)).read_bytes() == source.read_bytes()
    assert delivery.verify_delivery(destination).accepted


def test_packaged_analysis_tampering_fails_readback(tmp_path, monkeypatch):
    manifest, analysis, table, _ = fixture_bundle(tmp_path, monkeypatch)
    destination = tmp_path/'delivery'
    delivery.build_fresh_delivery(manifest, destination, analysis_manifest=analysis)
    delivered_table = destination/table.relative_to(manifest.parent)
    delivered_table.write_text('{}', encoding='utf-8')
    check = delivery.verify_delivery(destination)
    assert not check.accepted
    assert any(reason.startswith('hash_mismatch:') for reason in check.reasons)
