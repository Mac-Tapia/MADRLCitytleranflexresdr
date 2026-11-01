"""Pure completion decisions; exit status alone never promotes a run."""
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from uc3m.domain.evidence import EvidenceManifest, REQUIRED_VERIFIED_KINDS
from uc3m.domain.experiments import ExperimentSpec, RunStatus


@dataclass(frozen=True)
class CompletionDecision:
    status: RunStatus
    reasons: Tuple[str, ...]


def evaluate_completion(spec: ExperimentSpec, manifest: Optional[EvidenceManifest],
                        discovered: Mapping[str, object]) -> CompletionDecision:
    reasons = []
    if discovered.get('return_code') != 0:
        reasons.append('backend_not_successful')
    if manifest is None:
        reasons.append('missing_manifest')
    else:
        if manifest.identity.experiment_fingerprint != spec.fingerprint():
            return CompletionDecision(RunStatus.BLOCKED, ('experiment_fingerprint_mismatch',))
        if manifest.completed_episodes != spec.target_episodes:
            reasons.append('episodes_incomplete')
        if manifest.target_episodes != spec.target_episodes:
            reasons.append('target_mismatch')
        if REQUIRED_VERIFIED_KINDS - {item.kind for item in manifest.artifacts}:
            reasons.append('missing_required_artifacts')
        root = discovered.get('run_root')
        if root is None or not manifest.verify_files(root):
            reasons.append('artifact_verification_failed')
    return CompletionDecision(RunStatus.PARTIAL if reasons else RunStatus.VERIFIED, tuple(reasons))
