"""SPEC-008 FR-008.2/FR-008.3: retention policy and hash-verified backup/restore.

The run is built from real domain contracts (ExperimentSpec, EvidenceManifest,
ArtifactRef) on tmp_path without training. This proves the backup/restore
mechanics only; it is not training or scientific acceptance.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from uc3m.adapters.local_artifacts import LocalArtifactStore
from uc3m.application.artifacts import (
    BackupVerificationError,
    RetentionPolicy,
    backup_run,
    restore_run,
)
from uc3m.application.configuration import load_scenario_catalog
from uc3m.application.training.layout import normalize_scenario_dir
from uc3m.application.training.persistence import write_json_atomic
from uc3m.domain.evidence import ArtifactRef, EvidenceManifest, verify_artifact
from uc3m.domain.experiments import ExperimentSpec, RunIdentity, RunStatus

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = PROJECT_ROOT / "governance/artifact_retention_policy.yaml"
RUN_MANIFESTS = ("evidence.json", "experiment.json", "completion.json")


def _policy() -> RetentionPolicy:
    return RetentionPolicy.from_mapping(
        yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")))


def _make_run(output_root: Path, *, status: RunStatus = RunStatus.VERIFIED) -> Path:
    catalog = load_scenario_catalog(PROJECT_ROOT / "configs/scenarios.yaml")
    spec = ExperimentSpec("MATD3", catalog["E1"], 42, "a" * 64, "b" * 40, {}, 2)
    identity = RunIdentity.from_spec(spec)
    run_root = output_root / identity.run_id
    scenario = run_root / normalize_scenario_dir("E1", 42)
    files = {
        "source_snapshot.zip": (b"PK\x03\x04source", "source_snapshot", "application/zip"),
        f"{scenario.name}/checkpoints/actor_0.pt": (b"\x00weights\xff" * 64, "checkpoint",
                                                    "application/octet-stream"),
        f"{scenario.name}/checkpoints/training_state.pt": (b"\x01replay-rng-optim" * 32,
                                                           "training_state",
                                                           "application/octet-stream"),
        f"{scenario.name}/results.json": (b'{"cost": 1.5}', "kpi", "application/octet-stream"),
        f"{scenario.name}/training_summary.json": (b'{"episodes": 2}', "training_summary",
                                                   "application/octet-stream"),
        f"{scenario.name}/data/kpis.csv": (b"kpi,value\ncost,1.5\n", "artifact",
                                           "application/octet-stream"),
        f"{scenario.name}/figures/reward.png": (b"\x89PNG\r\n\x1a\nfake", "artifact",
                                                "application/octet-stream"),
    }
    artifacts = []
    for relative, (payload, kind, media) in files.items():
        path = run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        artifacts.append(ArtifactRef.from_file(run_root, path, kind=kind, media_type=media,
                                               producer="MATD3"))
    # Temporaries exist on disk but are never part of the evidence contract.
    (scenario / "checkpoints/.actor_0.pt.123.tmp").write_bytes(b"partial")
    (run_root / ".runner.lock").write_bytes(b"")
    episodes = 2 if status is RunStatus.VERIFIED else 1
    manifest = EvidenceManifest(identity, status, episodes, 2, tuple(artifacts))
    write_json_atomic(run_root / "experiment.json", spec.as_dict())
    write_json_atomic(run_root / "completion.json", {"status": status.value, "reasons": []})
    write_json_atomic(run_root / "evidence.json", manifest.as_dict())
    return run_root


def _snapshot(root: Path) -> dict:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*")) if path.is_file()}


def _evidence(run_root: Path) -> dict:
    return json.loads((run_root / "evidence.json").read_text(encoding="utf-8"))


# --- FR-008.2: retention policy -------------------------------------------------

def test_policy_covers_every_artifact_kind_the_code_emits() -> None:
    sources = "\n".join(path.read_text(encoding="utf-8")
                        for folder in ("uc3m/adapters", "uc3m/ports")
                        for path in (PROJECT_ROOT / folder).rglob("*.py"))
    emitted = set(re.findall(r"\bkind\s*(?::\s*str\s*)?=\s*['\"]([a-z_]+)['\"]", sources))
    # Guard the scan itself: these kinds are produced by native.py and the store port.
    assert {"checkpoint", "kpi", "training_summary", "source_snapshot", "artifact",
            "manifest"} <= emitted
    covered = {kind for cls in _policy().classes for kind in cls.kinds}
    assert emitted - covered == set()


def test_policy_git_rules_match_current_gitignore() -> None:
    ignored = {line.strip() for line in
               (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
    policy = _policy()
    for cls in policy.classes:
        assert set(cls.gitignore_rules) <= ignored, cls.name
        if cls.git_versioned:
            assert not cls.gitignore_rules, cls.name
    by_name = {cls.name: cls for cls in policy.classes}
    assert by_name["checkpoints"].git_versioned is False
    assert {"*.pt", "*.pkl"} <= set(by_name["checkpoints"].gitignore_rules)
    assert by_name["training_state"].git_versioned is False
    assert by_name["temporaries"].backup is False


def test_policy_classifies_real_layout_paths() -> None:
    policy = _policy()
    def ref(path, kind):
        return ArtifactRef(path, "0" * 64, 1, kind, "application/octet-stream", "MATD3")
    assert policy.classify(ref("E1_s42/figures/a.png", "artifact")).name == "figures"
    assert policy.classify(ref("E1/data/kpis.csv", "artifact")).name == "tables"
    assert policy.classify(ref("E1/backend_extra.log", "artifact")).name == "other_artifacts"
    assert policy.classify(ref("E1/checkpoints/x.pt", "checkpoint")).name == "checkpoints"
    with pytest.raises(BackupVerificationError, match="no retention class"):
        policy.classify(ref("E1/x.bin", "unknown_kind"))


def test_policy_rejects_discard_without_backup() -> None:
    raw = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    raw["classes"]["training_state"]["backup"] = False
    with pytest.raises(ValueError, match="discard_after_promotion requires backup"):
        RetentionPolicy.from_mapping(raw)


# --- FR-008.3: verified backup and restore --------------------------------------

def test_backup_delete_restore_reproduces_every_hash(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs")
    original = _snapshot(run_root)
    evidence = _evidence(run_root)
    backup_root = tmp_path / "backup" / run_root.name

    record = backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())
    assert record["run_id"] == run_root.name
    assert len(record["artifacts"]) == len(evidence["artifacts"]) == 7
    assert not any(path.suffix == ".tmp" for path in backup_root.rglob("*"))
    assert not (backup_root / ".runner.lock").exists()

    shutil.rmtree(run_root)
    assert not run_root.exists()

    report = restore_run(backup_root, LocalArtifactStore(run_root, producer="restore"))
    assert report.run_id == run_root.name
    assert report.restored == len(evidence["artifacts"]) + len(RUN_MANIFESTS)

    restored = _snapshot(run_root)
    for name in RUN_MANIFESTS:
        assert restored[name] == original[name]
    for item in evidence["artifacts"]:
        path = run_root / item["relative_path"]
        assert verify_artifact(path, item["sha256"]), item["relative_path"]
        assert restored[item["relative_path"]] == original[item["relative_path"]]
    from uc3m.application.training.runner import read_manifest
    manifest = read_manifest(run_root / "evidence.json")
    assert manifest.status is RunStatus.VERIFIED
    assert manifest.verify_files(run_root)


def test_restore_fails_closed_on_altered_byte_and_writes_nothing(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs")
    backup_root = tmp_path / "backup" / run_root.name
    backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())
    checkpoint = next(backup_root.rglob("actor_0.pt"))
    payload = bytearray(checkpoint.read_bytes())
    payload[3] ^= 0x01
    checkpoint.write_bytes(bytes(payload))
    target = tmp_path / "restored" / run_root.name

    with pytest.raises(BackupVerificationError, match="sha256 mismatch.*actor_0.pt"):
        restore_run(backup_root, LocalArtifactStore(target, producer="restore"))
    assert _snapshot(target) == {}


def test_restore_fails_closed_on_missing_file(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs")
    backup_root = tmp_path / "backup" / run_root.name
    backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())
    next(backup_root.rglob("reward.png")).unlink()
    target = tmp_path / "restored" / run_root.name

    with pytest.raises(BackupVerificationError, match="missing.*reward.png"):
        restore_run(backup_root, LocalArtifactStore(target, producer="restore"))
    assert not (target / "evidence.json").exists()


def test_restore_fails_closed_on_tampered_evidence_manifest(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs")
    backup_root = tmp_path / "backup" / run_root.name
    backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())
    evidence_path = backup_root / "evidence.json"
    evidence_path.write_text(evidence_path.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(BackupVerificationError, match="evidence.json"):
        restore_run(backup_root, LocalArtifactStore(tmp_path / "r", producer="restore"))


def test_restore_rejects_unpinned_evidence_hash(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs")
    backup_root = tmp_path / "backup" / run_root.name
    backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())

    with pytest.raises(BackupVerificationError, match="pinned evidence"):
        restore_run(backup_root, LocalArtifactStore(tmp_path / "r", producer="restore"),
                    expected_evidence_sha256="f" * 64)


def test_unverified_run_is_not_backed_up(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs", status=RunStatus.PARTIAL)
    backup_root = tmp_path / "backup" / run_root.name

    with pytest.raises(BackupVerificationError, match="not verified"):
        backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())
    assert _snapshot(backup_root) == {}


def test_corrupted_source_run_is_not_backed_up(tmp_path) -> None:
    run_root = _make_run(tmp_path / "runs")
    (run_root / "source_snapshot.zip").write_bytes(b"changed after evidence")
    backup_root = tmp_path / "backup" / run_root.name

    with pytest.raises(BackupVerificationError, match="source run fails hash verification"):
        backup_run(run_root, LocalArtifactStore(backup_root, producer="backup"), _policy())
    assert _snapshot(backup_root) == {}
