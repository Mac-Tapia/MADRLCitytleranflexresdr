import json
from pathlib import Path

from uc3m.application.configuration import load_scenario_catalog
from uc3m.domain.evidence import ArtifactRef
from uc3m.domain.experiments import ExperimentSpec


class DeterministicBackend:
    """Real file-producing integration backend, not a training acceptance substitute."""
    def execute(self, spec, run_root, resume):
        from uc3m.ports.learner import TrainingResult
        artifacts = []
        for name, kind in [('model.bin', 'checkpoint'), ('kpis.json', 'kpi'), ('summary.json', 'training_summary')]:
            path = run_root / name
            path.write_bytes(b'{"value":1}')
            artifacts.append(ArtifactRef.from_file(run_root, path, kind=kind, media_type='application/json', producer='integration'))
        return TrainingResult(0, spec.target_episodes, tuple(artifacts))


def test_runner_persists_verified_evidence_and_rejects_corruption(tmp_path):
    from uc3m.application.training.runner import ExperimentRunner
    root = Path(__file__).resolve().parents[2]
    spec = ExperimentSpec('HAPPO', load_scenario_catalog(root / 'configs/scenarios.yaml')['E1'], 0, 'a'*64, 'b'*40, {}, 2)
    runner = ExperimentRunner(tmp_path, DeterministicBackend())
    result = runner.run(spec)
    assert result.status.value == 'verified'
    run_root = tmp_path / result.identity.run_id
    assert json.loads((run_root / 'evidence.json').read_text())['status'] == 'verified'
    (run_root / 'model.bin').write_bytes(b'corrupt')
    try:
        runner.run(spec, resume=True)
    except ValueError as exc:
        assert 'artifact_verification_failed' in str(exc)
    else:
        raise AssertionError('corrupted checkpoint was accepted')


def test_runner_recovers_durable_checkpoint_after_backend_exception(tmp_path):
    from uc3m.application.training.runner import ExperimentRunner, read_manifest
    from uc3m.ports.learner import TrainingResult
    root = Path(__file__).resolve().parents[2]
    spec = ExperimentSpec('HAPPO', load_scenario_catalog(root/'configs/scenarios.yaml')['E1'], 0, 'a'*64, 'b'*40, {}, 2)
    class InterruptedBackend:
        def execute(self, spec, run_root, resume):
            (run_root/'model.pt').write_bytes(b'durable-weights')
            raise RuntimeError('interruption')
        def recover(self, spec, run_root):
            artifact = ArtifactRef.from_file(run_root, run_root/'model.pt', kind='checkpoint',
                        media_type='application/octet-stream', producer='integration')
            return TrainingResult(1, 1, (artifact,))
    runner = ExperimentRunner(tmp_path, InterruptedBackend())
    import pytest
    with pytest.raises(RuntimeError, match='interruption'):
        runner.run(spec)
    from uc3m.domain.experiments import RunIdentity
    run_root = tmp_path/RunIdentity.from_spec(spec).run_id
    recovered = read_manifest(run_root/'evidence.json')
    assert recovered.completed_episodes == 1
    assert recovered.verify_files(run_root)
