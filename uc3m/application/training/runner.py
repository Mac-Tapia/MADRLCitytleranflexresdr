"""Transactional orchestration independent of native training libraries."""
import json
from pathlib import Path

from uc3m.application.training.completion import evaluate_completion
from uc3m.application.training.persistence import write_json_atomic
from uc3m.application.training.resume import plan_resume
from uc3m.application.training.lock import run_lock
from uc3m.application.training.layout import experiment_path
from uc3m.domain.evidence import ArtifactRef, EvidenceManifest
from uc3m.domain.experiments import ExperimentSpec, RunIdentity, RunStatus
from uc3m.ports.learner import LearnerPort


def read_manifest(path: Path) -> EvidenceManifest:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return EvidenceManifest(
        RunIdentity(payload['run_id'], payload['experiment_fingerprint']),
        RunStatus(payload['status']), payload['completed_episodes'], payload['target_episodes'],
        tuple(ArtifactRef(**item) for item in payload['artifacts']),
    )


class ExperimentRunner:
    def __init__(self, output_root: Path, learner: LearnerPort, *, run_root=None):
        self.output_root = Path(output_root).resolve()
        self.learner = learner
        self.run_root = Path(run_root).resolve() if run_root is not None else None
        if self.run_root is not None:
            self.run_root.relative_to(self.output_root)

    def run(self, spec: ExperimentSpec, *, resume: bool = False) -> EvidenceManifest:
        identity = RunIdentity.from_spec(spec)
        root = self.run_root or experiment_path(self.output_root, spec)
        root.mkdir(parents=True, exist_ok=True)
        # A concurrent process may not mutate the same experiment directory.
        lock = run_lock(root / '.runner.lock')
        lock.__enter__()
        try:
            path = root / 'evidence.json'
            previous = None
            if path.exists():
                previous = read_manifest(path)
                if not resume:
                    raise ValueError('existing_run_requires_resume')
                if ((not previous.artifacts or previous.status is RunStatus.RUNNING)
                        and hasattr(self.learner, 'recover')
                        and previous.identity.experiment_fingerprint == spec.fingerprint()):
                    recovered = self.learner.recover(spec, root)
                    previous = EvidenceManifest(identity, RunStatus.PARTIAL,
                        recovered.completed_episodes, spec.target_episodes, recovered.artifacts)
                decision = plan_resume(spec, previous, root)
                if not decision.allowed:
                    raise ValueError(decision.reason)
                if previous.status is RunStatus.VERIFIED:
                    return previous
            elif resume:
                raise ValueError('resume_manifest_missing')
            write_json_atomic(root / 'experiment.json', spec.as_dict())
            running = EvidenceManifest(identity, RunStatus.RUNNING,
                previous.completed_episodes if previous else 0, spec.target_episodes,
                previous.artifacts if previous else ())
            write_json_atomic(path, running.as_dict())
            try:
                result = self.learner.execute(spec, root, resume)
                partial = EvidenceManifest(identity, RunStatus.PARTIAL,
                    result.completed_episodes, spec.target_episodes, result.artifacts)
                completion = evaluate_completion(spec, partial,
                    {'return_code': result.return_code, 'run_root': root})
                final = EvidenceManifest(identity, completion.status,
                    partial.completed_episodes, spec.target_episodes, partial.artifacts)
                write_json_atomic(root / 'completion.json',
                                  {'status': completion.status.value, 'reasons': completion.reasons})
                write_json_atomic(path, final.as_dict())
                return final
            except BaseException as exc:
                artifacts = running.artifacts
                completed = running.completed_episodes
                if hasattr(self.learner, 'recover'):
                    try:
                        recovered = self.learner.recover(spec, root)
                        artifacts, completed = recovered.artifacts, recovered.completed_episodes
                    except Exception:
                        # Do not hide the original backend failure on recovery error.
                        pass
                failed = EvidenceManifest(identity, RunStatus.PARTIAL,
                    completed, spec.target_episodes, artifacts)
                write_json_atomic(path, failed.as_dict())
                write_json_atomic(root / 'failure.json', {'error': str(exc), 'type': type(exc).__name__})
                raise
        finally:
            lock.__exit__(None, None, None)
