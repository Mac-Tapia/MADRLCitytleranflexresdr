from pathlib import Path

import pytest

from uc3m.application.configuration import load_scenario_catalog
from uc3m.domain.experiments import ExperimentSpec


@pytest.fixture
def spec():
    root = Path(__file__).resolve().parents[4]
    return ExperimentSpec('HAPPO', load_scenario_catalog(root / 'configs/scenarios.yaml')['E1'],
                          0, 'a'*64, 'b'*40, {}, 2)


def test_exit_zero_without_artifacts_is_partial(spec):
    from uc3m.application.training.completion import evaluate_completion
    result = evaluate_completion(spec, None, {'return_code': 0, 'completed_episodes': 2})
    assert result.status.value == 'partial'
    assert 'missing_manifest' in result.reasons


def test_resume_rejects_policy_mismatch_and_corrupt_checkpoint(spec, tmp_path):
    from uc3m.application.training.resume import plan_resume
    from uc3m.domain.evidence import ArtifactRef, EvidenceManifest
    from uc3m.domain.experiments import RunIdentity, RunStatus
    path = tmp_path / 'model.pt'
    path.write_bytes(b'weights')
    artifact = ArtifactRef.from_file(tmp_path, path, kind='checkpoint', media_type='application/octet-stream', producer='test')
    manifest = EvidenceManifest(RunIdentity.from_spec(spec), RunStatus.PARTIAL, 1, 2, (artifact,))
    plan = plan_resume(spec, manifest, tmp_path)
    assert plan.allowed and plan.start_episode == 1
    path.write_bytes(b'corrupt')
    assert not plan_resume(spec, manifest, tmp_path).allowed
    wrong = EvidenceManifest(RunIdentity('other', 'c'*64), RunStatus.PARTIAL, 1, 2, (artifact,))
    assert plan_resume(spec, wrong, tmp_path).reason == 'experiment_fingerprint_mismatch'
