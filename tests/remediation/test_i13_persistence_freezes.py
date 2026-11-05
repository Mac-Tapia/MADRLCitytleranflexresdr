"""R009: real atomic primitives and lock; failure injection never trains or loads models."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from uc3m.application.training import fresh_campaign as fc
from uc3m.application.training import persistence
from uc3m.application.training.lock import run_lock


HYPER = {'learning_rate': 0.001, 'hidden_dimension': 64, 'gamma': 0.99}


def campaign(tmp_path):
    root = tmp_path/'campaign'
    root.mkdir()
    path = root/'campaign_manifest.json'
    path.write_text(json.dumps({'campaign_id': 'fresh_fixture_v1',
                               'hpo_candidates_by_algorithm': {'MATD3': {'c1': HYPER}},
                               'preserved_marker': 'original'}), encoding='utf-8')
    freeze = fc.freeze_configuration('fresh_fixture_v1', 'MATD3', HYPER, ['a'*64],
                                     selection_rule='fixture_validation_rule', candidates=['c1'],
                                     reason='contract fixture, no scientific selection')
    return path, freeze


def interrupt_manifest_replace(manifest, monkeypatch):
    original = persistence.os.replace
    reached = []
    def interrupted(source, target):
        assert Path(source).resolve().is_relative_to(manifest.parent.resolve())
        assert Path(target).resolve().is_relative_to(manifest.parent.resolve())
        if Path(target) == manifest:
            reached.append(Path(target))
            raise OSError('injected manifest publication failure')
        return original(source, target)
    monkeypatch.setattr(persistence.os, 'replace', interrupted)
    return original, reached


def test_manifest_replace_failure_preserves_original_and_retry_repairs_orphan(tmp_path, monkeypatch):
    manifest, freeze = campaign(tmp_path)
    original_bytes = manifest.read_bytes()
    original_replace, reached = interrupt_manifest_replace(manifest, monkeypatch)
    with pytest.raises(OSError, match='injected manifest publication failure'):
        fc.write_configuration_freezes(manifest, [freeze])
    assert reached == [manifest]
    assert manifest.read_bytes() == original_bytes
    target = manifest.parent/fc.FREEZES_FILE
    frozen_bytes = target.read_bytes()
    frozen_digest = hashlib.sha256(frozen_bytes).hexdigest()
    monkeypatch.setattr(persistence.os, 'replace', original_replace)
    retry = replace(freeze, frozen_at='2030-01-01T00:00:00+00:00')
    record = fc.write_configuration_freezes(manifest, [retry])
    assert target.read_bytes() == frozen_bytes
    assert record['sha256'] == frozen_digest
    assert record['freeze_hashes']['MATD3'] == freeze.freeze_hash()
    assert fc.load_configuration_freezes(manifest.parent, json.loads(manifest.read_text()))['MATD3'] == freeze


def test_same_registered_freeze_is_idempotent_preserving_manifest_bytes(tmp_path):
    manifest, freeze = campaign(tmp_path)
    record = fc.write_configuration_freezes(manifest, [freeze])
    frozen_bytes = (manifest.parent/fc.FREEZES_FILE).read_bytes()
    manifest_bytes = manifest.read_bytes()
    assert fc.write_configuration_freezes(manifest, [replace(freeze, frozen_at='2031-01-01T00:00:00+00:00')]) == record
    assert manifest.read_bytes() == manifest_bytes
    assert (manifest.parent/fc.FREEZES_FILE).read_bytes() == frozen_bytes


@pytest.mark.parametrize('change', ['evidence', 'selection', 'reason', 'candidates'])
def test_different_orphan_cannot_be_resealed(tmp_path, monkeypatch, change):
    manifest, freeze = campaign(tmp_path)
    original_replace, _ = interrupt_manifest_replace(manifest, monkeypatch)
    with pytest.raises(OSError):
        fc.write_configuration_freezes(manifest, [freeze])
    target = manifest.parent/fc.FREEZES_FILE
    before_manifest, before_freeze = manifest.read_bytes(), target.read_bytes()
    monkeypatch.setattr(persistence.os, 'replace', original_replace)
    changes = {'evidence': {'validation_manifest_hashes': ('b'*64,)},
               'selection': {'selection_rule': 'different_rule'}, 'reason': {'reason': 'changed'},
               'candidates': {'candidates': ()}}
    with pytest.raises((FileExistsError, ValueError, PermissionError)):
        fc.write_configuration_freezes(manifest, [replace(freeze, **changes[change])])
    assert manifest.read_bytes() == before_manifest
    assert target.read_bytes() == before_freeze


def test_tampered_orphan_hash_is_rejected_and_preserved(tmp_path, monkeypatch):
    manifest, freeze = campaign(tmp_path)
    original_replace, _ = interrupt_manifest_replace(manifest, monkeypatch)
    with pytest.raises(OSError):
        fc.write_configuration_freezes(manifest, [freeze])
    target = manifest.parent/fc.FREEZES_FILE
    payload = json.loads(target.read_text())
    payload['freezes']['MATD3']['freeze_hash'] = '0'*64
    target.write_text(json.dumps(payload), encoding='utf-8')
    tampered = target.read_bytes()
    monkeypatch.setattr(persistence.os, 'replace', original_replace)
    with pytest.raises(PermissionError):
        fc.write_configuration_freezes(manifest, [freeze])
    assert target.read_bytes() == tampered
    assert 'configuration_freezes' not in json.loads(manifest.read_text())


def test_registered_digest_mismatch_is_not_repaired_by_overwrite(tmp_path):
    manifest, freeze = campaign(tmp_path)
    fc.write_configuration_freezes(manifest, [freeze])
    target = manifest.parent/fc.FREEZES_FILE
    target.write_text(target.read_text() + ' ', encoding='utf-8')
    before_manifest, before_freeze = manifest.read_bytes(), target.read_bytes()
    with pytest.raises(PermissionError):
        fc.write_configuration_freezes(manifest, [freeze])
    assert manifest.read_bytes() == before_manifest
    assert target.read_bytes() == before_freeze


def test_empty_freeze_input_is_rejected_before_publishing(tmp_path):
    manifest, _ = campaign(tmp_path)
    before = manifest.read_bytes()
    with pytest.raises(ValueError, match='nonempty|empty'):
        fc.write_configuration_freezes(manifest, [])
    assert manifest.read_bytes() == before
    assert not (manifest.parent/fc.FREEZES_FILE).exists()


def test_non_candidate_rejected_without_freeze(tmp_path):
    manifest, freeze = campaign(tmp_path)
    invalid_hyper = dict(HYPER, gamma=0.5)
    invalid = replace(freeze, hyperparameters=invalid_hyper,
                      config_hash=freeze.config_hash_for('MATD3', invalid_hyper))
    with pytest.raises(ValueError, match='candidate'):
        fc.write_configuration_freezes(manifest, [invalid])
    assert not (manifest.parent/fc.FREEZES_FILE).exists()


def test_active_freeze_lock_rejects_second_writer(tmp_path):
    manifest, freeze = campaign(tmp_path)
    before = manifest.read_bytes()
    with run_lock(manifest.parent/'.configuration_freezes.lock'):
        with pytest.raises(OSError):
            fc.write_configuration_freezes(manifest, [freeze])
    assert manifest.read_bytes() == before
    assert not (manifest.parent/fc.FREEZES_FILE).exists()


def test_freeze_replace_failure_preserves_manifest_and_leaves_no_partial_freeze(tmp_path, monkeypatch):
    manifest, freeze = campaign(tmp_path)
    before = manifest.read_bytes()
    original_replace = persistence.os.replace
    def interrupted(source, target):
        assert Path(source).resolve().is_relative_to(manifest.parent.resolve())
        assert Path(target).resolve().is_relative_to(manifest.parent.resolve())
        if Path(target).name == fc.FREEZES_FILE:
            raise OSError('injected freeze publication failure')
        return original_replace(source, target)
    monkeypatch.setattr(persistence.os, 'replace', interrupted)
    with pytest.raises(OSError, match='injected freeze publication failure'):
        fc.write_configuration_freezes(manifest, [freeze])
    assert manifest.read_bytes() == before
    assert not (manifest.parent/fc.FREEZES_FILE).exists()
    assert not list(manifest.parent.glob('*.tmp'))


def test_missing_registered_freeze_is_not_silently_recreated(tmp_path):
    manifest, freeze = campaign(tmp_path)
    fc.write_configuration_freezes(manifest, [freeze])
    original_manifest = manifest.read_bytes()
    target = manifest.parent/fc.FREEZES_FILE
    target.unlink()
    with pytest.raises(PermissionError, match='missing'):
        fc.write_configuration_freezes(manifest, [freeze])
    assert manifest.read_bytes() == original_manifest
    assert not target.exists()
