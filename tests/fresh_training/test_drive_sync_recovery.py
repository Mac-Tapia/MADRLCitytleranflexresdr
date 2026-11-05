"""I09: real local copying with interruption, malicious paths and strict restore."""
import hashlib
import json
import shutil

import pytest

from tests.fresh_training.test_security_and_acceptance import CAMPAIGN_ID, _campaign
from uc3m.application.training import drive_sync as ds


@pytest.mark.parametrize('relative', ['sub/../../outside.txt', '../outside.txt', 'C:/outside.txt'])
def test_restore_never_writes_a_manifest_path_outside_artifacts(tmp_path, relative):
    drive, target = tmp_path/'drive', tmp_path/'local'
    drive.mkdir()
    outside = tmp_path/'outside.txt'
    outside.write_bytes(b'original')
    (drive/ds.MANIFEST).write_text(json.dumps({'files': {relative: hashlib.sha256(b'original').hexdigest()},
                                               'attempts': {}}), encoding='utf-8')
    report = ds.restore_finished_attempts(drive, target, CAMPAIGN_ID)
    assert relative in report['conflicts'] or relative in report['rejected']
    assert outside.read_bytes() == b'original'


def test_restore_recovers_a_published_attempt_with_pending_manifest(tmp_path, monkeypatch):
    manifest_path = _campaign(tmp_path/'source')
    source, drive, target = manifest_path.parent, tmp_path/'drive', tmp_path/'restored'
    original = ds._write_manifest

    def disconnect_after_attempt_publish(root, manifest):
        if manifest.get('attempts'):
            raise KeyboardInterrupt('session lost after rename')
        return original(root, manifest)

    monkeypatch.setattr(ds, '_write_manifest', disconnect_after_attempt_publish)
    with pytest.raises(KeyboardInterrupt):
        ds.sync_finished_attempts(source, drive)
    monkeypatch.setattr(ds, '_write_manifest', original)
    shutil.rmtree(source)  # only this test's disposable source, as on loss of a runtime
    report = ds.restore_finished_attempts(drive, target, CAMPAIGN_ID)
    assert len(report['restored_complete']) == 1 and not report['rejected']
    state = json.loads((drive/ds.MANIFEST).read_text(encoding='utf-8'))
    assert len(state['attempts']) == 1 and not state.get('pending_attempts')


def test_sync_recovers_an_identical_orphan_and_rechecks_recorded_digest(tmp_path):
    manifest = _campaign(tmp_path/'source')
    source, drive = manifest.parent, tmp_path/'drive'
    attempt = next(source.rglob('attempt.json')).parent
    relative = attempt.relative_to(source)
    shutil.copytree(attempt, drive/relative)
    report = ds.sync_finished_attempts(source, drive)
    assert not report['conflicts']
    next((drive/relative).rglob('*.pt')).write_bytes(b'changed on drive')
    assert relative.as_posix() in ds.sync_finished_attempts(source, drive)['conflicts']


def test_conflicts_make_the_drive_cli_fail(tmp_path, capsys):
    source, drive = tmp_path/'source', tmp_path/'drive'
    source.mkdir()
    drive.mkdir()
    (source/'campaign_manifest.json').write_text('{"campaign_id":"fresh_one_v1"}', encoding='utf-8')
    (drive/'campaign_manifest.json').write_text('{"campaign_id":"fresh_other_v1"}', encoding='utf-8')
    assert ds.main(['--artifacts', str(source), '--drive', str(drive), '--sync']) == 2
    assert json.loads(capsys.readouterr().out)['conflicts']


def test_directory_digest_streams_and_preserves_its_existing_identity(tmp_path, monkeypatch):
    data = b'01234567'*(300000)
    (tmp_path/'weights.pt').write_bytes(data)
    expected = hashlib.sha256(b'weights.pt\0'+data+b'\0').hexdigest()
    from pathlib import Path
    original = Path.read_bytes

    def no_checkpoint_read_bytes(path):
        assert path.suffix != '.pt', 'checkpoint digest must stream'
        return original(path)

    monkeypatch.setattr(Path, 'read_bytes', no_checkpoint_read_bytes)
    assert ds.directory_digest(tmp_path) == expected


def test_present_attempt_is_not_reported_trusted_only_because_it_exists(tmp_path):
    manifest = _campaign(tmp_path/'source')
    evidence = next(manifest.parent.rglob('learning_evidence.json'))
    value = json.loads(evidence.read_text(encoding='utf-8'))
    value['verified'] = False
    evidence.write_text(json.dumps(value), encoding='utf-8')
    drive = tmp_path/'drive'
    ds.sync_finished_attempts(manifest.parent, drive)
    report = ds.restore_finished_attempts(drive, manifest.parent, CAMPAIGN_ID)
    assert report['rejected'] and not report['present']


def test_restore_does_not_touch_another_local_campaign(tmp_path):
    manifest = _campaign(tmp_path/'source')
    drive, target = tmp_path/'drive', tmp_path/'other'
    ds.sync_finished_attempts(manifest.parent, drive)
    target.mkdir()
    local = target/'campaign_manifest.json'
    local.write_text('{"campaign_id":"fresh_other_v1"}', encoding='utf-8')
    report = ds.restore_finished_attempts(drive, target, CAMPAIGN_ID)
    assert report['conflicts'] and list(target.iterdir()) == [local]


def test_evaluation_and_registered_analysis_append_without_copying_native_model_again(tmp_path, monkeypatch):
    manifest_path = _campaign(tmp_path/'source')
    source, drive, target = manifest_path.parent, tmp_path/'drive', tmp_path/'restored'
    attempt = next(source.rglob('attempt.json')).parent
    assert not ds.sync_finished_attempts(source, drive)['conflicts']
    folder = attempt/'evaluation/validation_2024'
    folder.mkdir(parents=True)
    (folder/'kpi_report.json').write_text('{"report":1}', encoding='utf-8')
    analysis = source/'analysis/confirm_validation_2024'
    analysis.mkdir(parents=True)
    (analysis/'seed_table.json').write_text('{"rows":[]}', encoding='utf-8')
    (analysis/'analysis_manifest.json').write_text('{"files":{}}', encoding='utf-8')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['analyses'] = {'confirm:validation_2024': {
        'path': 'analysis/confirm_validation_2024/analysis_manifest.json',
        'sha256': ds._file_digest(analysis/'analysis_manifest.json')}}
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    original = ds.shutil.copytree
    def no_second_training_copy(src, dst, *args, **kwargs):
        assert src != attempt, 'postprocessing must not recopy the native checkpoint'
        return original(src, dst, *args, **kwargs)
    monkeypatch.setattr(ds.shutil, 'copytree', no_second_training_copy)
    assert not ds.sync_finished_attempts(source, drive)['conflicts']
    report = ds.restore_finished_attempts(drive, target, CAMPAIGN_ID)
    assert len(report['restored_complete']) == 1 and not report['conflicts'] and not report['rejected']
    assert (target/folder.relative_to(source)/'kpi_report.json').read_text() == '{"report":1}'
    assert (target/analysis.relative_to(source)/'seed_table.json').is_file()
    next((drive/attempt.relative_to(source)).rglob('*.pt')).write_bytes(b'corrupt')
    assert ds.sync_finished_attempts(source, drive)['conflicts']
