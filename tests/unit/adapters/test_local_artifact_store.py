from __future__ import annotations

import json
from pathlib import Path

import pytest

from uc3m.adapters.local_artifacts import LocalArtifactStore


def test_local_store_writes_and_verifies_bytes_and_json(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path, producer="unit-test")

    binary = store.write_bytes(
        "checkpoints/model.bin",
        b"model-weights",
        kind="checkpoint",
        media_type="application/octet-stream",
    )
    manifest = store.write_json(
        "reports/kpis.json", {"cost": 12.5}, kind="kpi"
    )

    assert store.verify(binary)
    assert store.verify(manifest)
    assert json.loads((tmp_path / manifest.relative_path).read_text(encoding="utf-8")) == {
        "cost": 12.5
    }


def test_failed_replace_preserves_last_valid_file_and_removes_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = LocalArtifactStore(tmp_path, producer="unit-test")
    store.write_json("state.json", {"version": 1}, kind="training_summary")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated interruption")

    monkeypatch.setattr(store, "_replace", fail_replace)
    with pytest.raises(OSError, match="simulated interruption"):
        store.write_json("state.json", {"version": 2}, kind="training_summary")

    assert json.loads((tmp_path / "state.json").read_text(encoding="utf-8")) == {
        "version": 1
    }
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


@pytest.mark.parametrize("relative_path", ["../escape.json", "/absolute.json"])
def test_local_store_rejects_paths_outside_root(
    tmp_path: Path, relative_path: str
) -> None:
    store = LocalArtifactStore(tmp_path, producer="unit-test")

    with pytest.raises(ValueError, match="relative"):
        store.write_json(relative_path, {"bad": True})
