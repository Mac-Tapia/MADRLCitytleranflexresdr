from __future__ import annotations

import json
from pathlib import Path

import pytest

from uc3m.application.training.dataset_gate import DatasetNotValidated, require_validated_dataset
from uc3m.application.training.preflight import dataset_digest


def _dataset(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    root.mkdir()
    (root / "Building_1.csv").write_text("hour,load\n0,1.0\n", encoding="utf-8")
    schema = root / "schema.json"
    schema.write_text(json.dumps({"buildings": {"Building_1": {"energy_simulation": "Building_1.csv"}}}),
                      encoding="utf-8")
    return schema


def _manifest(tmp_path: Path, schema: Path, *, status: str = "ready", digest: str = None) -> Path:
    manifest = tmp_path / "training_dataset_ready_manifest.json"
    manifest.write_text(
        json.dumps({"status": status, "dataset_digest": digest or dataset_digest(schema)}),
        encoding="utf-8",
    )
    return manifest


def test_validated_unchanged_dataset_is_accepted(tmp_path: Path) -> None:
    schema = _dataset(tmp_path)
    manifest = _manifest(tmp_path, schema)

    assert require_validated_dataset(schema, manifest) == dataset_digest(schema)


def test_one_byte_change_after_validation_blocks_training(tmp_path: Path) -> None:
    schema = _dataset(tmp_path)
    manifest = _manifest(tmp_path, schema)
    (schema.parent / "Building_1.csv").write_text("hour,load\n0,1.1\n", encoding="utf-8")

    with pytest.raises(DatasetNotValidated, match="revalidate"):
        require_validated_dataset(schema, manifest)


def test_dataset_not_marked_ready_blocks_training(tmp_path: Path) -> None:
    schema = _dataset(tmp_path)
    manifest = _manifest(tmp_path, schema, status="blocked")

    with pytest.raises(DatasetNotValidated, match="not ready"):
        require_validated_dataset(schema, manifest)


def test_missing_manifest_or_digest_blocks_training(tmp_path: Path) -> None:
    schema = _dataset(tmp_path)

    with pytest.raises(DatasetNotValidated, match="no validation manifest"):
        require_validated_dataset(schema, tmp_path / "absent.json")

    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps({"status": "ready", "schema_sha256": "a" * 64}), encoding="utf-8")
    with pytest.raises(DatasetNotValidated, match="dataset_digest"):
        require_validated_dataset(schema, legacy)
