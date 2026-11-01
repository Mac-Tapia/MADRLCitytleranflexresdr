"""Training refuses a dataset that changed after it passed the dataset gate (SPEC-011)."""
from __future__ import annotations

import json
from pathlib import Path

from uc3m.application.training.preflight import dataset_digest

DEFAULT_READY_MANIFEST = Path("data/dataset_audit/training_dataset_ready_manifest.json")
REVALIDATE = "python tools/dataset/check_training_dataset_ready.py"


class DatasetNotValidated(RuntimeError):
    """The dataset has no passing validation for its current content."""


def require_validated_dataset(schema_path: Path, ready_manifest: Path) -> str:
    """Return the dataset digest if the gate validated exactly this content."""
    ready_manifest = Path(ready_manifest)
    if not ready_manifest.is_file():
        raise DatasetNotValidated(f"no validation manifest at {ready_manifest}; run {REVALIDATE}")
    payload = json.loads(ready_manifest.read_text(encoding="utf-8"))
    if payload.get("status") != "ready":
        raise DatasetNotValidated(
            f"dataset gate status is {payload.get('status')!r}, not ready; fix issues and run {REVALIDATE}"
        )
    validated = payload.get("dataset_digest")
    if not validated:
        raise DatasetNotValidated(f"manifest predates dataset_digest; run {REVALIDATE}")
    current = dataset_digest(schema_path)
    if current != validated:
        raise DatasetNotValidated(f"dataset changed since validation; revalidate with {REVALIDATE}")
    return current
