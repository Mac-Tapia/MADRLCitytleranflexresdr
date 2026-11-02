"""Read-only projections of persisted evidence for presentation clients."""
from pathlib import Path

from uc3m.application.training.runner import read_manifest
from uc3m.application.training.layout import iter_evidence_paths


def list_runs(output_root: Path):
    rows = []
    for path in sorted(iter_evidence_paths(output_root)):
        try:
            manifest = read_manifest(path)
            integrity = manifest.verify_files(path.parent)
            status = manifest.status.value
            if status == 'verified' and not integrity:
                status = 'artifact_verification_failed'
            rows.append({'run_id': manifest.identity.run_id, 'status': status,
                'completed_episodes': manifest.completed_episodes,
                'target_episodes': manifest.target_episodes,
                'artifacts_verified': integrity,
                'experiment_fingerprint': manifest.identity.experiment_fingerprint})
        except (ValueError, KeyError, TypeError, OSError):
            rows.append({'run_id': path.parent.name, 'status': 'invalid_manifest'})
    return rows
