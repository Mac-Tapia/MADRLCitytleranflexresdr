"""Hash-verified backup and restore of a verified training run (SPEC-008/FR-008.3).

Layout handled: ``<run_root>/{evidence.json, experiment.json, completion.json}``
plus every artifact indexed in ``evidence.json``. The destination is reached only
through the injected ``ArtifactStore`` port, whose root is the backup (or the
restored run) directory. Every step fails closed: nothing is written until the
whole source has been verified against ``evidence.json``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from uc3m.application.artifacts.retention import BackupVerificationError, RetentionPolicy
from uc3m.application.training.runner import read_manifest
from uc3m.domain.evidence import ArtifactRef, EvidenceManifest
from uc3m.domain.experiments import RunStatus
from uc3m.ports.artifact_store import ArtifactStore

BACKUP_MANIFEST = "backup_manifest.json"
BACKUP_SCHEMA = "uc3m.artifact_backup.v1"
EVIDENCE = "evidence.json"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _inside(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise BackupVerificationError(f"path escapes root: {relative_path}") from exc
    return path


def _experiment_fingerprint(payload: Mapping[str, object]) -> str:
    # Same serialization as ExperimentSpec.fingerprint().
    return _digest(json.dumps(payload, ensure_ascii=True, sort_keys=True,
                              separators=(",", ":")).encode("utf-8"))


def _load_evidence(path: Path) -> EvidenceManifest:
    try:
        return read_manifest(path)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise BackupVerificationError(f"invalid {path.name}: {exc}") from exc


def _write_checked(store: ArtifactStore, relative_path: str, payload: bytes, *,
                   kind: str, media_type: str, expected_sha256: str) -> ArtifactRef:
    written = store.write_bytes(relative_path, payload, kind=kind, media_type=media_type)
    if written.sha256 != expected_sha256 or written.size_bytes != len(payload):
        raise BackupVerificationError(f"store readback sha256 mismatch: {relative_path}")
    return written


def backup_run(run_root: Path, store: ArtifactStore, policy: RetentionPolicy) -> Dict[str, object]:
    """Copy a verified run into ``store`` and return the written backup manifest."""
    run_root = Path(run_root).resolve()
    evidence_path = run_root / EVIDENCE
    if not evidence_path.is_file():
        raise BackupVerificationError(f"missing {EVIDENCE} in {run_root}")
    evidence = _load_evidence(evidence_path)
    if evidence.status is not RunStatus.VERIFIED:
        raise BackupVerificationError(
            f"run {evidence.identity.run_id} is not verified (status={evidence.status.value})")
    if not evidence.verify_files(run_root):
        raise BackupVerificationError("source run fails hash verification against evidence.json")

    manifests: Dict[str, bytes] = {}
    for name in policy.run_manifests:
        path = run_root / name
        if not path.is_file():
            raise BackupVerificationError(f"missing run manifest {name}")
        manifests[name] = path.read_bytes()
    if EVIDENCE not in manifests:
        raise BackupVerificationError("policy run_manifests must include evidence.json")
    if "completion.json" in manifests:
        completion = json.loads(manifests["completion.json"].decode("utf-8"))
        if completion.get("status") != RunStatus.VERIFIED.value:
            raise BackupVerificationError("completion.json does not report verified")
    if "experiment.json" in manifests:
        experiment = json.loads(manifests["experiment.json"].decode("utf-8"))
        if _experiment_fingerprint(experiment) != evidence.identity.experiment_fingerprint:
            raise BackupVerificationError("experiment.json does not match evidence fingerprint")

    planned: List[Tuple[ArtifactRef, str]] = []
    for artifact in evidence.artifacts:
        artifact_class = policy.classify(artifact)
        if not artifact_class.backup:
            raise BackupVerificationError(
                f"class {artifact_class.name} is not backed up but {artifact.relative_path} "
                "is in evidence.json; restore could not reproduce its hash")
        planned.append((artifact, artifact_class.name))

    records = []
    for artifact, class_name in planned:
        payload = _inside(run_root, artifact.relative_path).read_bytes()
        if _digest(payload) != artifact.sha256:
            raise BackupVerificationError(f"sha256 changed during backup: {artifact.relative_path}")
        _write_checked(store, artifact.relative_path, payload, kind=artifact.kind,
                       media_type=artifact.media_type, expected_sha256=artifact.sha256)
        records.append({**artifact.as_dict(), "retention_class": class_name})
    manifest_hashes = {}
    for name, payload in manifests.items():
        digest = _digest(payload)
        _write_checked(store, name, payload, kind="manifest",
                       media_type="application/json", expected_sha256=digest)
        manifest_hashes[name] = digest

    record: Dict[str, object] = {
        "schema": BACKUP_SCHEMA,
        "policy_schema_version": policy.schema_version,
        "run_id": evidence.identity.run_id,
        "experiment_fingerprint": evidence.identity.experiment_fingerprint,
        "evidence_sha256": manifest_hashes[EVIDENCE],
        "run_manifests": manifest_hashes,
        "artifacts": records,
    }
    # Written last: its presence marks a complete backup.
    store.write_json(BACKUP_MANIFEST, record, kind="manifest")
    return record


@dataclass(frozen=True)
class RestoreReport:
    run_id: str
    experiment_fingerprint: str
    evidence_sha256: str
    restored: int
    paths: Tuple[str, ...]


def restore_run(backup_root: Path, store: ArtifactStore, *,
                expected_evidence_sha256: Optional[str] = None) -> RestoreReport:
    """Restore a backup into ``store`` only if every byte matches evidence.json.

    ``expected_evidence_sha256`` pins the evidence manifest to an independent
    record (for example a Git-versioned evidence.json); without it the trust
    anchor is the backup manifest itself.
    """
    backup_root = Path(backup_root).resolve()
    manifest_path = backup_root / BACKUP_MANIFEST
    if not manifest_path.is_file():
        raise BackupVerificationError(f"missing {BACKUP_MANIFEST} in {backup_root}")
    try:
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupVerificationError(f"invalid {BACKUP_MANIFEST}") from exc
    if record.get("schema") != BACKUP_SCHEMA:
        raise BackupVerificationError(f"unsupported backup schema {record.get('schema')!r}")
    manifest_hashes = record.get("run_manifests")
    if not isinstance(manifest_hashes, dict) or EVIDENCE not in manifest_hashes:
        raise BackupVerificationError("backup manifest does not record evidence.json")

    problems: List[str] = []
    manifests: Dict[str, bytes] = {}
    for name, digest in sorted(manifest_hashes.items()):
        path = _inside(backup_root, name)
        if not path.is_file():
            problems.append(f"missing {name}")
            continue
        payload = path.read_bytes()
        if _digest(payload) != digest:
            problems.append(f"sha256 mismatch {name}")
        manifests[name] = payload
    if problems:
        raise BackupVerificationError("; ".join(problems))
    evidence_sha = manifest_hashes[EVIDENCE]
    if expected_evidence_sha256 is not None and evidence_sha != expected_evidence_sha256.casefold():
        raise BackupVerificationError("evidence.json differs from the pinned evidence sha256")

    evidence = _load_evidence(backup_root / EVIDENCE)
    if evidence.status is not RunStatus.VERIFIED:
        raise BackupVerificationError("backed-up evidence.json is not verified")
    if (record.get("run_id") != evidence.identity.run_id
            or record.get("experiment_fingerprint") != evidence.identity.experiment_fingerprint):
        raise BackupVerificationError("backup manifest identity differs from evidence.json")
    recorded = {(item.get("relative_path"), item.get("sha256"))
                for item in record.get("artifacts", []) if isinstance(item, dict)}
    expected = {(item.relative_path, item.sha256) for item in evidence.artifacts}
    if recorded != expected:
        problems.append("backup manifest artifact list differs from evidence.json")

    # Verify the whole backup against evidence.json before writing anything.
    payloads: List[Tuple[ArtifactRef, bytes]] = []
    for artifact in evidence.artifacts:
        path = _inside(backup_root, artifact.relative_path)
        if not path.is_file():
            problems.append(f"missing {artifact.relative_path}")
            continue
        payload = path.read_bytes()
        if len(payload) != artifact.size_bytes or _digest(payload) != artifact.sha256:
            problems.append(f"sha256 mismatch {artifact.relative_path}")
            continue
        payloads.append((artifact, payload))
    if problems:
        raise BackupVerificationError("; ".join(problems))

    paths = []
    for artifact, payload in payloads:
        _write_checked(store, artifact.relative_path, payload, kind=artifact.kind,
                       media_type=artifact.media_type, expected_sha256=artifact.sha256)
        paths.append(artifact.relative_path)
    # evidence.json last so an interrupted restore never looks complete.
    for name in sorted(manifests, key=lambda item: item == EVIDENCE):
        _write_checked(store, name, manifests[name], kind="manifest",
                       media_type="application/json", expected_sha256=manifest_hashes[name])
        paths.append(name)
    return RestoreReport(evidence.identity.run_id, evidence.identity.experiment_fingerprint,
                         evidence_sha, len(paths), tuple(paths))
