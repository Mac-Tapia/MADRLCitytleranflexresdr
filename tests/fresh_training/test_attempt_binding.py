"""I04/I06: validate the persisted plan ID and full attempt fingerprint coherently."""
import json

import pytest

from tests.fresh_training.test_security_and_acceptance import _campaign
from uc3m.application.training import attempt_trust as trust


def test_bound_attempt_reloads_its_own_plan_and_fingerprint(tmp_path):
    manifest = _campaign(tmp_path)
    root = next(manifest.parent.rglob('attempt.json')).parent
    context = trust.read_trusted_attempt(root, algorithm='MATD3')
    assert context.manifest_path == manifest
    assert context.resolved['treatment_id'] != context.record['treatment_id']
    assert context.record['seed'] == context.resolved['seed'] == 1001
    assert context.evidence['verified'] is True


def test_changed_resolved_attempt_is_rejected_before_loading_a_model(tmp_path):
    manifest = _campaign(tmp_path)
    path = next(manifest.parent.rglob('resolved_treatment.json'))
    value = json.loads(path.read_text(encoding='utf-8'))
    value['seed'] = 1002
    path.write_text(json.dumps(value), encoding='utf-8')
    with pytest.raises(PermissionError):
        trust.read_trusted_attempt(path.parent, algorithm='MATD3')
