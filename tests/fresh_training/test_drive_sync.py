"""Incremental Drive persistence and restore of finished attempts (owner 2026-11-01).

«el entrenamiento [local] es parcial y microentrenamiento; el entrenamiento largo se va
a almacenar en Drive». Finished attempts (completion.json) are copied as soon as they
finish, verified by digest, never while in progress; a new session restores them with
the campaign registry before relaunching, so run_stage reuses the verified attempt and
repeats from zero only what was not finished.
"""
import json
import shutil
from pathlib import Path

import pytest

from uc3m.application.training import drive_sync as ds
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'


def _attempt(root, name, *, finished=True, complete=True):
    path = root/'pilot'/name
    path.mkdir(parents=True)
    (path/'attempt.json').write_text('{}', encoding='utf-8')
    (path/'native.bin').write_bytes(b'weights-' + name.encode())
    if finished:
        (path/'completion.json').write_text(json.dumps({'training_complete': complete}), encoding='utf-8')
    return path


def test_only_finished_attempts_are_copied_verified_and_never_overwritten(tmp_path):
    local, drive = tmp_path/'local', tmp_path/'drive'
    _attempt(local, 'try_01')
    _attempt(local, 'try_02', finished=False)                      # in progress
    (local/'campaign_manifest.json').parent.mkdir(parents=True, exist_ok=True)
    (local/'campaign_manifest.json').write_text('{"campaign_id": "x"}', encoding='utf-8')
    (local/'treatments.json').write_text('{}', encoding='utf-8')
    first = ds.sync_finished_attempts(local, drive)
    assert first['copied'] == ['pilot/try_01'] and (drive/'pilot/try_01/native.bin').is_file()
    assert not (drive/'pilot/try_02').exists()
    assert {'campaign_manifest.json', 'treatments.json'} <= set(first['files'])
    assert ds.sync_finished_attempts(local, drive)['already_synced'] == ['pilot/try_01']
    (local/'pilot/try_01/native.bin').write_bytes(b'changed later')
    assert ds.sync_finished_attempts(local, drive)['conflicts'] == ['pilot/try_01']
    assert (drive/'pilot/try_01/native.bin').read_bytes() == b'weights-try_01'


def test_restore_verifies_digest_and_trust(tmp_path):
    local, drive, fresh = tmp_path/'local', tmp_path/'drive', tmp_path/'fresh'
    _attempt(local, 'try_01')
    _attempt(local, 'try_02', complete=False)
    _attempt(local, 'try_03')
    ds.sync_finished_attempts(local, drive)
    (drive/'pilot/try_03/native.bin').write_bytes(b'tampered on drive')
    report = ds.restore_finished_attempts(drive, fresh, 'fresh_x_v1',
                                          trust=lambda artifacts, campaign, attempt: [])
    assert report['restored_complete'] == ['pilot/try_01'] and report['restored_failed'] == ['pilot/try_02']
    assert report['rejected'] == {'pilot/try_03': ['drive_copy_digest_mismatch']}
    untrusted = ds.restore_finished_attempts(drive, tmp_path/'other', 'fresh_x_v1',
                                             trust=lambda artifacts, campaign, attempt: ['untrusted_checkpoint'])
    assert 'pilot/try_01' in untrusted['rejected'] and not (tmp_path/'other/pilot/try_01').exists()


def test_restore_then_relaunch_reuses_the_verified_attempt(tmp_path):
    from tests.fresh_training.test_campaign_contract import _learned
    campaign, drive = tmp_path/'campaign', tmp_path/'drive'
    fc.prepare_campaign(CONFIG, REPO, artifact_root=campaign)
    manifest_path = campaign/'campaign_manifest.json'
    calls = []

    def learner(treatment, attempt_root):
        calls.append(treatment['treatment_id'])
        return _learned(treatment, attempt_root)
    first = fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True)
    assert first['completed_treatments'] == 4 and len(calls) == 4
    synced = ds.sync_finished_attempts(campaign, drive)
    assert len(synced['copied']) == 4 and 'treatments.json' in synced['files']
    tries_before = sorted(p.parent.relative_to(campaign).as_posix() for p in campaign.rglob('attempt.json'))

    shutil.rmtree(campaign)                                       # the Colab session is lost
    manifest = json.loads((drive/'campaign_manifest.json').read_text(encoding='utf-8'))
    restored = ds.restore_finished_attempts(drive, campaign, manifest['campaign_id'])
    assert len(restored['restored_complete']) == 4 and not restored['rejected']
    calls.clear()
    second = fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True)
    assert calls == [] and second['completed_treatments'] == 4
    assert all(t['reused_verified_attempt'] for t in second['treatments'])
    tries_after = sorted(p.parent.relative_to(campaign).as_posix() for p in campaign.rglob('attempt.json'))
    assert tries_after == tries_before                             # no new attempt was created


def test_interrupted_attempt_is_never_restored_as_complete(tmp_path):
    from tests.fresh_training.test_campaign_contract import _learned
    campaign, drive = tmp_path/'campaign', tmp_path/'drive'
    fc.prepare_campaign(CONFIG, REPO, artifact_root=campaign)
    manifest_path = campaign/'campaign_manifest.json'
    interrupted = []

    def learner(treatment, attempt_root):
        if treatment['algorithm'] == 'MASAC' and not interrupted:
            interrupted.append(attempt_root)
            ds.sync_finished_attempts(campaign, drive)            # sync while MASAC is still running
            raise KeyboardInterrupt
        return _learned(treatment, attempt_root)
    with pytest.raises(KeyboardInterrupt):
        fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True)
    ds.sync_finished_attempts(campaign, drive)
    relative = interrupted[0].relative_to(campaign).as_posix()
    assert relative not in json.loads((drive/ds.MANIFEST).read_text(encoding='utf-8'))['attempts']
    shutil.rmtree(campaign)
    manifest = json.loads((drive/'campaign_manifest.json').read_text(encoding='utf-8'))
    ds.restore_finished_attempts(drive, campaign, manifest['campaign_id'])
    assert not (campaign/relative).exists()
    calls = []

    def relaunch(treatment, attempt_root):
        calls.append((treatment['algorithm'], attempt_root.name))
        return _learned(treatment, attempt_root)
    result = fc.run_stage(manifest_path, 'pilot', relaunch, REPO, authorized=True)
    # HAPPO finished before the interruption and is reused; MASAC (interrupted) and the
    # treatments that never started run from zero in new attempts.
    assert [algorithm for algorithm, _ in calls] == ['MASAC', 'MATD3', 'MAAC']
    assert result['completed_treatments'] == 4
    masac = [t for t in result['treatments'] if '/masac/' in t['treatment_id']][0]
    assert masac['reused_verified_attempt'] is False
