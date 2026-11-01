"""Resume only matching scientific identities and byte-verified checkpoints."""
from dataclasses import dataclass
from pathlib import Path

from uc3m.domain.evidence import EvidenceManifest
from uc3m.domain.experiments import ExperimentSpec


@dataclass(frozen=True)
class ResumePlan:
    allowed: bool
    start_episode: int
    checkpoint_paths: tuple
    reason: str


def plan_resume(spec: ExperimentSpec, manifest: EvidenceManifest, run_root: Path) -> ResumePlan:
    if manifest.identity.experiment_fingerprint != spec.fingerprint():
        return ResumePlan(False, 0, (), 'experiment_fingerprint_mismatch')
    if not manifest.verify_files(run_root):
        return ResumePlan(False, 0, (), 'artifact_verification_failed')
    checkpoints = tuple(item.relative_path for item in manifest.artifacts if item.kind == 'checkpoint')
    if not checkpoints:
        return ResumePlan(False, 0, (), 'checkpoint_missing')
    if manifest.target_episodes != spec.target_episodes:
        return ResumePlan(False, 0, (), 'target_mismatch')
    has_training_state = any(item.kind == 'training_state' for item in manifest.artifacts)
    if not has_training_state:
        return ResumePlan(False, 0, (), 'training_state_missing')
    return ResumePlan(True, manifest.completed_episodes, checkpoints, 'verified_checkpoint')
