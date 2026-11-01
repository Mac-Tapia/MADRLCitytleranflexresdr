from __future__ import annotations

from pathlib import Path

import pytest

from uc3m.application.configuration import load_scenario_catalog
from uc3m.domain.evidence import ArtifactRef, EvidenceManifest, verify_artifact
from uc3m.domain.experiments import ExperimentSpec, RunIdentity, RunStatus


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CATALOG = load_scenario_catalog(PROJECT_ROOT / "configs" / "scenarios.yaml")


def _identity() -> RunIdentity:
    return RunIdentity.from_spec(
        ExperimentSpec(
            algorithm="MATD3",
            scenario=CATALOG["E1"],
            seed=0,
            dataset_sha256="a" * 64,
            code_commit="b" * 40,
            submodule_commits={"CityLearn": "c" * 40},
            target_episodes=50,
        )
    )


def _artifact(root: Path, relative: str, kind: str) -> ArtifactRef:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"{kind}-payload".encode("utf-8"))
    return ArtifactRef.from_file(
        root,
        path,
        kind=kind,
        media_type="application/octet-stream",
        producer="unit-test",
    )


def test_artifact_reference_detects_byte_changes(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path, "checkpoints/model.bin", "checkpoint")

    assert artifact.relative_path == "checkpoints/model.bin"
    assert artifact.size_bytes > 0
    assert verify_artifact(tmp_path / artifact.relative_path, artifact.sha256)

    (tmp_path / artifact.relative_path).write_bytes(b"changed")
    assert not verify_artifact(tmp_path / artifact.relative_path, artifact.sha256)


def test_artifact_reference_rejects_paths_outside_run_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.bin"
    outside.write_bytes(b"outside")

    with pytest.raises(ValueError, match="inside run root"):
        ArtifactRef.from_file(
            tmp_path,
            outside,
            kind="checkpoint",
            media_type="application/octet-stream",
            producer="unit-test",
        )


def test_verified_manifest_requires_complete_hashed_evidence(tmp_path: Path) -> None:
    checkpoint = _artifact(tmp_path, "checkpoint.bin", "checkpoint")

    with pytest.raises(ValueError, match="required artifact kinds"):
        EvidenceManifest(
            identity=_identity(),
            status=RunStatus.VERIFIED,
            completed_episodes=50,
            target_episodes=50,
            artifacts=(checkpoint,),
        )

    artifacts = (
        checkpoint,
        _artifact(tmp_path, "kpis.json", "kpi"),
        _artifact(tmp_path, "training.json", "training_summary"),
    )
    manifest = EvidenceManifest(
        identity=_identity(),
        status=RunStatus.VERIFIED,
        completed_episodes=50,
        target_episodes=50,
        artifacts=artifacts,
    )

    assert manifest.verify_files(tmp_path)
    (tmp_path / "kpis.json").unlink()
    assert not manifest.verify_files(tmp_path)


def test_partial_manifest_never_claims_verified(tmp_path: Path) -> None:
    manifest = EvidenceManifest(
        identity=_identity(),
        status=RunStatus.PARTIAL,
        completed_episodes=12,
        target_episodes=50,
        artifacts=(_artifact(tmp_path, "checkpoint.bin", "checkpoint"),),
    )

    assert manifest.status is RunStatus.PARTIAL
    assert manifest.as_dict()["status"] == "partial"
